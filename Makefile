# Tello XR Proto Makefile

.PHONY: venv install clean run help

# Python実行コマンド
PYTHON := python3
# 仮想環境のディレクトリ
VENV_DIR := venv
# 仮想環境のactivateスクリプトへのパス
VENV_ACTIVATE := $(VENV_DIR)/bin/activate

help:
	@echo "使用可能なコマンド:"
	@echo "  make venv      - 仮想環境を作成"
	@echo "  make install   - 依存パッケージをインストール"
	@echo "  make activate  - 仮想環境に接続（シェル変数を設定）"
	@echo "  make run       - メインプログラムを実行"
	@echo "  make clean     - 一時ファイルとキャッシュを削除"

# 仮想環境の作成
venv:
	@echo "Python仮想環境を作成しています..."
	@$(PYTHON) -m venv $(VENV_DIR)
	@echo "仮想環境が作成されました。'source $(VENV_ACTIVATE)'で有効化してください。"

# 依存パッケージのインストール
install: venv
	@echo "依存パッケージをインストールしています..."
	@. $(VENV_ACTIVATE) && pip install -r requirements.txt
	@echo "依存パッケージのインストールが完了しました。"

# 仮想環境の有効化（直接シェルで実行する必要があります）
activate:
	@echo "仮想環境を有効化するには以下のコマンドを実行してください:"
	@echo "source $(VENV_ACTIVATE)"

# プログラムの実行
run:
	@if [ -f $(VENV_ACTIVATE) ]; then \
		. $(VENV_ACTIVATE) && python main.py; \
	else \
		echo "仮想環境が見つかりません。まず 'make venv' を実行してください。"; \
		exit 1; \
	fi

# クリーンアップ
clean:
	@echo "一時ファイルとキャッシュを削除しています..."
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".DS_Store" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "*.egg" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "クリーンアップが完了しました。"