# Makefile for AWS Lambda vs VM Cost Simulator
# 日々の開発作業を効率化するためのコマンド集

# Project configuration
PROJECT_NAME := cost-sim-vm-lambda
PYTHON_VERSION := 3.11.8
NODE_VERSION := 20.11.0

# Colors for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

# Default target
.DEFAULT_GOAL := help

# Check if mise is available
.PHONY: check-mise
check-mise:
	@which mise > /dev/null || (echo "$(RED)Error: mise is not installed$(RESET)" && exit 1)

# =============================================================================
# Environment Setup
# =============================================================================

.PHONY: setup
setup: check-mise ## 🚀 初回環境構築（mise + 依存関係インストール）
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	mise trust
	mise install
	mise run install
	mise run pre-commit-install
	@echo "$(GREEN)✅ Setup completed!$(RESET)"

.PHONY: install
install: check-mise ## 📦 依存関係の再インストール
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	mise run install
	@echo "$(GREEN)✅ Dependencies installed!$(RESET)"

.PHONY: clean
clean: ## 🧹 キャッシュ・一時ファイルのクリーンアップ
	@echo "$(BLUE)Cleaning up cache and temporary files...$(RESET)"
	mise run clean
	@echo "$(GREEN)✅ Cleanup completed!$(RESET)"

.PHONY: clean-all
clean-all: clean ## 🗑️  完全クリーンアップ（mise環境も含む）
	@echo "$(YELLOW)Removing mise tools cache...$(RESET)"
	rm -rf ~/.local/share/mise/installs/python/$(PYTHON_VERSION) || true
	rm -rf ~/.local/share/mise/installs/node/$(NODE_VERSION) || true
	@echo "$(GREEN)✅ Complete cleanup finished!$(RESET)"

# =============================================================================
# Development Tasks
# =============================================================================

.PHONY: test
test: check-mise ## 🧪 テスト実行（カバレッジ付き）
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	mise run test

.PHONY: t
t: test ## 🧪 テスト実行（短縮形）

.PHONY: test-unit
test-unit: check-mise ## 🔬 単体テストのみ実行
	@echo "$(BLUE)Running unit tests...$(RESET)"
	mise run test-unit

.PHONY: test-watch
test-watch: check-mise ## 👀 ファイル変更監視付きテスト
	@echo "$(BLUE)Running tests in watch mode...$(RESET)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(RESET)"
	pytest tests/ --cov=app -f

.PHONY: lint
lint: check-mise ## 🔍 全品質チェック（black, isort, flake8, mypy）
	@echo "$(BLUE)Running linting checks...$(RESET)"
	mise run lint

.PHONY: l
l: lint ## 🔍 品質チェック（短縮形）

.PHONY: format
format: check-mise ## ✨ コードフォーマット（black + isort）
	@echo "$(BLUE)Formatting code...$(RESET)"
	mise run format
	@echo "$(GREEN)✅ Code formatted!$(RESET)"

.PHONY: f
f: format ## ✨ フォーマット（短縮形）

.PHONY: check
check: format lint test ## ✅ コミット前の全チェック（format + lint + test）
	@echo "$(GREEN)✅ All checks passed!$(RESET)"

.PHONY: dev
dev: check-mise ## 🚀 開発サーバー起動
	@echo "$(BLUE)Starting development server...$(RESET)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(RESET)"
	mise run dev

.PHONY: dev-bg
dev-bg: check-mise ## 🚀 バックグラウンドで開発サーバー起動
	@echo "$(BLUE)Starting development server in background...$(RESET)"
	nohup mise run dev > dev.log 2>&1 &
	@echo "$(GREEN)✅ Server started! Check dev.log for output$(RESET)"

.PHONY: dev-stop
dev-stop: ## 🛑 バックグラウンド開発サーバー停止
	@echo "$(BLUE)Stopping background development server...$(RESET)"
	pkill -f "python app/main.py" || echo "No server process found"
	rm -f nohup.out dev.log
	@echo "$(GREEN)✅ Server stopped!$(RESET)"

# =============================================================================
# Git & CI Tasks
# =============================================================================

.PHONY: pre-commit
pre-commit: check-mise ## 🔧 pre-commitフック手動実行
	@echo "$(BLUE)Running pre-commit hooks...$(RESET)"
	pre-commit run --all-files

.PHONY: commit-ready
commit-ready: clean format lint test ## 📝 コミット準備完了チェック
	@echo "$(GREEN)🎉 Ready to commit!$(RESET)"
	@echo "$(BLUE)Run: git add . && git commit -m 'your message'$(RESET)"

.PHONY: status
status: ## 📊 プロジェクト状況確認
	@echo "$(BLUE)=== Project Status ===$(RESET)"
	@echo "Project: $(PROJECT_NAME)"
	@echo "Python: $(shell python --version 2>/dev/null || echo 'Not found')"
	@echo "Node: $(shell node --version 2>/dev/null || echo 'Not found')"
	@echo "Mise: $(shell mise --version 2>/dev/null || echo 'Not found')"
	@echo ""
	@echo "$(BLUE)=== Git Status ===$(RESET)"
	@git status --short 2>/dev/null || echo "Not a git repository"
	@echo ""
	@echo "$(BLUE)=== Test Coverage ===$(RESET)"
	@if [ -f htmlcov/index.html ]; then echo "Coverage report: file://$(PWD)/htmlcov/index.html"; else echo "Run 'make test' to generate coverage report"; fi

# =============================================================================
# Documentation & Utilities
# =============================================================================

.PHONY: docs
docs: ## 📚 ドキュメント生成（将来の機能）
	@echo "$(YELLOW)Documentation generation not implemented yet$(RESET)"

