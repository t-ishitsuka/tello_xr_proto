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
  ├── main.py         # メインエントリーポイント、モジュールの統合
  ├── video_stream.py # 映像ストリーミング処理用モジュール
  ├── tello_control.py # Telloドローン制御用モジュール
  ├── requirements.txt # 依存パッケージの一覧
  ├── Makefile        # 開発補助コマンド集
  ├── .gitignore      # Gitが無視するファイルの設定
  └── README.md       # このファイル
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

Tello を起動し、PC を Tello の Wi-Fi に接続してから実行します：

```bash
# 仮想環境を有効化
source venv/bin/activate  # Windowsは venv\Scripts\activate

# プログラムを実行
python main.py

# またはMakefileを使用
make run
```

### 現在実装されている機能

- Tello ドローンとの UDP 通信接続確立
- ドローンからのリアルタイム映像受信・表示
- 'q'キーによるプログラム終了
- モジュール分割によるコード整理と再利用性の向上
  - `video_stream.py`: 映像ストリーミング関連の機能
  - `tello_control.py`: ドローン制御関連の機能
  - `main.py`: 各モジュールを結合する統合機能

### 今後実装予定の機能

- ゲームパッド操作：
  - 左スティック：前後左右移動
  - 右スティック：上昇／下降・回転
  - A ボタン：離陸
  - B ボタン：着陸

## 💡 補足

- UDP 通信のため、Tello の Wi-Fi に安定して接続されている必要があります
- XR ゴーグルは外部ディスプレイとして認識される必要があります
- Unity 対応に向けた拡張も視野に入れています

## 📅 開発状況（2025 年 5 月 3 日現在）

- [x] プロジェクト構想の策定
- [x] リポジトリの作成
- [x] 開発環境の構築（Python 仮想環境、パッケージ管理）
- [x] Tello との基本的な通信確立
- [x] ドローンからの映像ストリーミング表示
- [x] モジュール分割によるコード整理
- [ ] ゲームパッド入力の連携
- [ ] 飛行制御機能の実装
- [ ] 統合テスト
- [ ] マニュアル整備

## 🐛 既知の問題

- H.264 ストリーミングの初期化時に「non-existing PPS 0 referenced」エラーが表示される場合がありますが、FFmpeg バックエンドの使用により改善されています
- まれに映像ストリームの初期化に失敗する場合がありますが、リトライ処理により自動的に再接続を試みます
