#!/usr/bin/env python3
"""
Main entry point for the Tello XR prototype.
"""
import socket
import time
import cv2
import sys  # sys モジュールをインポート

# TelloのIPアドレスとポート
TELLO_IP = '192.168.10.1'
TELLO_PORT = 8889
TELLO_ADDRESS = (TELLO_IP, TELLO_PORT)

def create_socket():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock
    except socket.error as e:
        print(f"Socket creation failed: {e}")
        raise

def tello_start(sock):
    # TelloのWi-Fiに接続するためのコマンドを送信
    send(sock, 'command')
    # ストリーミングを開始するためのコマンドを送信
    send(sock, 'streamon')
    # ストリーミングが安定するまで少し待機
    time.sleep(2)

def cv_init(sock):
    cap = None
    retry_count = 0
    max_retries = 5
    
    while cap is None and retry_count < max_retries:
        try:
            # GStreamerバックエンドを使用してH.264デコードを改善
            # CAP_FFMPEG を使用してFFmpegバックエンドを強制的に使用
            cap = cv2.VideoCapture("udp://0.0.0.0:11111", cv2.CAP_FFMPEG)
            
            # バッファサイズと読み取りタイムアウトを設定
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            
            if not cap.isOpened():
                print(f"カメラオープン失敗 (試行 {retry_count+1}/{max_retries})")
                time.sleep(2)  # より長い待機時間
                retry_count += 1
            else:
                # ダミーフレームを数回読み取ってバッファを初期化
                for i in range(5):
                    cap.read()
                print("カメラ接続成功!")
        except Exception as e:
            print(f"カメラオープン失敗: {e} (試行 {retry_count+1}/{max_retries})")
            time.sleep(2)
            retry_count += 1
    
    if cap is None or not cap.isOpened():
        raise Exception("ビデオストリームに接続できませんでした")
        
    return cap


def send(sock, cmd, wait=2):
    print(f"Send: {cmd}")
    sock.sendto(cmd.encode('utf-8'), TELLO_ADDRESS)
    time.sleep(wait)  # waitはコマンドの処理時間に応じて調整


def close(sock, cap):
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    send(sock, 'streamoff')
    sock.close()

def main():
    print("Tello XR prototype initialized!")
    sock = None
    cap = None
    
    try:
        # UDPソケットを作成
        sock = create_socket()
        tello_start(sock)
        
        cap = cv_init(sock)
        
        # ビデオストリーム処理開始
        print("ビデオストリーム処理を開始します...")
        frame_count = 0
        start_time = time.time()
        fps_update_interval = 30  # 30フレームごとにFPS表示を更新
        
        # 無限ループでビデオを継続的に表示
        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"フレーム受信失敗 - リトライします")
                time.sleep(0.1)
                continue
                
            frame_count += 1
            
            # 定期的にFPS情報を表示
            if frame_count % fps_update_interval == 0:
                current_time = time.time()
                elapsed = current_time - start_time
                fps = fps_update_interval / elapsed
                print(f"現在のFPS: {fps:.2f}")
                start_time = current_time

            # 処理したフレームを表示
            cv2.imshow('Tello Video Stream', frame)

            # 'q'キーで終了
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("ユーザーによる終了")
                break

        # # 離陸
        # send(sock, 'takeoff', wait=5)
        # # 1メートル（=100cm）前進
        # send(sock, 'forward 100', wait=4)
        # # 着陸
        # send(sock, 'land', wait=5)

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)  # エラーコード1でアプリケーションを終了
    finally:
        if sock is not None and cap is not None:
            close(sock, cap)

if __name__ == "__main__":
    main()