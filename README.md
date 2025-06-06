# 🛸 Tello XR Controller（プロトタイプ）

このプロジェクトは、Ryze Tello ドローンをゲームパッドで操作し、リアルタイムの映像を XR ゴーグル（例：VITURE）で表示する体験を Python でプロトタイピングするものです。没入型のドローン操作体験を手軽に構築することを目的としています。

## 🚀 主な機能

- ゲームパッドによる Tello ドローンの操作（Xbox / PS4 など対応）
- リアルタイムの FPV（First Person View）映像表示
- HDMI 経由の XR ヘッドセットに映像出力（外部ディスプレイ扱い）
- Unity 移行を前提としたシンプルなモジュール構造
- コントローラー設定の JSON 形式保存とカスタマイズ機能
- コントローラーのキャリブレーション機能
- コントローラー入力とドローン制御の連携機能

## 🧱 ディレクトリ構成

```bash
tello_xr_proto/
  ├── main.py         # メインエントリーポイント、モジュールの統合
  ├── video_stream.py # 映像ストリーミング処理用モジュール
  ├── tello_control.py # Telloドローン制御用モジュール
  ├── controller_input.py # ゲームパッド入力処理用モジュール
  ├── config/         # 設定ファイル格納ディレクトリ
  │   └── controller_config.json # コントローラー設定ファイル
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

### 基本操作

#### コントローラー操作

- **左スティック**: 左右・前後移動
- **右スティック**: 上下移動・回転
- **A/X ボタン**: 離陸
- **B/O ボタン**: 着陸
- **X/□ ボタン**: 緊急停止
- **Y/△ ボタン**: 写真撮影（将来実装予定）

#### キーボード操作

- **q**: プログラム終了

### 現在実装されている機能

- Tello ドローンとの UDP 通信接続確立
- ドローンからのリアルタイム映像受信・表示
- 'q'キーによるプログラム終了
- モジュール分割によるコード整理と再利用性の向上
  - `video_stream.py`: 映像ストリーミング関連の機能
  - `tello_control.py`: ドローン制御関連の機能
  - `controller_input.py`: ゲームパッド入力処理関連の機能
  - `main.py`: 各モジュールを結合する統合機能
- ゲームパッド検出と入力処理の実装：
  - 複数のコントローラー種別に対応（Xbox、PS4、その他）
  - コントローラーの接続・切断の自動検出
  - アナログスティックとボタンの入力読み取り
  - ドローン操作向けに最適化された入力値の正規化
- コントローラー設定のカスタマイズ機能：
  - JSON 形式の設定ファイルによるマッピングのカスタマイズ
  - 軸とボタンのマッピングをユーザーが自由に定義可能
  - デッドゾーン、感度、軸反転などの詳細設定
  - 設定が見つからない場合はデフォルト設定を自動生成
- コントローラー入力の最適化：
  - スティック軸のキャリブレーション機能
  - 中心位置のオフセット自動補正
  - 複数サンプルによる高精度なキャリブレーション
  - キャリブレーション結果の設定ファイルへの自動保存
- コントローラー入力とドローン制御の連携：
  - コントローラーのボタン入力による離陸、着陸、緊急停止
  - スティック入力によるリアルタイムの速度制御（RC 制御）
  - 前回の入力状態を記憶し、ボタンの連続実行を防止
  - 飛行状態に応じた制御の有効/無効切替
  - 適切なタイミングでの RC コマンド送信（遅延とパケットロス対策）

### コントローラー設定ファイル

コントローラー設定は `config/controller_config.json` に保存され、以下の項目をカスタマイズできます：

```json
{
  "deadzone": 0.15, // スティック入力のデッドゾーン（0.0-1.0）
  "axis_mapping": {
    // 軸のマッピング
    "move_x": 0, // 左右移動（左スティックX軸）
    "move_y": 1, // 前後移動（左スティックY軸）
    "move_z": 3, // 上下移動（右スティックY軸）
    "rotation": 2 // 回転（右スティックX軸）
  },
  "button_mapping": {
    // ボタンのマッピング
    "takeoff": 0, // 離陸（A/Xボタン）
    "land": 1, // 着陸（B/Oボタン）
    "emergency": 2, // 緊急停止（X/□ボタン）
    "photo": 3 // 写真撮影（Y/△ボタン）
  },
  "invert_axis": {
    // 軸の反転設定
    "move_y": true, // 前後移動は反転（前進が-1）
    "move_z": true // 上下移動は反転（上昇が-1）
  },
  "sensitivity": {
    // 感度設定
    "move_xy": 1.0, // 水平移動の感度
    "move_z": 0.7, // 垂直移動の感度
    "rotation": 0.8 // 回転の感度
  }
}
```

### キャリブレーション機能

コントローラーキャリブレーションは以下の手順で実行できます：

```bash
# コントローラー入力モジュールを単独で実行
python controller_input.py

