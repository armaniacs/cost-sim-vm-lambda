# 開発者向けドキュメント

AWS Lambda vs VM Cost Simulatorの開発環境構築と開発手順

## 開発環境セットアップ

### 前提条件
- [mise](https://mise.jdx.dev/) がインストールされていること

### セットアップ手順

1. **Python環境の自動セットアップ**
   ```bash
   mise install
   ```

2. **依存関係のインストール**
   ```bash
   mise run install
   ```

3. **pre-commitフックのインストール**
   ```bash
   mise run pre-commit-install
   ```

### 開発用コマンド

**🚀 Makeコマンド（推奨）**
```bash
# 日常的な開発作業
make test       # テスト実行（カバレッジ付き）
make lint       # コード品質チェック
make format     # コードフォーマット
make dev        # 開発サーバー起動（http://localhost:5001）
make check      # 全チェック（format + lint + test）

# 短縮コマンド
make t          # test
make l          # lint  
make f          # format

# 環境管理
make setup      # 初回環境構築
make clean      # キャッシュクリーンアップ
make status     # プロジェクト状況確認
```

**mise直接コマンド**
```bash
# テスト実行
mise run test           # 全テスト + カバレッジ
mise run test-unit      # 単体テストのみ

# コード品質チェック
mise run lint           # リント実行
mise run format         # コードフォーマット

# 開発サーバー起動
mise run dev            # http://localhost:5001 で起動

# クリーンアップ
mise run clean
```

### 開発ワークフロー例
```bash
# 開発開始時
make setup              # 初回のみ

# 日常の開発サイクル
make dev               # 開発サーバー起動（http://localhost:5001）
make t                 # テスト実行
make f                 # コードフォーマット

# コミット前
make check             # 全チェック実行
git add . && git commit -m "feature: add new functionality"
```

## アプリケーション起動

### 開発サーバー起動
```bash
# 基本起動（ポート5001）
make dev

# 別ポート指定（例：ポート8000）
PORT=8000 make dev

# 直接起動
python app/main.py
```

**アクセスURL**: http://localhost:5001

**ポート競合時の対処**:
```bash
# 使用中ポートの確認
lsof -i :5001

# 環境変数で別ポート指定
PORT=8000 make dev
```

## プロジェクト構造

```
cost-sim-vm-lambda/
├── app/                    # メインアプリケーション
│   ├── main.py            # Flask アプリケーションエントリーポイント
│   ├── config.py          # アプリケーション設定
│   ├── api/               # REST API
│   │   └── calculator_api.py
│   ├── models/            # ビジネスロジック
│   │   ├── lambda_calculator.py
│   │   └── vm_calculator.py
│   ├── templates/         # HTMLテンプレート
│   │   ├── base.html
│   │   └── index.html
│   └── static/            # 静的ファイル
│       ├── css/
│       └── js/
├── tests/                 # テストコード
├── Design/                # 設計ドキュメント
├── ref/                   # リファレンスドキュメント
├── Makefile              # 開発コマンド
├── pyproject.toml        # Python プロジェクト設定
└── .mise.toml            # mise 設定
```

## 技術スタック

### バックエンド
- **Python 3.11+**: メイン言語
- **Flask**: Webフレームワーク
- **Flask-CORS**: CORS対応
- **pytest**: テストフレームワーク
- **pytest-cov**: カバレッジ測定

### フロントエンド
- **Bootstrap 5**: UIフレームワーク
- **Chart.js**: グラフ描画
- **Bootstrap Icons**: アイコン

### 開発ツール
- **mise**: 開発環境管理
- **ruff**: リンター・フォーマッター
- **mypy**: 型チェック
- **pre-commit**: Git フック
- **bandit**: セキュリティチェック

## 開発ガイドライン

### コード品質
```bash
# コミット前に必ず実行
make check              # フォーマット + リント + テスト
```

### テスト
- 単体テスト: `tests/unit/`
- 統合テスト: `tests/integration/`
- カバレッジ目標: 90%以上

### コードスタイル
- **ruff**: PEP 8準拠
- **mypy**: 型ヒント必須
- **docstring**: 関数・クラスに必須

### Git ワークフロー
```bash
# 機能ブランチ作成
git checkout -b feature/new-functionality

# 開発・テスト
make dev
make check

# コミット
git add .
git commit -m "feature: add new functionality"

# プッシュ
git push origin feature/new-functionality
```

## API仕様

### エンドポイント
- `POST /api/v1/calculator/lambda` - Lambda コスト計算
- `POST /api/v1/calculator/vm` - VM コスト計算
- `POST /api/v1/calculator/comparison` - コスト比較
- `GET /api/v1/calculator/instances` - 利用可能インスタンス取得

### レスポンス形式
```json
{
  "success": true,
  "data": {
    "comparison_data": [...],
    "break_even_points": [...]
  }
}
```

## デバッグ

### ログ確認
```bash
# Flask ログ
tail -f app.log

# テストログ
pytest -v -s
```

### ブラウザデバッグ
1. F12で開発者ツールを開く
2. Consoleタブでエラー確認
3. Networkタブでapi通信確認

## トラブルシューティング

### mise関連
```bash
# mise インストール確認
mise --version

# Python バージョン確認
mise current python
```

### 依存関係エラー
```bash
# キャッシュクリーンアップ
make clean

# 再インストール
mise run install
```

### テストエラー
```bash
# 詳細ログ付きテスト実行
pytest -v -s --tb=long
```

## デプロイ

### 本番環境準備
```bash
# 本番用依存関係のみインストール
pip install -r requirements.txt

# 環境変数設定
export FLASK_ENV=production
export PORT=5001
```

### Docker（将来実装予定）
```bash
# イメージビルド
docker build -t cost-simulator .

# コンテナ起動
docker run -p 5001:5001 cost-simulator
```

## 参考資料

- **設計仕様**: [Design/Overview.md](Design/Overview.md)
- **リファレンス**: [ref/README.md](ref/README.md)
- **API仕様**: [ref/api-reference.md](ref/api-reference.md)
- **テスト戦略**: [ref/testing-strategy.md](ref/testing-strategy.md)