.PHONY: requirements
requirements: ## 📋 依存関係の更新チェック
	@echo "$(BLUE)Checking for outdated packages...$(RESET)"
	pip list --outdated

.PHONY: security
security: ## 🔒 セキュリティチェック
	@echo "$(BLUE)Running security checks...$(RESET)"
	pip install bandit safety --quiet
	bandit -r app/ -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true
	@echo "$(GREEN)✅ Security check completed! Check *-report.json files$(RESET)"

.PHONY: info
info: ## ℹ️  プロジェクト情報表示
	@echo "$(BLUE)=== $(PROJECT_NAME) Information ===$(RESET)"
	@echo "Description: AWS Lambda vs VM Cost Comparison Simulator"
	@echo "Python Version: $(PYTHON_VERSION)"
	@echo "Node Version: $(NODE_VERSION)"
	@echo "Framework: Flask + pytest + Chart.js"
	@echo "Repository: $(shell git remote get-url origin 2>/dev/null || echo 'Local only')"
	@echo ""
	@echo "$(BLUE)=== Quick Commands ===$(RESET)"
	@echo "Development: make dev"
	@echo "Testing: make test (or make t)"
	@echo "Linting: make lint (or make l)"
	@echo "Formatting: make format (or make f)"
	@echo "All checks: make check"

# =============================================================================
# Docker Tasks
# =============================================================================

# Docker configuration
DOCKER_IMAGE := cost-sim-vm-lambda
DOCKER_CONTAINER := cost-sim
PORT ?= 5001
ENV ?= production

.PHONY: docker-build
docker-build: ## 🐳 Dockerイメージをビルド
	@echo "$(BLUE)Building Docker image...$(RESET)"
	docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)✅ Docker image built: $(DOCKER_IMAGE)$(RESET)"

.PHONY: docker-run
docker-run: ## 🚀 Dockerコンテナを起動
	@echo "$(BLUE)Starting Docker container...$(RESET)"
	docker run -d -p $(PORT):5001 --name $(DOCKER_CONTAINER) $(DOCKER_IMAGE)
	@echo "$(GREEN)✅ Container started: http://localhost:$(PORT)$(RESET)"

.PHONY: docker-run-env
docker-run-env: ## 🌐 環境変数付きでDockerコンテナを起動
	@echo "$(BLUE)Starting Docker container with environment variables...$(RESET)"
	docker run -d -p $(PORT):$(PORT) \
		-e PORT=$(PORT) \
		-e FLASK_ENV=$(ENV) \
		--name $(DOCKER_CONTAINER) $(DOCKER_IMAGE)
	@echo "$(GREEN)✅ Container started with PORT=$(PORT) ENV=$(ENV)$(RESET)"

.PHONY: docker-stop
docker-stop: ## 🛑 Dockerコンテナを停止・削除
	@echo "$(BLUE)Stopping Docker container...$(RESET)"
	docker stop $(DOCKER_CONTAINER) 2>/dev/null || true
	docker rm $(DOCKER_CONTAINER) 2>/dev/null || true
	@echo "$(GREEN)✅ Container stopped$(RESET)"

.PHONY: docker-clean
docker-clean: docker-stop ## 🧹 Dockerイメージとコンテナを削除
	@echo "$(BLUE)Cleaning Docker images and containers...$(RESET)"
	docker rmi $(DOCKER_IMAGE) 2>/dev/null || true
	@echo "$(GREEN)✅ Docker cleanup completed$(RESET)"

.PHONY: docker-logs
docker-logs: ## 📋 Dockerコンテナのログを表示
	@echo "$(BLUE)Showing Docker container logs...$(RESET)"
	docker logs $(DOCKER_CONTAINER)

.PHONY: docker-exec
docker-exec: ## 🖥️  Dockerコンテナに入る
	@echo "$(BLUE)Entering Docker container...$(RESET)"
	docker exec -it $(DOCKER_CONTAINER) /bin/bash

.PHONY: docker-restart
docker-restart: docker-stop docker-run ## 🔄 Dockerコンテナを再起動

.PHONY: docker-rebuild
docker-rebuild: docker-clean docker-build docker-run ## 🔄 Docker完全再構築

.PHONY: docker-stats
docker-stats: ## 📊 Dockerコンテナの統計情報
	@echo "$(BLUE)Docker container statistics:$(RESET)"
	docker stats $(DOCKER_CONTAINER) --no-stream

.PHONY: docker-size
docker-size: ## 📏 Dockerイメージサイズを確認
	@echo "$(BLUE)Docker image size:$(RESET)"
	docker images $(DOCKER_IMAGE) --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

.PHONY: docker-health
docker-health: ## 🏥 Dockerコンテナのヘルスチェック
	@echo "$(BLUE)Docker container health status:$(RESET)"
	docker inspect $(DOCKER_CONTAINER) --format='{{.State.Health.Status}}' 2>/dev/null || echo "Health check not available"

.PHONY: help
help: ## 📖 利用可能なコマンド一覧
	@echo "$(BLUE)Available commands for $(PROJECT_NAME):$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)Examples:$(RESET)"
	@echo "  make setup          # 初回環境構築"
	@echo "  make test           # テスト実行"
	@echo "  make dev            # 開発サーバー起動"
	@echo "  make check          # 全チェック実行"
	@echo ""
	@echo "$(BLUE)Docker commands:$(RESET)"
	@echo "  make docker-build   # Dockerイメージ作成"
	@echo "  make docker-run     # Dockerコンテナ起動"
	@echo "  make docker-stop    # Dockerコンテナ停止"
	@echo "  make docker-rebuild # Docker完全再構築"
	@echo ""
	@echo "$(BLUE)Short commands:$(RESET)"
	@echo "  make t              # test"
	@echo "  make l              # lint"
	@echo "  make f              # format"