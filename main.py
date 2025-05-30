#!/usr/bin/env python3
"""
Main entry point for the Tello XR prototype.
Program to display and control video stream from Tello drone
"""
import sys
import time
from threading import Event, Thread

from controller_input import ControllerManager

from tello_control import TelloControl
from video_stream import VideoStream  # Using the enhanced video stream module


def main():
    """Main execution function"""
    print("Tello XR prototype initialized!")
    print("Using improved H.264 video stream decoder with error recovery")
    tello = None
    video = None
    controller = None

    # プログラム終了フラグ
    exit_event = Event()

    # ビデオ再接続関連変数
    video_reconnect_attempts = 0
    max_video_reconnect = 5
    last_video_reconnect = 0
    reconnect_cooldown = 10  # 再接続のクールダウン時間(秒)

    # ドローン状態と入力値を格納する辞書(スレッド間共有用) - 関数の先頭で定義
    drone_state = {
        "is_flying": False,
        "battery": 0,
        "rc_control_enabled": False,
        "connection_status": "Not Connected",
        "video_stream_status": "Not Connected",
        "last_controller_input": {
            "movement": {"x": 0.0, "y": 0.0, "z": 0.0, "rotation": 0.0},
            "buttons": {"takeoff": False, "land": False, "emergency": False, "photo": False},
        },
        "error_count": 0,  # エラーカウンター
        "last_error": "",  # 最後のエラーメッセージ
        "recovery_mode": False,  # 復旧モード
        # テレメトリーデータ用の初期値
        "height": 0,  # 高度 (cm)
        "vgx": 0,  # X軸速度 (cm/s)
        "vgy": 0,  # Y軸速度 (cm/s)
        "vgz": 0,  # Z軸速度 (cm/s)
        "pitch": 0,  # ピッチ角 (度)
        "roll": 0,  # ロール角 (度)
        "yaw": 0,  # ヨー角 (度)
    }

    try:
        # コントローラーの初期化
        controller = ControllerManager(config_file="config/controller_config.json")
        num_controllers = controller.detect_controllers()
        if num_controllers == 0:
            print("警告: コントローラーが検出されませんでした。キーボード操作のみ可能です。")
        else:
            print(f"{num_controllers}個のコントローラーを検出しました。")
            for _, name in controller.get_controller_names():
                print(f"- {name}")

        # Tello制御モジュールの初期化
        tello = TelloControl()
        if not tello.connect():
            print("Telloとの接続に失敗しました")
            return

        # ビデオストリーミングを開始
        print("Starting video streaming...")
        if not tello.start_video_stream():
            print("Failed to start video streaming")
            return

        # Initialize the improved video streaming module and connect
        video = VideoStream()
        print("Waiting for video stream to stabilize...")
        time.sleep(2)  # Wait briefly for streaming to stabilize

        connection_attempts = 0
        max_connection_attempts = 3
        while connection_attempts < max_connection_attempts:
            if video.connect():
                print("Successfully connected to video stream with improved H.264 decoder")
                break
            connection_attempts += 1
            print(
                f"Retrying video stream connection "
                f"({connection_attempts}/{max_connection_attempts})..."
            )
            time.sleep(1)

        if connection_attempts >= max_connection_attempts:
            print("Failed to connect to video stream")
            return  # バッテリー残量とテレメトリーを取得(初期値)
        battery_level = tello.get_battery()
        telemetry = tello.get_telemetry_data()
        print(f"現在のバッテリー残量: {battery_level}%")
        if telemetry:
            print(f"テレメトリーデータ取得成功: {len(telemetry)}項目")

        print("ビデオストリーム処理を開始します... 'q'キーで終了")
        print("コントローラー操作: ")
        print(" - 左スティック: 前後/左右の移動")
        print(" - 右スティック: 上下/回転")
        print(" - A/Xボタン: 離陸")
        print(" - B/Oボタン: 着陸")
        print(" - X/□ボタン: 緊急停止")
        print(" - LB/L1ボタン: 速度モード上昇")
        print(" - RB/R1ボタン: 速度モード下降")
        print(" - iキー: UI情報表示の切り替え")
        
        # 現在の速度モードを表示
        if controller and controller.is_controller_available():
            current_mode = controller.get_current_speed_mode()
            mode_info = controller.get_speed_mode_info()
            mode_name = mode_info.get("name", current_mode)
            print(f"初期速度モード: {mode_name}")
        print()

        # ボタン状態の前回値(連続実行防止用)
        prev_button_states = {"takeoff": False, "land": False, "emergency": False, "photo": False}

        # 飛行状態
        is_flying = False

        # drone_stateの初期化
        drone_state["battery"] = battery_level if battery_level > 0 else 0
        drone_state["connection_status"] = "Connected"
        drone_state["video_stream_status"] = (
            "Connected" if video and video.connection_status == "Connected" else "Not Connected"
        )

        # RCコマンド送信用のスレッドを開始
        rc_thread = Thread(
            target=rc_control_thread, args=(tello, controller, drone_state, exit_event), daemon=True
        )
        rc_thread.start()

        # バッテリー残量取得のための変数
        last_battery_check = time.time()
        battery_check_interval = 10  # バッテリー残量を10秒ごとに更新

        # ビデオ再接続関連変数
        video_reconnect_attempts = 0
        max_video_reconnect = 5
        last_video_reconnect = 0
        reconnect_cooldown = 10  # 再接続のクールダウン時間(秒)

        # メインループ: ビデオフレーム処理、UI表示、キー入力処理
        while not exit_event.is_set():
            try:
                loop_start_time = time.time()  # ループの実行時間測定用

                # コントローラーのイベント処理(接続/切断検出)
                if controller:
                    controller.handle_events()

                # Get video frame
                ret, frame = video.read_frame()
                if not ret or frame is None:
                    print(f"Frame reception failed - retrying (status: {video.connection_status})")

                    # Connection loss reconnection logic
                    current_time = time.time()
                    if (
                        (video.connection_status in ["Disconnected", "Read Error", "Frame Error"])
                        and (current_time - last_video_reconnect > reconnect_cooldown)
                        and (video_reconnect_attempts < max_video_reconnect)
                    ):

                        print(
                            f"Attempting to reconnect video stream... "
                            f"(attempt {video_reconnect_attempts+1}/{max_video_reconnect})"
                        )
                        # Release current capture
                        video.release()
                        # Reconnect
                        if video.connect():
                            print("Successfully reconnected to video stream")
                            video_reconnect_attempts = 0  # Reset counter on success
                            # Track metrics for decode errors
                            drone_state["video_decode_errors"] = 0
                        else:
                            video_reconnect_attempts += 1
                            print(
                                f"Failed to reconnect video stream "
                                f"(attempt {video_reconnect_attempts}/{max_video_reconnect})"
                            )

                        last_video_reconnect = current_time

                    time.sleep(0.1)
                    continue

                # 定期的にバッテリー残量とテレメトリーデータを更新
                current_time = time.time()
                if current_time - last_battery_check > battery_check_interval:
                    # バッテリー情報の取得と更新
                    battery_level = tello.get_battery()
                    if battery_level > 0:
                        drone_state["battery"] = battery_level
                        # バッテリー残量が低い場合は警告
                        if battery_level <= 15:
                            print(f"警告: バッテリー残量が低下しています ({battery_level}%)")

                    # テレメトリーデータの取得と更新
                    telemetry_data = tello.get_telemetry_data()
                    if telemetry_data:
                        print(f"Received telemetry data: {telemetry_data}")
                        # テレメトリー情報をdrone_stateに統合
                        for key, value in telemetry_data.items():
                            drone_state[key] = value
                    else:
                        print("No telemetry data received")

                    last_battery_check = current_time

                # コントローラー入力の取得
                input_data = None
                if controller and controller.is_controller_available():
                    input_data = controller.get_normalized_input()
                    if input_data and "buttons" in input_data:
                        button_states = input_data["buttons"]

                        # ボタン入力によるドローン操作
                        # 離陸(A/Xボタン): 前回押されていなくて今回押された場合に実行
                        if (
                            button_states["takeoff"]
                            and not prev_button_states["takeoff"]
                            and not is_flying
                        ):
                            print("離陸コマンド実行")
                            if tello.takeoff():
                                is_flying = True
                                # ドローン状態を更新
                                drone_state["is_flying"] = True
                                drone_state["rc_control_enabled"] = True

                        # 着陸(B/Oボタン): 前回押されていなくて今回押された場合に実行
                        if button_states["land"] and not prev_button_states["land"] and is_flying:
                            print("着陸コマンド実行")
                            if tello.land():
                                is_flying = False
                                # ドローン状態を更新
                                drone_state["is_flying"] = False
                                drone_state["rc_control_enabled"] = False

                        # 緊急停止(X/□ボタン): 前回押されていなくて今回押された場合に実行
                        if button_states["emergency"] and not prev_button_states["emergency"]:
                            print("緊急停止コマンド実行")
                            tello.send_command("emergency", wait_time=1)
                            is_flying = False
                            # ドローン状態を更新
                            drone_state["is_flying"] = False
                            drone_state["rc_control_enabled"] = False

                        # 写真撮影機能は将来的に実装予定
                        if button_states["photo"] and not prev_button_states["photo"]:
                            print("写真撮影コマンド(未実装)")

                        # コントローラー入力をスレッドに共有
                        drone_state["last_controller_input"] = input_data
                        
                        # 速度モード情報をdrone_stateに保存
                        if "speed_mode" in input_data:
                            drone_state["current_speed_mode"] = input_data["speed_mode"]
                            if controller:
                                drone_state["speed_mode_info"] = controller.get_speed_mode_info()

                        # 前回のボタン状態を更新
                        prev_button_states = button_states.copy()

                # 定期的にFPSを計算(30フレームごと)
                video.calculate_fps(interval=30)

                # UI表示のためのフレーム処理
                display_frame = frame.copy()

                # テレメトリーデータの更新
                telemetry_data = {
                    "battery": drone_state.get("battery", -1),
                    "is_flying": is_flying,
                    "error_count": drone_state.get("error_count", 0),
                    "connection_status": video.connection_status,
                    "last_error": drone_state.get("last_error", ""),
                    # Extended telemetry data
                    "height": drone_state.get("h"),  # Height (cm)
                    "vgx": drone_state.get("vgx"),  # X-axis speed (cm/s)
                    "vgy": drone_state.get("vgy"),  # Y-axis speed (cm/s)
                    "vgz": drone_state.get("vgz"),  # Z-axis speed (cm/s)
                    "pitch": drone_state.get("pitch"),  # Pitch angle (degrees)
                    "roll": drone_state.get("roll"),  # Roll angle (degrees)
                    "yaw": drone_state.get("yaw"),  # Yaw angle (degrees)
                    # Video statistics from improved decoder
                    "decode_errors": video.decode_errors,
                    "dropped_frames": video.dropped_frames,
                    "total_frames": video.total_frames,
                }

                # テレメトリーデータの表示
                display_frame = video.display_telemetry_data(display_frame, telemetry_data)

                # コントローラーデータの表示
                controller_data = (
                    input_data if input_data else drone_state.get("last_controller_input")
                )
                # バッテリー情報も渡す
                battery = drone_state.get("battery", -1)
                display_frame = video.draw_controller_state(
                    display_frame, controller_data, is_flying, battery, drone_state
                )

                # フレームを表示
                key = video.display_frame(display_frame)

                # キー入力処理
                if key & 0xFF == ord("q"):
                    print("ユーザーによる終了")
                    break
                elif key & 0xFF == ord("i"):
                    # 'i'キーでUI情報表示の切り替え
                    show_info = video.toggle_info_display()
                    print(f"UI情報表示: {'ON' if show_info else 'OFF'}")

                # ループの実行時間を測定(パフォーマンス監視用)
                loop_time = time.time() - loop_start_time
                if loop_time > 0.05:  # 50ms以上かかる場合は警告(ループが遅い)
                    print(f"警告: メインループの実行に時間がかかっています: {loop_time*1000:.1f}ms")

                    # Adaptive sleep for performance management
                    if loop_time > 0.1:  # Very slow iterations
                        # Add to drone state to track performance issues
                        drone_state["performance_warnings"] = (
                            drone_state.get("performance_warnings", 0) + 1
                        )

                        # If experiencing consistent performance issues, adjust processing load
                        if drone_state.get("performance_warnings", 0) > 10:
                            print(
                                "Performance optimization: "
                                "Reducing processing load due to consistent slow frames"
                            )
                            # Reset counter after taking action
                            drone_state["performance_warnings"] = 0

            except Exception as e:
                print(f"メインループでエラーが発生しました: {e}")
                # エラー情報を保存
                drone_state["error_count"] += 1
                drone_state["last_error"] = str(e)

                # 連続したエラーが多すぎる場合は短時間休止
                if drone_state["error_count"] > 10:
                    print("エラーが多発しています。システムを短時間休止します...")
                    drone_state["recovery_mode"] = True
                    time.sleep(1.0)
                    drone_state["error_count"] = 0
                    drone_state["recovery_mode"] = False
                else:
                    time.sleep(0.1)

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)  # エラーコード1でアプリケーションを終了
    finally:
        # 終了フラグをセット
        exit_event.set()

        # リソースのクリーンアップ
        if video:
            video.release()
        if tello:
            # 安全のため、着陸コマンドを送信
            if drone_state.get("is_flying", False):
                print("ドローンが飛行中のためコマンド実行: 着陸")
                tello.land()
            tello.stop_video_stream()
            tello.close()
        if controller:
            controller.cleanup()

        print("すべてのリソースを解放しました。プログラムを終了します。")


