#!/usr/bin/env python3
"""
Tello XR Video Stream Module
Telloドローンからのビデオストリームを処理するためのモジュール
"""
import time

import cv2

# Tello ビデオストリームの UDP アドレス定数
TELLO_VIDEO_STREAM_ADDRESS = "udp://0.0.0.0:11111"

class VideoStream:
    """Telloからの映像ストリームを処理するクラス"""
    
    def __init__(self):
        """VideoStreamクラスの初期化"""
        self.cap = None
        self.frame_count = 0
        self.start_time = time.time()
        self.fps = 0
    
    def connect(self, retry_limit=5):
        """
        ビデオストリームに接続する
        
        Parameters:
            retry_limit (int): 接続失敗時のリトライ回数上限
            
        Returns:
            bool: 接続成功したらTrue、失敗したらFalse
        """
        retry_count = 0
        
        while self.cap is None and retry_count < retry_limit:
            try:
                # FFmpegバックエンドを使用してH.264デコードの問題を解消
                self.cap = cv2.VideoCapture(TELLO_VIDEO_STREAM_ADDRESS, cv2.CAP_FFMPEG)
                
                # バッファサイズを設定
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
                
                if not self.cap.isOpened():
                    print(f"カメラオープン失敗 (試行 {retry_count+1}/{retry_limit})")
                    time.sleep(2)
                    retry_count += 1
                    self.cap = None
                else:
                    # ダミーフレーム読み取りによるバッファ初期化
                    for _ in range(5):
                        self.cap.read()
                    print("カメラ接続成功!")
                    return True
            except Exception as e:
                print(f"カメラオープン失敗: {e} (試行 {retry_count+1}/{retry_limit})")
                time.sleep(2)
                retry_count += 1
        
        if self.cap is None:
            print("ビデオストリームへの接続に失敗しました")
            return False
            
        return True

    def read_frame(self):
        """
        フレームを1つ読み取る
        
        Returns:
            tuple: (読み取り成功フラグ, フレーム画像)
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None
            
        ret, frame = self.cap.read()
        
        if ret:
            self.frame_count += 1
        
        return ret, frame
    
    def calculate_fps(self, interval=30):
        """
        FPSを計算する (intervalフレームごとに更新)
        
        Parameters:
            interval (int): FPS計算の間隔となるフレーム数
            
        Returns:
            float: 現在のFPS値
        """
        if self.frame_count % interval == 0:
            current_time = time.time()
            elapsed = current_time - self.start_time
            self.fps = interval / elapsed if elapsed > 0 else 0
            self.start_time = current_time
            
        return self.fps
    
    def display_frame(self, frame, window_name="Tello Video Stream"):
        """
        フレームをウィンドウに表示する
        
        Parameters:
            frame: 表示するフレーム画像
            window_name (str): 表示ウィンドウの名前
            
        Returns:
            int: キー入力の値 (27はESC、113は'q')
        """
        cv2.imshow(window_name, frame)
        return cv2.waitKey(1)
    
    def release(self):
        """リソースを解放する"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
        print("ビデオストリームをクローズしました")

# 単体テスト用コード
if __name__ == "__main__":
    stream = VideoStream()
    if stream.connect():
        try:
            print("ビデオストリーム表示中... 'q'キーで終了")
            while True:
                ret, frame = stream.read_frame()
                if not ret:
                    print("フレーム読み取り失敗")
                    time.sleep(0.1)
                    continue
                
                fps = stream.calculate_fps()
                if fps > 0:
                    print(f"現在のFPS: {fps:.2f}")
                
                key = stream.display_frame(frame)
                if key & 0xFF in (27, ord('q')):  # ESCまたはqで終了
                    print("ユーザーによる終了")
                    break
                
        finally:
            stream.release()
    else:
        print("ストリーミング開始失敗")