# Makefile使用ガイド

## 概要

このプロジェクトでは、日々の開発作業を効率化するためのMakefileを提供しています。
mise環境と連携し、一般的な開発タスクを簡単なコマンドで実行できます。

## 基本的な使い方

### ヘルプ表示
```bash
make help
# または
make
```

利用可能な全コマンドと説明が表示されます。

### 初回セットアップ
```bash
make setup
```

以下の処理を自動実行：
- mise環境のセットアップ
- Python/Node.jsのインストール
- 依存関係のインストール
- pre-commitフックの設定

## コマンド一覧

### 🚀 環境管理

| コマンド | 説明 |
|---------|------|
| `make setup` | 初回環境構築 |
| `make install` | 依存関係の再インストール |
| `make clean` | キャッシュ・一時ファイルのクリーンアップ |
| `make clean-all` | 完全クリーンアップ（mise環境も削除） |

### 🧪 テスト関連

| コマンド | 説明 |
|---------|------|
| `make test` / `make t` | テスト実行（カバレッジ付き） |
| `make test-unit` | 単体テストのみ実行 |
| `make test-watch` | ファイル変更監視付きテスト |

### 🔍 コード品質

| コマンド | 説明 |
|---------|------|
| `make lint` / `make l` | 全品質チェック |
| `make format` / `make f` | コードフォーマット |
| `make check` | 全チェック（format + lint + test） |

### 🚀 開発サーバー

| コマンド | 説明 |
|---------|------|
| `make dev` | 開発サーバー起動 |
| `make dev-bg` | バックグラウンドで起動 |
| `make dev-stop` | バックグラウンドサーバー停止 |

### 📝 Git・CI関連

| コマンド | 説明 |
|---------|------|
| `make pre-commit` | pre-commitフック手動実行 |
| `make commit-ready` | コミット準備完了チェック |

### 📊 情報表示

| コマンド | 説明 |
|---------|------|
| `make status` | プロジェクト状況確認 |
| `make info` | プロジェクト情報表示 |
| `make security` | セキュリティチェック |

## 日常的な開発ワークフロー

### 1. 朝の開発開始時
```bash
# プロジェクト状況確認
make status

# 最新のテストを実行
make test

# 開発サーバー起動
make dev
```

### 2. コード変更中
```bash
# テスト実行（短縮形）
make t

# コードフォーマット（短縮形）
make f

# 品質チェック（短縮形）
make l
```

### 3. コミット前
```bash
# 全チェック実行
make check

# または段階的に
make format    # フォーマット適用
make lint      # 品質チェック
make test      # テスト実行

# 準備完了確認
make commit-ready
```

### 4. 環境のメンテナンス
```bash
# キャッシュクリーンアップ
make clean

# 依存関係の更新確認
make requirements

# セキュリティチェック
make security
```

## 便利な機能

### 1. 短縮コマンド
よく使うコマンドには短縮形を用意：
- `make t` → `make test`
- `make l` → `make lint`
- `make f` → `make format`

### 2. カラー出力
コマンド実行時に色付きで状況を表示：
- 🔵 青：実行中
- 🟢 緑：成功
- 🟡 黄：警告
- 🔴 赤：エラー

### 3. 自動チェック
- mise環境の存在確認
- 必要なツールのインストール状況確認

### 4. バックグラウンド実行
```bash
# サーバーをバックグラウンドで起動
make dev-bg

# ログ確認
tail -f dev.log

# 停止
make dev-stop
```

## トラブルシューティング

### mise not found エラー
```bash
# miseのインストール確認
which mise

# 未インストールの場合
brew install mise  # macOS
```

### 依存関係エラー
```bash
# 完全な再インストール
make clean-all
make setup
```

### テスト失敗
```bash
# 詳細なテスト出力
pytest tests/ -v --tb=long

# 特定のテストのみ実行
pytest tests/unit/test_lambda_calculator.py::TestLambdaCalculator::test_lambda_calculator_initialization -v
```

### 開発サーバーが起動しない
```bash
# プロセス確認
make status

# バックグラウンドプロセス停止
make dev-stop

# 再起動
make dev
```

## 高度な使い方

### 1. 継続的テスト
```bash
# ファイル変更を監視してテスト自動実行
make test-watch
```

### 2. カスタムターゲット追加
Makefileを編集して独自のターゲットを追加可能：

```makefile
.PHONY: my-task
my-task: ## 🎯 カスタムタスク
	@echo "My custom task"
	# コマンドを追加
```

### 3. 環境変数の活用
```bash
# デバッグモードでテスト実行
FLASK_DEBUG=1 make test

# 特定の設定で開発サーバー起動
FLASK_ENV=production make dev
```

## 他のツールとの連携

### IDE統合
多くのIDEでMakefileのターゲットを直接実行可能：
- VS Code: Command Palette → "Tasks: Run Task"
- IntelliJ: Run Configurations → Makefile

### GitHub Actions
CI/CDでもMakeコマンドを使用：
```yaml
- name: Run tests
  run: make test

- name: Check code quality  
  run: make lint
```

これにより、ローカル開発とCI環境で同じコマンドを使用できます。