#!/usr/bin/env python3
"""
Main entry point for the Tello XR prototype.
"""
import socket
import time

# TelloのIPアドレスとポート
TELLO_IP = '192.168.10.1'
TELLO_PORT = 8889
TELLO_ADDRESS = (TELLO_IP, TELLO_PORT)

def send(sock, cmd, wait=2):
    print(f"Send: {cmd}")
    sock.sendto(cmd.encode('utf-8'), TELLO_ADDRESS)
    time.sleep(wait)  # waitはコマンドの処理時間に応じて調整

def main():
    print("Tello XR prototype initialized!")
    
    try:
        # UDPソケットを作成
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # SDKモードへ
        send(sock, 'command')

        # 離陸
        send(sock, 'takeoff', wait=5)

        # 1メートル（=100cm）前進
        send(sock, 'forward 100', wait=4)

        # 着陸
        send(sock, 'land', wait=5)

        # ソケットを閉じる
        sock.close()

    except ImportError as e:
        print(f"Error importing dependencies: {e}")

if __name__ == "__main__":
    main()