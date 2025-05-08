#!/usr/bin/env python3
"""
Tello XR Controller Module
Telloドローンとの通信および制御を担当するモジュール
"""
import socket
import time

# Telloドローンの通信設定用定数
DEFAULT_TELLO_IP = "192.168.10.1"
DEFAULT_TELLO_PORT = 8889


class TelloControl:
    """Telloドローンとの通信と制御を行うクラス"""

    def __init__(self, tello_ip=DEFAULT_TELLO_IP, tello_port=DEFAULT_TELLO_PORT):
        """
        TelloControlクラスの初期化

        Parameters:
            tello_ip (str): TelloドローンのIPアドレス
            tello_port (int): Telloドローンの通信ポート
        """
        self.tello_address = (tello_ip, tello_port)
        self.sock = None

    def connect(self):
        """
        Telloドローンとの通信ソケットを作成する

        Returns:
            bool: 接続成功したらTrue、失敗したらFalse
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return True
        except OSError as e:
            print(f"ソケット作成失敗: {e}")
            return False

    def send_command(self, command, wait_time=2):
        """
        Telloにコマンドを送信する

        Parameters:
            command (str): 送信するコマンド
            wait_time (float): コマンド送信後の待機時間（秒）

        Returns:
            bool: 送信成功したらTrue、失敗したらFalse
        """
        if self.sock is None:
            print("ソケットが初期化されていません")
            return False

        try:
            print(f"コマンド送信: {command}")
            self.sock.sendto(command.encode("utf-8"), self.tello_address)
            time.sleep(wait_time)  # コマンド処理時間を考慮
            return True
        except Exception as e:
            print(f"コマンド送信エラー: {e}")
            return False

    def activate_sdk_mode(self):
        """
        SDKモードをアクティブ化する

        Returns:
            bool: 成功したらTrue
        """
        return self.send_command("command")

    def start_video_stream(self):
        """
        ビデオストリーミングを開始する

        Returns:
            bool: 成功したらTrue
        """
        # SDKモードをアクティブ化
        if not self.activate_sdk_mode():
            return False

        # ストリーミングを開始
        if not self.send_command("streamon", wait_time=5):
            return False

        print("ビデオストリーミングを開始しました")
        return True

    def stop_video_stream(self):
        """
        ビデオストリーミングを停止する

        Returns:
            bool: 成功したらTrue
        """
        return self.send_command("streamoff")

    def takeoff(self):
        """
        ドローンを離陸させる

        Returns:
            bool: 成功したらTrue
        """
        return self.send_command("takeoff", wait_time=5)

    def land(self):
        """
        ドローンを着陸させる

        Returns:
            bool: 成功したらTrue
        """
        return self.send_command("land", wait_time=5)

    def move(self, direction, distance):
        """
        ドローンを指定方向に移動させる

        Parameters:
            direction (str): 移動方向 ('forward', 'back', 'left', 'right', 'up', 'down')
            distance (int): 移動距離（cm、20-500）

        Returns:
            bool: 成功したらTrue
        """
        valid_directions = ("forward", "back", "left", "right", "up", "down")
        if direction not in valid_directions:
            print(f"無効な移動方向です: {direction}")
            return False

        try:
            distance_val = int(distance)
            if not (20 <= distance_val <= 500):
                print(f"無効な距離です: {distance_val}cm (20-500cmの範囲で指定してください)")
                return False
        except ValueError:
            print(f"無効な距離値です: {distance}")
            return False

        return self.send_command(f"{direction} {distance_val}", wait_time=4)

    def rotate(self, direction, degrees):
        """
        ドローンを回転させる

        Parameters:
            direction (str): 回転方向 ('cw' = 時計回り, 'ccw' = 反時計回り)
            degrees (int): 回転角度 (1-360)

        Returns:
            bool: 成功したらTrue
        """
        if direction not in ("cw", "ccw"):
            print(f"無効な回転方向です: {direction}")
            return False

        try:
            degrees_val = int(degrees)
            if not (1 <= degrees_val <= 360):
                print(f"無効な回転角度です: {degrees_val} (1-360度の範囲で指定してください)")
                return False
        except ValueError:
            print(f"無効な角度値です: {degrees}")
            return False

        return self.send_command(f"{direction} {degrees_val}", wait_time=3)

    def close(self):
        """ソケット接続を閉じる"""
        if self.sock:
            self.sock.close()
            self.sock = None
            print("Telloとの接続を閉じました")


# 単体テスト用コード
if __name__ == "__main__":
    tello = TelloControl()
    if tello.connect():
        try:
            print("Tello接続テスト")
            # SDKモード有効化
            tello.activate_sdk_mode()
            # バッテリーレベルを確認
            tello.send_command("battery?")

            # 必要に応じてコメントアウトを解除してテスト
            # tello.start_video_stream()
            # tello.takeoff()
            # tello.move('forward', 50)
            # tello.land()

        finally:
            tello.close()
    else:
        print("Tello接続失敗")