def rc_control_thread(tello, controller, drone_state, exit_event):
    """
    RCコマンド送信を担当する別スレッド
    メインループのフレームレート低下を防ぐ

    Parameters:
        tello (TelloControl): Tello制御クラスのインスタンス
        controller (ControllerManager): コントローラー管理クラスのインスタンス
        drone_state (dict): ドローンの状態とコントローラー入力を格納する辞書
        exit_event (Event): プログラム終了を通知するイベント
    """
    print("RC制御スレッド開始")
    last_rc_time = time.time()
    rc_send_interval = 0.05  # RCコマンド送信間隔 (20Hz - より滑らかな制御のため)
    heartbeat_interval = 3  # ハートビート信号の送信間隔(秒)
    last_heartbeat_time = time.time()

    # 連続して同じ値を送り続けるのを防ぐための変数
    last_rc_values = (0, 0, 0, 0)
    idle_count = 0
    max_idle_count = 10  # 10回同じ値が続いたら送信を一時停止

    # 送信失敗時のリトライ関連設定
    retry_count = 0
    max_retries = 3

    try:
        while not exit_event.is_set():
            try:
                # スレッドセーフな方法で状態を取得
                is_flying = drone_state.get("is_flying", False)
                rc_enabled = drone_state.get("rc_control_enabled", False)
                controller_input = drone_state.get("last_controller_input")

                current_time = time.time()

                # 飛行中かつRC制御有効の場合
                if is_flying and rc_enabled:
                    # 1. コントローラー入力の処理(メイン制御)
                    if controller_input and current_time - last_rc_time > rc_send_interval:

                        # movementが存在するか確認
                        movements = controller_input.get("movement")
                        if movements:
                            # コントローラー値を-100〜100の範囲にスケーリング
                            left_right = int(movements.get("x", 0) * 100)  # 左右移動
                            forward_backward = int(movements.get("y", 0) * 100)  # 前後移動
                            up_down = int(movements.get("z", 0) * 100)  # 上下移動
                            yaw = int(movements.get("rotation", 0) * 100)  # 回転

                            # 小さすぎる値は0とみなす(誤差の扱い改善)
                            if abs(left_right) < 5:
                                left_right = 0
                            if abs(forward_backward) < 5:
                                forward_backward = 0
                            if abs(up_down) < 5:
                                up_down = 0
                            if abs(yaw) < 5:
                                yaw = 0

                            # 現在のRC値
                            current_rc_values = (left_right, forward_backward, up_down, yaw)

                            # 値に変化があるか、または一定時間経過した場合のみ送信
                            if current_rc_values != last_rc_values or idle_count >= max_idle_count:
                                # RCコマンド送信(失敗時はリトライ)
                                success = tello.send_rc_control(
                                    left_right, forward_backward, up_down, yaw
                                )
                                if not success and retry_count < max_retries:
                                    # 送信失敗時は短い間隔を空けてリトライ
                                    retry_count += 1
                                    time.sleep(0.02)
                                    tello.send_rc_control(
                                        left_right, forward_backward, up_down, yaw
                                    )
                                else:
                                    retry_count = 0  # 成功またはリトライ上限に達したらリセット

                                last_rc_time = current_time
                                last_rc_values = current_rc_values
                                idle_count = 0  # カウンターをリセット
                            else:
                                idle_count += 1

                    # 2. ハートビート信号の送信(接続を維持するための定期的なアイドルコマンド)
                    elif current_time - last_heartbeat_time > heartbeat_interval:
                        # 長時間操作がない場合は停止コマンドを送信して接続を維持
                        tello.send_rc_control(0, 0, 0, 0)
                        last_heartbeat_time = current_time

            except Exception as e:
                print(f"RC制御処理でエラーが発生しました: {e}")
                # エラー情報を状態に記録
                drone_state["last_error"] = f"RC制御: {e!s}"
                drone_state["error_count"] += 1

            # スレッドの負荷を軽減するためのスリープ (短い間隔でポーリング)
            time.sleep(0.01)
    except Exception as e:
        print(f"RC制御スレッドでエラーが発生しました: {e}")
    finally:
        # 終了時には必ず停止コマンドを送信 (複数回試行して確実に停止させる)
        try:
            if tello:
                for _ in range(3):  # 確実に停止コマンドを送るために複数回試行
                    tello.send_rc_control(0, 0, 0, 0)
                    time.sleep(0.1)
        except Exception as e:
            print(f"終了時の停止コマンド送信中にエラー: {e}")
        print("RC制御スレッド終了")


if __name__ == "__main__":
    main()
