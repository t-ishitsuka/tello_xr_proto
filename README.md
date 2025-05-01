# 🛸 Tello XR Controller（プロトタイプ）

このプロジェクトは、Ryze Tello ドローンをゲームパッドで操作し、リアルタイムの映像を XR ゴーグル（例：VITURE）で表示する体験を Python でプロトタイピングするものです。没入型のドローン操作体験を手軽に構築することを目的としています。

## 🚀 主な機能

- ゲームパッドによる Tello ドローンの操作（Xbox / PS4 など対応）
- リアルタイムの FPV（First Person View）映像表示
- HDMI 経由の XR ヘッドセットに映像出力（外部ディスプレイ扱い）
- Unity 移行を前提としたシンプルなモジュール構造

## 🧱 ディレクトリ構成

```bash
tello_xr_proto/
  ├── controller.py # ゲームパッド入力の処理（予定）
  ├── tello_control.py # Telloへのコマンド送信（予定）
  ├── video_stream.py # Telloの映像ストリームを受信・表示（予定）
  ├── main.py # 各モジュールを統合・実行
  ├── requirements.txt # 依存パッケージの一覧
  ├── Makefile # 開発補助コマンド集
  └── README.md # このファイル
```

## 🛠 必要環境

- macOS または Windows（動作確認は macOS）
- Python 3.10 推奨
- Tello ドローン（Wi-Fi 接続）
- ゲームパッド（Xbox / PS 系推奨）
- オプション：XR ゴーグル（HDMI 接続対応）

## 📦 インストール手順

```bash
# リポジトリをクローン
git clone https://github.com/t-ishitsuka/tello_xr_proto.git
cd tello_xr_proto

# Makefileを使って環境を構築（推奨）
make install

# または手動で仮想環境を作成
python3 -m venv venv
source venv/bin/activate  # Windowsは venv\Scripts\activate
pip install -r requirements.txt
```

## 🛠️ 開発コマンド

プロジェクトには Makefile が用意されており、以下のコマンドが利用可能です：

```bash
make venv      # 仮想環境を作成
make install   # 依存パッケージをインストール
make activate  # 仮想環境に接続するためのコマンドを表示
make run       # メインプログラムを実行
make clean     # 一時ファイルとキャッシュを削除
```

## 🎮 操作方法

Tello を起動し、PC を Tello の Wi-Fi に接続

メインスクリプトを実行：

```bash
# 仮想環境を有効化
source venv/bin/activate  # Windowsは venv\Scripts\activate

# プログラムを実行
python main.py

# またはMakefileを使用
make run
```

計画している操作方法：

- 左スティック：前後左右移動
- 右スティック：上昇／下降・回転
- A ボタン：離陸
- B ボタン：着陸

映像がウィンドウに表示されるので、XR ゴーグルでミラー表示することで没入体験が可能になる予定です。

## 💡 補足

- UDP 通信のため、Tello の Wi-Fi に安定して接続されている必要があります
- XR ゴーグルは外部ディスプレイとして認識される必要があります
- Unity 対応に向けた拡張も視野に入れています

## 📅 開発状況（2025 年 5 月 1 日現在）

- [x] プロジェクト構想の策定
- [x] リポジトリの作成
- [x] 開発環境の構築（Python 仮想環境、パッケージ管理）
- [ ] 基本的なドローン制御モジュールの実装
- [ ] ゲームパッド入力の連携
- [ ] 映像ストリーミング処理の実装
- [ ] 統合テスト
- [ ] マニュアル整備
