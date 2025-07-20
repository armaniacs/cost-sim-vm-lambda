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

### 方法1: .mise.toml (推奨)
**すでに設定済み** - `make dev` で自動的に読み込まれます。

### 方法2: 手動設定
```bash
export SECRET_KEY="your-secret-key"
export CSRF_SECRET_KEY="your-csrf-key"
export JWT_SECRET_KEY="your-jwt-key"
make dev
```

### 方法3: .env ファイル
```bash
# .env.development ファイルをコピー
cp .env.development .env.local

# .env.local を編集
# その後
source .env.local
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
1. `.mise.toml` の環境変数設定を確認
2. 手動で環境変数をエクスポート:
   ```bash
   export SECRET_KEY=dev-secret-key
   export CSRF_SECRET_KEY=dev-csrf-key
   export JWT_SECRET_KEY=dev-jwt-key
   make dev
   ```

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