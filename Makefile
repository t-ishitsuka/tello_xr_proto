# Tello XR Proto Makefile

.PHONY: venv install clean run help format lint check-format fix-imports

# Python実行コマンド
PYTHON := python3
# 仮想環境のディレクトリ
VENV_DIR := venv
# 仮想環境のactivateスクリプトへのパス
VENV_ACTIVATE := $(VENV_DIR)/bin/activate

help:
	@echo "使用可能なコマンド:"
	@echo "  make venv        - 仮想環境を作成"
	@echo "  make install     - 依存パッケージをインストール"
	@echo "  make activate    - 仮想環境に接続（シェル変数を設定）"
	@echo "  make run         - メインプログラムを実行"
	@echo "  make clean       - 一時ファイルとキャッシュを削除"
	@echo "  make format      - コードを自動整形（black + isort）"
	@echo "  make lint        - コードの問題をチェック（ruff）"
	@echo "  make check-format- コード整形の問題を検出（変更なし）"
	@echo "  make fix-imports - 未使用インポートを削除（autoflake）"

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

# コードを自動整形（Black + isort）
format:
	@echo "コードを自動整形しています..."
	@if [ -f $(VENV_ACTIVATE) ]; then \
		. $(VENV_ACTIVATE) && black . && isort .; \
	else \
		echo "仮想環境が見つかりません。まず 'make venv' を実行してください。"; \
		exit 1; \
	fi
	@echo "コード整形が完了しました。"

# コードの問題をチェック（ruff）
lint:
	@echo "コードの問題をチェックしています..."
	@if [ -f $(VENV_ACTIVATE) ]; then \
		. $(VENV_ACTIVATE) && ruff check .; \
	else \
		echo "仮想環境が見つかりません。まず 'make venv' を実行してください。"; \
		exit 1; \
	fi

# コード整形の問題を検出（変更なし）
check-format:
	@echo "コード整形の問題を検出しています..."
	@if [ -f $(VENV_ACTIVATE) ]; then \
		. $(VENV_ACTIVATE) && black --check . && isort --check .; \
	else \
		echo "仮想環境が見つかりません。まず 'make venv' を実行してください。"; \
		exit 1; \
	fi

# 未使用インポートを削除（autoflake）
fix-imports:
	@echo "未使用インポートを削除しています..."
	@if [ -f $(VENV_ACTIVATE) ]; then \
		. $(VENV_ACTIVATE) && autoflake --remove-all-unused-imports --recursive --in-place .; \
	else \
		echo "仮想環境が見つかりません。まず 'make venv' を実行してください。"; \
		exit 1; \
	fi
	@echo "未使用インポートの削除が完了しました。"

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
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@echo "クリーンアップが完了しました。"