# 開発環境セットアップガイド

## 🔐 セキュリティ要件

このアプリケーションは**エンタープライズ級セキュリティ**を実装しており、起動時に以下の環境変数が必須です：

### 必須環境変数
- `SECRET_KEY`: Flaskアプリケーションのシークレットキー
- `CSRF_SECRET_KEY`: CSRF保護用シークレットキー  
- `JWT_SECRET_KEY`: JWT認証用シークレットキー

## 🚀 クイックスタート

### 1. 初回セットアップ
```bash
# リポジトリクローン
git clone <repository-url>
cd cost-sim-vm-lambda

# 環境構築
make setup
```

### 2. 開発サーバー起動
```bash
# 環境変数は .mise.toml で自動設定されます
make dev
```

**アクセス**: http://127.0.0.1:5001

## 🛠️ 環境変数設定方法

### 方法1: .mise.local.toml (推奨)
```bash
# サンプルファイルをコピー
cp .mise.local.toml.example .mise.local.toml

# セキュアなキーを生成
export SECRET_KEY=$(openssl rand -hex 32)
export CSRF_SECRET_KEY=$(openssl rand -hex 32)  
export JWT_SECRET_KEY=$(openssl rand -hex 32)

# .mise.local.toml ファイルを編集して上記のキーを設定
# その後、開発サーバー起動
make dev
```

### 方法2: 手動環境変数設定
```bash
# セキュアなキーを生成
export SECRET_KEY=$(openssl rand -hex 32)
export CSRF_SECRET_KEY=$(openssl rand -hex 32)
export JWT_SECRET_KEY=$(openssl rand -hex 32)
make dev
```

### 方法3: .env.development ファイル
```bash
# サンプルファイルをコピー
cp .env.development.example .env.development

# .env.development ファイルを編集してセキュアなキーに変更
source .env.development
make dev
```

## 🔧 開発コマンド

```bash
# テスト実行
make test          # または make t

# コード品質チェック
make lint          # または make l

# フォーマット
make format        # または make f

# 全チェック
make check

# ヘルプ
make help
```

## 🐳 Docker開発

```bash
# Dockerイメージビルド
make docker-build

# Dockerコンテナ起動
make docker-run

# Docker環境での開発
make docker-exec
```

## 🔍 トラブルシューティング

### エラー: "SECRET_KEY environment variable is required"

**原因**: セキュリティ環境変数が設定されていない

**解決方法**:
1. **推奨**: セキュアなキーを生成:
   ```bash
   # セキュアなキーを生成
   export SECRET_KEY=$(openssl rand -hex 32)
   export CSRF_SECRET_KEY=$(openssl rand -hex 32)
   export JWT_SECRET_KEY=$(openssl rand -hex 32)
   
   # アプリケーション起動
   make dev
   ```

2. **または**: .mise.local.toml を使用:
   ```bash
   cp .mise.local.toml.example .mise.local.toml
   # .mise.local.toml を編集してセキュアなキーに変更
   make dev
   ```

**重要**: 本番環境では必ずセキュアなランダムキーを使用してください。

### Redis接続エラー (WARNING)
```
WARNING: Anomaly detector Redis connection failed
```

**これは正常です** - 開発環境ではRedisは必須ではありません。

### ポート衝突エラー
```bash
# 別のポートを使用
PORT=8000 make dev
```

## 🔐 セキュリティ機能

開発サーバーでも以下のセキュリティ機能が有効です：

- ✅ JWT認証
- ✅ CSRF保護
- ✅ CORS設定
- ✅ 入力検証
- ✅ XSS/SQLインジェクション対策
- ✅ セキュリティヘッダー
- ✅ 監査ログ
- ✅ データ整合性チェック

## 📚 参考資料

- [API仕様書](ref/api-endpoints-reference.md)
- [アーキテクチャ文書](ref/architecture-overview.md)
- [セキュリティ実装報告書](Design/security-implementation-report.md)
- [テスト戦略](ref/testing-framework-guide.md)