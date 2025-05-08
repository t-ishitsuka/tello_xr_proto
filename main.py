#!/usr/bin/env python3
"""
Main entry point for the Tello XR prototype.
Telloドローンからのビデオストリームを表示し、制御するメインプログラム
"""
import sys
import time

from tello_control import TelloControl
from video_stream import VideoStream


def main():
    """メイン実行関数"""
    print("Tello XR prototype initialized!")
    tello = None
    video = None
    
    try:
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
        
        # メインループ: ビデオフレーム処理と表示
        while True:
            ret, frame = video.read_frame()
            if not ret:
                print("フレーム受信失敗 - リトライします")
                time.sleep(0.1)
                continue
                
            # 定期的にFPSを計算して表示
            fps = video.calculate_fps(interval=30)
            if fps > 0:
                print(f"現在のFPS: {fps:.2f}")
            
            # フレームを表示
            key = video.display_frame(frame)
            
            # 'q'キーで終了
            if key & 0xFF == ord('q'):
                print("ユーザーによる終了")
                break

        # # ドローン操作のテスト (コメントアウト状態)
        # tello.takeoff()
        # tello.move('forward', 100)
        # tello.land()

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

if __name__ == "__main__":
    main()