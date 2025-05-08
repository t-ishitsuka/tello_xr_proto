#!/usr/bin/env python3
"""
Main entry point for the Tello XR prototype.
Telloドローンからのビデオストリームを表示し、制御するメインプログラム
"""
import sys
import time

from tello_control import TelloControl
from video_stream import VideoStream
from controller_input import ControllerManager


def main():
    """メイン実行関数"""
    print("Tello XR prototype initialized!")
    tello = None
    video = None
    controller = None

    try:
        # コントローラーの初期化
        controller = ControllerManager(config_file="config/controller_config.json")
        num_controllers = controller.detect_controllers()
        if num_controllers == 0:
            print("警告: コントローラーが検出されませんでした。キーボード操作のみ可能です。")
        else:
            print(f"{num_controllers}個のコントローラーを検出しました。")
            for controller_id, name in controller.get_controller_names():
                print(f"- {name}")

        # Tello制御モジュールの初期化
        tello = TelloControl()
        if not tello.connect():
            print("Telloとの接続に失敗しました")
            return

        # ビデオストリーミングを開始
        if not tello.start_video_stream():
            print("ビデオストリーミングの開始に失敗しました")
            return

        # 映像ストリーミングモジュールの初期化と接続
        video = VideoStream()
        time.sleep(2)  # ストリーミングが安定するまで少し待機

        if not video.connect():
            print("ビデオストリームへの接続に失敗しました")
            return

        print("ビデオストリーム処理を開始します... 'q'キーで終了")
        print("コントローラー操作: ")
        print(" - 左スティック: 前後/左右の移動")
        print(" - 右スティック: 上下/回転")
        print(" - A/Xボタン: 離陸")
        print(" - B/Oボタン: 着陸")
        print(" - X/□ボタン: 緊急停止")

        # ボタン状態の前回値（連続実行防止用）
        prev_button_states = {
            "takeoff": False,
            "land": False,
            "emergency": False,
            "photo": False
        }

        # 飛行状態
        is_flying = False
        rc_control_enabled = False
        last_rc_time = time.time()

        # メインループ: ビデオフレーム処理、コントローラー入力処理、ドローン制御
        while True:
            # コントローラーのイベント処理（接続/切断検出）
            if controller:
                controller.handle_events()

            # ビデオフレームの取得と表示
            ret, frame = video.read_frame()
            if not ret:
                print("フレーム受信失敗 - リトライします")
                time.sleep(0.1)
                continue

            # コントローラー入力の取得と処理
            if controller and controller.is_controller_available():
                input_data = controller.get_normalized_input()
                if input_data:
                    button_states = input_data["buttons"]
                    movements = input_data["movement"]
                    
                    # ボタン入力によるドローン操作
                    # 離陸（A/Xボタン）: 前回押されていなくて今回押された場合に実行
                    if button_states["takeoff"] and not prev_button_states["takeoff"] and not is_flying:
                        print("離陸コマンド実行")
                        if tello.takeoff():
                            is_flying = True
                            rc_control_enabled = True
                    
                    # 着陸（B/Oボタン）: 前回押されていなくて今回押された場合に実行
                    if button_states["land"] and not prev_button_states["land"] and is_flying:
                        print("着陸コマンド実行")
                        if tello.land():
                            is_flying = False
                            rc_control_enabled = False
                    
                    # 緊急停止（X/□ボタン）: 前回押されていなくて今回押された場合に実行
                    if button_states["emergency"] and not prev_button_states["emergency"]:
                        print("緊急停止コマンド実行")
                        tello.send_command("emergency", wait_time=1)
                        is_flying = False
                        rc_control_enabled = False
                    
                    # 写真撮影機能は将来的に実装予定
                    if button_states["photo"] and not prev_button_states["photo"]:
                        print("写真撮影コマンド（未実装）")
                    
                    # スティック入力による移動制御（飛行中のみ）
                    if rc_control_enabled and is_flying:
                        # 200ms間隔でRCコマンドを送信（あまり頻繁に送信するとパケットロスの原因になる）
                        current_time = time.time()
                        if current_time - last_rc_time > 0.2:  # 5Hz
                            # コントローラー値を-100〜100の範囲にスケーリング
                            left_right = int(movements["x"] * 100)  # 左右移動
                            forward_backward = int(movements["y"] * 100)  # 前後移動
                            up_down = int(movements["z"] * 100)  # 上下移動
                            yaw = int(movements["rotation"] * 100)  # 回転
                            
                            # 速度値が大きい場合のみ表示（デバッグ用）
                            if abs(left_right) > 15 or abs(forward_backward) > 15 or abs(up_down) > 15 or abs(yaw) > 15:
                                print(f"RC: 左右={left_right}, 前後={forward_backward}, 上下={up_down}, 回転={yaw}")
                            
                            # RCコマンド送信
                            tello.send_rc_control(left_right, forward_backward, up_down, yaw)
                            last_rc_time = current_time
                    
                    # 前回のボタン状態を更新
                    prev_button_states = button_states.copy()

            # 定期的にFPSを計算して表示（30フレームごと）
            fps = video.calculate_fps(interval=30)
            if fps > 0:
                print(f"現在のFPS: {fps:.2f}")

            # フレームを表示
            key = video.display_frame(frame)

            # 'q'キーで終了
            if key & 0xFF == ord("q"):
                print("ユーザーによる終了")
                break

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)  # エラーコード1でアプリケーションを終了
    finally:
        # リソースのクリーンアップ
        if video:
            video.release()
        if tello:
            tello.stop_video_stream()
            tello.close()
        if controller:
            controller.cleanup()


if __name__ == "__main__":
    main()
