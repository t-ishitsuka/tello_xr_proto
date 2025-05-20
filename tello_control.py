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

    def send_command(self, command, wait_time=2.0, expect_response=False):
        """
        Telloにコマンドを送信する

        Parameters:
            command (str): 送信するコマンド
            wait_time (float): コマンド送信後の待機時間(秒)
            expect_response (bool): レスポンスを待機するか

        Returns:
            bool | str: expect_response=Falseの場合はTrue/False、Trueの場合はレスポンス文字列
        """
        if self.sock is None:
            print("ソケットが初期化されていません")
            return False

        try:
            # 送信前にソケットのタイムアウトを設定
            self.sock.settimeout(5.0)
            
            # コマンドを送信
            print(f"コマンド送信: {command}")
            self.sock.sendto(command.encode("utf-8"), self.tello_address)
            
            # レスポンスを期待する場合
            response = None
            response_socket = None
            if expect_response:
                try:
                    # レスポンス用のソケットを作成
                    response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    response_socket.bind(('', 8890))  # Telloからの応答を受け取るポート
                    response_socket.settimeout(3.0)
                    
                    # レスポンス受信
                    response_data, _ = response_socket.recvfrom(1518)
                    response = response_data.decode(encoding="utf-8").strip()
                    print(f"レスポンス: {response}")
                    
                except TimeoutError:
                    print(f"{command} コマンドへのレスポンスがタイムアウトしました")
                    response = None
                finally:
                    if response_socket:
                        response_socket.close()
            
            # 処理時間を確保
            time.sleep(wait_time)
            
            if expect_response:
                return response
            return True
            
        except Exception as e:
            print(f"コマンド送信エラー: {e}")
            return False

    def activate_sdk_mode(self):
        """
        SDKモードをアクティブ化する
        
        Returns:
            bool: 成功したらTrue、失敗したらFalse
        """
        return self.send_command("command", wait_time=1.0)

    def takeoff(self):
        """
        ドローンを離陸させる
        
        Returns:
            bool: 成功したらTrue、失敗したらFalse
        """
        return self.send_command("takeoff", wait_time=5.0)

    def land(self):
        """
        ドローンを着陸させる
        
        Returns:
            bool: 成功したらTrue、失敗したらFalse
        """
        return self.send_command("land", wait_time=5.0)

    def move(self, direction, distance):
        """
        指定した方向に指定した距離だけドローンを移動させる
        
        Parameters:
            direction (str): 移動方向 ('forward', 'back', 'left', 'right', 'up', 'down')
            distance (int): 移動距離(cm、20-500)
        
        Returns:
            bool: 成功したらTrue、失敗したらFalse
        """
        # 距離の範囲を確認(20-500cm)
        if not (20 <= distance <= 500):
            print(f"移動距離は20-500cmの範囲内である必要があります: {distance}cm")
            return False
        
        # 方向を確認
        valid_directions = ['forward', 'back', 'left', 'right', 'up', 'down']
        if direction not in valid_directions:
            print(f"無効な方向です: {direction}")
            return False
        
        # 移動コマンドを送信
        return self.send_command(f"{direction} {distance}", wait_time=4.0)

    def rotate(self, angle):
        """
        ドローンを指定した角度だけ回転させる
        
        Parameters:
            angle (int): 回転角度(度)、正の値で時計回り、負の値で反時計回り
        
        Returns:
            bool: 成功したらTrue、失敗したらFalse
        """
        if angle > 0:
            return self.send_command(f"cw {angle}", wait_time=3.0)
        else:
            return self.send_command(f"ccw {abs(angle)}", wait_time=3.0)

    def send_rc_control(self, left_right, forward_backward, up_down, yaw):
        """
        RCコントロールコマンドを送信する(リアルタイムの速度制御)

        Parameters:
            left_right (int): 左右の移動速度 (-100〜100)
            forward_backward (int): 前後の移動速度 (-100〜100)
            up_down (int): 上下の移動速度 (-100〜100)
            yaw (int): 回転速度 (-100〜100)
        
        Returns:
            bool: 成功したらTrue、失敗したらFalse
        """
        # 値の範囲を-100〜100に制限
        left_right = max(-100, min(100, int(left_right)))
        forward_backward = max(-100, min(100, int(forward_backward)))
        up_down = max(-100, min(100, int(up_down)))
        yaw = max(-100, min(100, int(yaw)))
        
        # rcコマンドの送信(待機時間はほぼ0)
        result = self.send_command(
            f"rc {left_right} {forward_backward} {up_down} {yaw}", wait_time=0.05
        )
        # 文字列や他の型の場合はTrueと見なす(正常に送信された)
        return bool(result)

    def start_video_stream(self):
        """
        ビデオストリーミングを開始する
        
        Returns:
            bool: 成功したらTrue、失敗したらFalse
        """
        return self.send_command("streamon", wait_time=2.0)

    def stop_video_stream(self):
        """
        ビデオストリーミングを停止する
        
        Returns:
            bool: 成功したらTrue、失敗したらFalse
        """
        return self.send_command("streamoff", wait_time=1.0)

    def get_battery(self):
        """
        バッテリー残量を取得する
        
        Returns:
            int: バッテリー残量(%)、エラー時は-1
        """
        response = self.send_command("battery?", wait_time=0.5, expect_response=True)
        try:
            if response and isinstance(response, str) and response.isdigit():
                return int(response)
            return -1
        except (ValueError, TypeError):
            return -1

    def get_telemetry_data(self):
        """
        テレメトリーデータを取得する
        
        Returns:
            dict: テレメトリーデータ(高度、姿勢、速度など)、エラー時はNone
        """
        # Telloから状態情報を取得
        response = self.send_command("state?", wait_time=0.5, expect_response=True)
        if not response or not isinstance(response, str):
            return None
        
        try:
            # レスポンスをキーと値のペアに分割
            data = {}
            for pair in response.split(';'):
                if not pair:
                    continue
                key, _, value = pair.partition(':')
                # 数値に変換可能な値を変換
                try:
                    data[key] = float(value)
                except ValueError:
                    data[key] = value
            return data
        except Exception as e:
            print(f"テレメトリーデータの解析エラー: {e}")
            return None

    def close(self):
        """ソケットを閉じる"""
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