# メニューから「2: コントローラーキャリブレーション」を選択
```

キャリブレーションにより、コントローラーのスティック中心位置のずれを補正し、より正確な操作が可能になります。

## 💡 補足

- UDP 通信のため、Tello の Wi-Fi に安定して接続されている必要があります
- XR ゴーグルは外部ディスプレイとして認識される必要があります
- Unity 対応に向けた拡張も視野に入れています
- ゲームパッド接続を確認するには `python controller_input.py` を実行

## 📅 開発状況（2025 年 5 月 8 日現在）

- [x] プロジェクト構想の策定
- [x] リポジトリの作成
- [x] 開発環境の構築（Python 仮想環境、パッケージ管理）
- [x] Tello との基本的な通信確立
- [x] ドローンからの映像ストリーミング表示
- [x] モジュール分割によるコード整理
- [x] ゲームパッド検出モジュールの実装
- [x] JSON 設定ファイルによるコントローラーカスタマイズ機能
- [x] コントローラーキャリブレーション機能の実装
- [x] ゲームパッド入力とドローン制御の連携
- [ ] 飛行制御機能の拡張と最適化
- [ ] 統合テスト
- [ ] マニュアル整備

## 🚩 将来の拡張予定

- コントローラー設定のプロファイル機能（[Issue #15](https://github.com/t-ishitsuka/tello_xr_proto/issues/15))
  - 複数コントローラー対応
  - プロファイル名付きの設定管理
  - 実行中のプロファイル切り替え
- コントローラー入力の可視化とフィードバック（[Issue #16](https://github.com/t-ishitsuka/tello_xr_proto/issues/16))
  - 入力状態のビデオストリームへの重ね表示
  - スティック入力の視覚的表現
  - ドローン状態情報のオンスクリーン表示
- ビデオストリームの安定性と応答性の向上（[Issue #18](https://github.com/t-ishitsuka/tello_xr_proto/issues/18))
  - バッファリング戦略の最適化
  - 低遅延モードの導入
  - フレームスキップ戦略の実装
- ドローン制御の速度調整と操作性向上（[Issue #19](https://github.com/t-ishitsuka/tello_xr_proto/issues/19))
  - 速度スケールの調整
  - 低速/中速/高速モードの導入
  - 速度変化率の制限による滑らかな操作

## 🐛 既知の問題

- H.264 ストリーミングの初期化時に「non-existing PPS 0 referenced」エラーが表示される場合がありますが、FFmpeg バックエンドの使用により改善されています
- まれに映像ストリームの初期化に失敗する場合がありますが、リトライ処理により自動的に再接続を試みます
- コントローラーによって軸とボタンのマッピングが異なる場合は、`config/controller_config.json`ファイルを編集して調整できます
- 映像に遅延が発生することがあり、操作性に影響を与える場合があります（[Issue #18](https://github.com/t-ishitsuka/tello_xr_proto/issues/18)で対応予定）
- ドローンの移動速度が速すぎて細かい操作が難しい場合があります（[Issue #19](https://github.com/t-ishitsuka/tello_xr_proto/issues/19)で対応予定）
