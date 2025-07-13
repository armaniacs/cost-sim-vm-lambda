# 開発環境セットアップガイド

## mise を使用したPython環境管理

このプロジェクトではPython環境管理に[mise](https://mise.jdx.dev/)を採用しています。

### mise のメリット
- **一元管理**: Python, Node.js, その他のツールを統一管理
- **自動切り替え**: ディレクトリ移動時の自動バージョン切り替え
- **チーム統一**: `.mise.toml`でチーム全体の環境を統一
- **高速**: pyenvやnodeenvより高速な動作

## 初回セットアップ

### 1. mise のインストール
```bash
# macOS (Homebrew)
brew install mise

# Linux/WSL
curl https://mise.run | sh

# 設定を追加 (bash/zsh)
echo 'eval "$(mise activate bash)"' >> ~/.bashrc  # bash
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc    # zsh
```

### 2. プロジェクト環境のセットアップ
```bash
# Python 3.11.8の自動インストール
mise install

# 依存関係のインストール
mise run install

# pre-commitフックのセットアップ
mise run pre-commit-install
```

### 3. 環境確認
```bash
# インストールされたツール確認
mise list

# 現在のPythonバージョン確認
python --version  # Python 3.11.8

# 仮想環境の確認
which python      # mise管理下のPython
```

## 開発ワークフロー

### 日常的な開発コマンド

```bash
# テスト実行（推奨）
mise run test              # 全テスト + カバレッジレポート
mise run test-unit         # 単体テストのみ
mise run test-integration  # 統合テストのみ

# コード品質チェック
mise run lint              # 全品質チェック実行
mise run format            # コードフォーマット適用

# 開発サーバー
mise run dev               # Flask開発サーバー起動

# メンテナンス
mise run clean             # キャッシュ等のクリーンアップ
```

### 詳細なテスト実行
```bash
# カバレッジ詳細表示
mise run test

# 特定のテストファイル
pytest tests/unit/test_lambda_calculator.py -v

# テストマーカー使用
pytest -m unit            # 単体テストのみ
pytest -m "not slow"      # 重いテスト除外
pytest -m integration     # 統合テストのみ

# 並列テスト実行（高速化）
pytest -n auto            # CPU数に応じて自動並列化
```

### コード品質管理
```bash
# 個別チェック
black --check app/ tests/              # フォーマットチェック
black app/ tests/                      # フォーマット適用
isort --check-only app/ tests/         # import順序チェック
isort app/ tests/                      # import順序修正
flake8 app/ tests/                     # リントチェック
mypy app/                              # 型チェック

# 全チェック一括実行
mise run lint
```

## 設定ファイル詳細

### .mise.toml の構成
```toml
[tools]
python = "3.11.8"          # Pythonバージョン固定
node = "20.11.0"           # Node.js (将来のフロントエンド用)

[env]
FLASK_ENV = "development"   # Flask開発モード
FLASK_DEBUG = "1"          # デバッグモード有効
PYTHONPATH = "."           # パス設定

[tasks.*]                  # 開発タスクの定義
```

### 環境変数の活用
```bash
# 自動設定される環境変数
echo $FLASK_ENV           # development
echo $FLASK_DEBUG         # 1
echo $PYTHONPATH          # .

# 手動での環境変数設定
export FLASK_ENV=production
export DATABASE_URL=sqlite:///prod.db
```

## トラブルシューティング

### よくある問題と解決法

#### 1. mise が認識されない
```bash
# シェルの設定確認
echo $SHELL
cat ~/.zshrc | grep mise   # zshの場合

# mise activate の追加
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc
source ~/.zshrc
```

#### 2. Python バージョンが切り替わらない
```bash
# mise の状態確認
mise doctor

# 強制再インストール
mise uninstall python 3.11.8
mise install python 3.11.8
```

#### 3. 依存関係のインストールエラー
```bash
# pip のアップグレード
python -m pip install --upgrade pip

# 依存関係の再インストール
mise run clean
mise run install
```

#### 4. テスト実行エラー
```bash
# PYTHONPATH の確認
echo $PYTHONPATH

# 手動でのPYTHONPATH設定
export PYTHONPATH=.
mise run test
```

## チーム開発での注意点

### 1. 環境統一
- `.mise.toml` は必ずコミット
- 新メンバーは `mise install` のみで環境構築完了
- バージョン変更時はチーム全体に周知

### 2. CI/CD との統合
- GitHub Actions でも mise を使用
- Docker での mise 使用も可能

### 3. 既存環境からの移行
```bash
# 既存のvenv環境は削除
rm -rf venv/

# pyenv と併用する場合
mise use python@system  # システムPython使用
mise use python@3.11.8  # 特定バージョン使用
```

## パフォーマンス比較

| 環境管理ツール | 切り替え速度 | メモリ使用量 | 機能豊富さ |
|--------------|------------|------------|-----------|
| mise         | ★★★★★      | ★★★★★      | ★★★★★     |
| pyenv        | ★★★☆☆      | ★★★☆☆      | ★★★☆☆     |
| venv         | ★★☆☆☆      | ★★★★☆      | ★☆☆☆☆     |
| conda        | ★★☆☆☆      | ★★☆☆☆      | ★★★★★     |

mise の採用により、開発効率と環境統一性が大幅に向上します。