# 開発者向けドキュメント

AWS Lambda・Google Cloud Functions vs マルチクラウドVM Cost Simulator の開発環境構築と開発手順

## 🎯 プロジェクト概要

本プロジェクトは、**マルチクラウド・マルチサーバーレス コスト比較シミュレーター** で、エンタープライズグレードの本番環境対応アプリケーションです。

### 🏆 プロジェクト完了ステータス
- ✅ **100% 完了** - 39ストーリーポイント実装済み
- ✅ **88% テストカバレッジ** - 133テストケース (Unit + Integration + E2E)
- ✅ **本番環境対応** - Docker化・セキュリティ基盤・監視システム完備
- ✅ **エンタープライズ機能** - JWT認証・包括的セキュリティ・完全i18n対応

### 🌐 対応プロバイダー

**サーバーレス (2プロバイダー):**
- AWS Lambda (1st generation)
- Google Cloud Functions (1st/2nd generation)

**Virtual Machine (6プロバイダー):**
- AWS EC2 (t3.micro ~ c5.xlarge)
- Google Cloud Compute Engine (e2-micro ~ c2-standard-4)
- Azure Virtual Machines (B1s ~ F2s_v2)
- Oracle Cloud Infrastructure (VM.Standard.E2.1 ~ E2.4)
- Sakura Cloud (1core/1GB ~ 6core/12GB)

### 🚀 主要機能
- **マルチサーバーレス比較**: AWS Lambda vs Google Cloud Functions 直接比較
- **高度なコスト計算**: Egress費用・インターネット転送割合 (0-100%) 設定
- **エンタープライズセキュリティ**: JWT認証・CSRF保護・レート制限・包括的入力検証
- **完全国際化**: 日本語/English UI完全対応 (i18n)
- **高性能可視化**: Chart.js インタラクティブグラフ・リアルタイム更新
- **包括的エクスポート**: 詳細分析データCSV出力

## 🛠 開発環境セットアップ

### 前提条件
- **[mise](https://mise.jdx.dev/)** がインストールされていること
- **Docker** (本番環境シミュレーション用)
- **Git** (バージョン管理)
- **現代的ブラウザ** (Chrome, Firefox, Safari推奨)

### 🚀 クイックスタート (推奨)
```bash
# 完全自動セットアップ
make setup              # 環境構築 + 依存関係 + pre-commit設定
make dev               # 開発サーバー起動 (http://localhost:5001)
```

### 詳細セットアップ手順

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

### 🛠 統合開発コマンドスイート

#### 🚀 日常開発コマンド (高頻度使用)
```bash
# 基本開発サイクル
make dev               # 開発サーバー起動 (localhost:5001) + ホットリロード
make test              # 全テストスイート実行 + 88%カバレッジレポート
make check             # コミット前必須チェック (format + lint + test + security)

# クイックアクセス (短縮形)
make t                 # test (高速テスト実行)
make l                 # lint (コード品質チェック)
make f                 # format (コード自動フォーマット)
```

#### 🧪 テスト実行コマンド (133テストケース)
```bash
# テストカテゴリ別実行
make test-unit         # ユニットテスト (38テスト) - ビジネスロジックテスト
make test-integration  # 結合テスト (32テスト) - APIエンドポイントテスト
make test-e2e          # E2Eテスト (13テスト) - 完全ユーザーワークフロー
make test-security     # セキュリティテスト - CSRF, JWT, 入力検証等

# テスト解析・デバッグ
make test-coverage     # カバレッジレポート生成 (htmlcov/ディレクトリ)
make test-verbose      # 詳細ログ付きテスト実行 (-v -s --tb=long)
make test-watch        # ファイル変更監視自動テスト (TDD開発用)
make test-failed       # 前回失敗テストのみ再実行
```

#### 🚀 Docker開発ワークフロー
```bash
# Docker環境管理
make docker-build      # Multi-stage Dockerイメージビルド (dev + prod)
make docker-run        # 本番環境シミュレーション起動
make docker-dev        # Dockerコンテナ内開発環境
make docker-test       # Docker環境での完全テスト実行

# Dockerメンテナンス
make docker-clean      # 使用していないイメージ・コンテナクリーンアップ
make docker-logs       # コンテナログ表示
make docker-shell      # 稼働中コンテナ内シェルアクセス
make docker-profile    # Dockerコンテナリソース使用量確認
```

#### 🔒 セキュリティ関連コマンド
```bash
# セキュリティ検証
make security-scan     # bandit脆弱性スキャン + セキュリティチェック
make vulnerability-scan # 依存関係脆弱性スキャン (pip-audit)
make validate-env      # 環境変数・シークレット検証
make security-report   # 総合セキュリティレポート生成

# セキュリティ設定
make generate-secrets  # .mise.local.toml用ランダムシークレット生成
make check-secrets     # シークレット漏洩チェック
```

#### 🌍 国際化 (i18n) 関連コマンド
```bash
# 翻訳ファイル管理
make i18n-extract      # JavaScriptコードから翻訳キー抽出
make i18n-update       # 翻訳ファイル同期 (en/ja)
make i18n-validate     # 翻訳キー欠損・重複チェック
make test-i18n         # 翻訳機能テスト (日英切り替え等)

# 翻訳ファイルメンテナンス
make i18n-sort         # 翻訳キーアルファベットソート
make i18n-stats        # 翻訳進捗統計表示
```

#### 📈 パフォーマンス・監視コマンド
```bash
# パフォーマンステスト
make performance-test  # APIレスポンスタイム測定 (<100ms目標)
make load-test         # 高負荷ストレステスト (1000同時リクエスト)
make profile-memory    # メモリプロファイリング (メモリリーク検出)
make profile-cpu       # CPUプロファイリング (ボトルネック特定)

# パフォーマンスレポート
make benchmark         # 総合ベンチマークレポート生成
make performance-report # パフォーマンス分析レポート
```

#### 🛠 環境管理・メンテナンス
```bash
# プロジェクト環境管理
make setup             # 完全初期セットアップ (依存関係+pre-commit+データベース)
make clean             # キャッシュクリーンアップ (__pycache__, .pytest_cache等)
make reset             # プロジェクトリセット (データベース初期化含む)
make status            # プロジェクト状況確認 (テストカバレッジ、コード品質等)

# 依存関係管理
make install           # 依存関係インストール/更新
make update-deps       # 依存関係バージョン更新
make freeze-deps       # requirements.txtバージョン固定
```

#### 📈 品質管理コマンド
```bash
# コード品質チェック
make format            # ruff + isort コード自動フォーマット
make lint              # ruff + mypy コード品質チェック
make type-check        # mypy 型チェックのみ
make complexity-check  # コード複雑度測定 (radon)

# 品質レポート
make quality-report    # 総合コード品質レポート
make metrics           # コードメトリクス測定 (行数、複雑度等)
```

#### 📋 ヘルプ・情報コマンド
```bash
# ヘルプ・ガイダンス
make help              # 全コマンド一覧と説明表示 (40+コマンド)
make info              # プロジェクト基本情報表示
make version           # アプリケーションバージョン情報
make deps-info         # 依存関係バージョン一覧
```

#### 📝 ドキュメント生成コマンド
```bash
# APIドキュメント生成
make docs-api          # OpenAPIスキーマ生成 + Swagger UI
make docs-build        # ドキュメントサイトビルド
make docs-serve        # ドキュメントサーバー起動 (localhost:8000)
```

### 📝 実用的開発ワークフロー例

#### 🚀 初回セットアップ (新規開発者)
```bash
# 1. リポジトリクローン後
cd cost-sim-vm-lambda

# 2. 完全自動セットアップ (推奨)
make setup             # mise環境 + 依存関係 + pre-commit + DB初期化

# 3. セキュリティ設定 (重要)
cp .mise.local.toml.example .mise.local.toml
make generate-secrets  # ランダムシークレット生成

# 4. 動作確認
make test              # 133テスト実行 (88%カバレッジ確認)
make dev               # http://localhost:5001 でアプリケーション起動
```

#### 🔄 日常開発サイクル (TDD)
```bash
# 朝のルーチン
make status            # プロジェクト状況確認
make dev               # 開発サーバー起動 (バックグラウンド)

# TDDサイクル開発
make test-watch        # ファイル変更監視自動テスト (別ターミナル)
# コード編集... -> 自動テスト実行 -> RED/GREEN/REFACTOR

# 定期的チェック
make t                 # クイックテスト実行
make f                 # コードフォーマット
```

#### 📋 コミット前チェック (必須)
```bash
# 完全チェック (pre-commitフックで自動実行)
make check             # format + lint + test + security (約1-2分)

# エラーがある場合の個別チェック
make test-failed       # 失敗テストのみ再実行
make lint              # コード品質問題確認
make security-scan     # セキュリティ問題確認

# 最終コミット
git add .
git commit -m "feat: implement new feature with TDD"
```

#### 🚀 本番環境テストワークフロー
```bash
# Docker本番環境シミュレーション
make docker-build      # Multi-stageビルド (開発/本番用)
make docker-test       # Docker環境で完全テスト
make docker-run        # 本番環境シミュレーション起動

# パフォーマンス検証
make performance-test  # APIレスポンスタイム測定
make load-test         # 高負荷ストレステスト

# リリース前チェック
make security-report   # 総合セキュリティレポート
make quality-report    # コード品質総合レポート
```

#### 🐛 デバッグ・トラブルシューティング
```bash
# テストデバッグ
make test-verbose      # 詳細ログ付きテスト実行
make test-coverage     # カバレッジレポート表示 (htmlcov/index.html)

# コンテナデバッグ
make docker-logs       # コンテナログ確認
make docker-shell      # コンテナ内シェルアクセス

# パフォーマンスデバッグ
make profile-memory    # メモリリーク検出
make profile-cpu       # CPUボトルネック特定
```

#### 🛠 メンテナンス・クリーンアップ
```bash
# 週次メンテナンス
make update-deps       # 依存関係バージョン更新
make vulnerability-scan # 脆弱性スキャン
make clean             # キャッシュクリーンアップ

# トラブル時のリセット
make reset             # プロジェクト全リセット
make docker-clean      # Docker環境クリーンアップ
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

## 🏢 プロジェクト構造 (エンタープライズアーキテクチャ)

```
cost-sim-vm-lambda/
├── app/                           # 📱 Flaskアプリケーションコア
│   ├── main.py                   # アプリケーションエントリーポイント (Application Factory)
│   ├── config.py                 # 環境別アプリケーション設定
│   ├── extensions.py             # Redisクライアント・キャッシュマネージャー
│   ├── api/                      # 🔌 REST APIエンドポイント群
│   │   ├── calculator_api.py        # メインコスト計算API
│   │   ├── auth_api.py              # JWT認証・Auth API
│   │   ├── monitoring_api.py        # ヘルスチェック・監視API
│   │   └── performance_api.py       # パフォーマンスメトリクスAPI
│   ├── auth/                     # 🔐 認証・認可システム (JWT)
│   │   ├── jwt_auth.py              # JWTトークン管理
│   │   ├── models.py                # ユーザーモデル
│   │   └── service.py               # 認証ビジネスロジック
│   ├── models/                   # 📋 ビジネスロジック・データモデル
│   │   ├── lambda_calculator.py     # AWS Lambdaコスト計算
│   │   ├── serverless_calculator.py # マルチサーバーレス計算 (GCP Functions等)
│   │   ├── vm_calculator.py         # マルチクラウドVM計算
│   │   ├── egress_calculator.py     # Egress費用計算エンジン
│   │   └── database.py              # データベース接続・モデル
│   ├── security/                 # 🔒 エンタープライズセキュリティ基盤 (12モジュール)
│   │   ├── csrf_protection.py       # CSRF攻撃保護
│   │   ├── rate_limiter.py          # レート制限システム
│   │   ├── input_validator.py       # 入力検証・サニタイゼーション
│   │   ├── security_headers.py      # セキュリティヘッダー設定
│   │   ├── audit_logger.py          # 監査ログシステム
│   │   ├── env_validator.py         # 環境変数検証
│   │   └── security_monitor.py      # セキュリティ監視システム
│   ├── services/                 # 🔧 アプリケーションサービス層
│   │   ├── cache_service.py         # Redisキャッシュサービス
│   │   ├── logging_service.py       # 統合ログシステム
│   │   ├── monitoring_integration.py # 監視システム統合
│   │   ├── performance_monitor.py   # パフォーマンス監視
│   │   └── observability_service.py # 可観測性サービス
│   ├── static/                   # 🎨 フロントエンドアセット
│   │   ├── css/style.css            # カスタムCSS + Bootstrap拡張
│   │   ├── js/app.js                # メインJavaScriptアプリケーション
│   │   ├── js/i18n.js               # 国際化システム (i18n)
│   │   └── i18n/                   # 🌍 国際化リソース
│   │       ├── en/common.json          # 英語リソース
│   │       └── ja/common.json          # 日本語リソース
│   └── templates/                # 📝 Jinja2テンプレート
│       ├── base.html                # 共通ベーステンプレート
│       ├── index.html               # メインUI (マルチプロバイダー対応)
│       └── dashboard.html           # ダッシュボードUI
│
├── tests/                         # 🧪 総合テストスイート (133テストケース)
│   ├── unit/                     # ユニットテスト (38テスト)
│   ├── integration/              # 結合テスト (32テスト)
│   ├── e2e/                      # E2Eテスト (13テスト) - 完全ワークフロー
│   │   ├── test_egress_feature.py   # Egress機能テスト
│   │   └── test_pbi_sec_*.py        # セキュリティ機能テスト
│   └── conftest.py               # pytest共通設定
│
├── deployment/                    # 🚀 本番環境デプロイ設定
│   ├── docker/                   # Docker構成ファイル
│   ├── nginx/nginx.conf          # nginxリバースプロキシ設定
│   ├── gunicorn/                 # WSGIサーバー設定
│   └── ssl/                      # SSL/TLS証明書管理
│
├── docs/                          # 📄 ユーザー・管理者ドキュメント
│   ├── USER_GUIDE.md             # エンドユーザー向けガイド
│   └── ADMIN_GUIDE.md            # システム管理者ガイド
│
├── Design/                        # 📐 設計ドキュメント
│   ├── PBI/                      # PBI管理 (implemented/not-todo)
│   └── Overview.md               # 完全プロジェクト仕様
│
├── ref/                           # 📋 リファレンスドキュメント
│   ├── security-architecture.md  # エンタープライズセキュリティ設計
│   ├── deployment-production-guide.md # 本番デプロイガイド
│   └── monitoring-observability.md # 監視・可観測性ガイド
│
└── プロジェクト設定ファイル           # ⚙️ 環境・ビルド設定
    ├── Dockerfile                # Multi-stage本番対応ビルド
    ├── docker-compose.yml        # 開発環境コンテナ構成
    ├── Makefile                  # 統合開発コマンド
    ├── pyproject.toml            # Pythonプロジェクト設定
    ├── .mise.toml                # mise環境管理
    └── .mise.local.toml.example  # セキュリティ設定テンプレート
```

### 🏆 アーキテクチャハイライト
- **Application Factoryパターン**: スケーラブルなFlaskアプリケーション
- **サービス層アーキテクチャ**: ビジネスロジックとインフラの分離
- **セキュリティミドルウェアスタック**: 包括的セキュリティ層
- **国際化アーキテクチャ**: 日英完全対応のi18nシステム

## 🚀 技術スタック (エンタープライズグレード)

### 💻 バックエンド コア
**メインフレームワーク:**
- **Python 3.11+**: メイン言語 (型ヒント完全対応)
- **Flask 2.3+**: Webフレームワーク (Application Factoryパターン)
- **Flask-CORS**: クロスオリジンリソース共有設定
- **Jinja2**: サーバーサイドテンプレートエンジン

**認証・セキュリティ:**
- **PyJWT**: JWTトークン認証システム
- **Flask-Limiter**: レート制限システム
- **Werkzeug**: セキュリティユーティリティ (入力検証等)
- **bandit**: セキュリティ脆弱性静的解析

**データベース・キャッシュ:**
- **SQLite3**: 開発環境データベース
- **PostgreSQL**: 本番環境データベース (サポート済)
- **Redis**: メモリキャッシュシステム
- **psutil**: システムリソース監視

**監視・パフォーマンス:**
- **カスタム監視システム**: パフォーマンスメトリクス収集
- **ログ統合システム**: 構造化ログ出力
- **可観測性サービス**: APM統合準備

### 🎨 フロントエンド
**UIフレームワーク:**
- **Bootstrap 5**: レスポンシブCSSフレームワーク
- **Bootstrap Icons**: アイコンセット
- **カスタムCSS**: ブランドテーマ・コンポーネント拡張

**JavaScript (フレームワーク非依存):**
- **Vanilla ES6+**: フレームワークに依存しない純粋JavaScript
- **Chart.js 3.9+**: インタラクティブグラフライブラリ
- **Fetch API**: モダンなHTTPクライアント

**国際化 (i18n):**
- **カスタムi18nシステム**: 日本語/English完全対応
- **JSONリソースファイル**: 動的言語切り替え
- **ユーザー設定永続化**: localStorageベース

### 📊 テストフレームワーク (88%カバレッジ)
**テスト実行:**
- **pytest**: メインテストフレームワーク
- **pytest-cov**: カバレッジ測定・レポート
- **pytest-mock**: モック・フィクスチャ機能

**テスト手法:**
- **Outside-In TDD**: 外側からのテスト駆動開発
- **BDD (Behavior-Driven Development)**: 振る舞い駆動開発
- **133テストケース**: Unit(38) + Integration(32) + E2E(13)

### 🚀 コンテナ・デプロイメント
**コンテナ技術:**
- **Docker**: Multi-stage builds 対応コンテナ化
- **Docker Compose**: 開発環境オーケストレーション
- **Alpine Linux**: 軽量ベースイメージ

**本番環境サーバー:**
- **nginx**: リバースプロキシ + 静的ファイル配信
- **Gunicorn**: WSGIアプリケーションサーバー
- **SSL/TLS**: 完全なHTTPS対応

### 🛠 開発ツールスイート
**環境管理:**
- **mise**: Pythonバージョン + 依存関係管理
- **pyproject.toml**: モダンPythonプロジェクト設定
- **pip-tools**: 依存関係バージョン固定

**コード品質ツール:**
- **ruff**: 高速Pythonリンター + フォーマッター
- **mypy**: 静的型チェッカー (型ヒント必須)
- **isort**: import文自動ソート
- **black**: コードフォーマッター (バックアップ)

**Git統合:**
- **pre-commit**: Gitフック自動品質チェック
- **commitizen**: コミットメッセージ標準化

**ビルドシステム:**
- **Makefile**: 統合開発コマンド (40+ターゲット)
- **GitHub Actions**: CI/CDパイプライン (準備済)

### 🔍 監視・デバッグ
**パフォーマンス監視:**
- **カスタムメトリクス**: APIレスポンスタイム等
- **リソース監視**: CPU・Memory使用量トラッキング
- **ヘルスチェック**: アプリケーション正常性監視

**ログシステム:**
- **構造化ログ**: JSON形式ログ出力
- **ログレベル分類**: DEBUG/INFO/WARNING/ERROR
- **監査ログ**: セキュリティイベント記録

## 📋 高度な開発ガイドライン

### 🧪 Outside-In TDD + BDD 手法

**テスト駆動開発フロー:**
```bash
# 1. E2Eテストから開始 (外側から)
make test-e2e           # 結果: RED (失敗)

# 2. 結合テストでAPIインターフェース設計
make test-integration   # 結果: RED (失敗)

# 3. ユニットテストで詳細ロジック実装
make test-unit          # 結果: GREEN (成功)

# 4. リファクタリングでコード品質向上
make format && make lint

# 5. 全テストで統合確認
make test               # 88%カバレッジ目標
```

**BDDシナリオ書き方:**
```python
# tests/e2e/test_user_story.py
def test_user_can_compare_lambda_vs_vm_costs():
    """Given: ユーザーがLambda設定を入力したとき
    When: コスト比較を実行すると
    Then: ブレークイーブンポイントが表示される"""
    # Given
    lambda_config = {...}
    
    # When
    response = client.post('/api/v1/calculator/comparison', json=lambda_config)
    
    # Then
    assert response.status_code == 200
    assert 'break_even_points' in response.json['data']
```

### 🔒 セキュリティファースト開発

**セキュリティ考慮事項:**
```bash
# セキュリティチェック実行
make security-scan      # bandit + 脆弱性スキャン

# セキュリティテスト実行
make test-security      # CSRF, JWT, 入力検証テスト

# 環境変数検証
make validate-env       # .mise.local.tomlセキュリティ検証
```

**セキュアコーディングプラクティス:**
- **入力サニタイズ**: 全APIエンドポイントで必須
- **JWTトークンローテーション**: 認証管理の基本
- **CSRF保護**: フォーム送信時の必須検証
- **レート制限**: API乱用防止
- **セキュリティヘッダー**: 本番環境で必須設定

### 🌍 国際化 (i18n) 開発

**翻訳ファイル管理:**
```bash
# 翻訳キー抽出
make i18n-extract       # JavaScriptコードから翻訳キー抽出

# 翻訳ファイル更新
make i18n-update        # en/ja翻訳ファイル同期

# 翻訳テスト
make test-i18n          # 翻訳欠損・表示テスト
```

**新しい翻訳追加手順:**
1. `app/static/js/i18n.js` でキー定義
2. `app/static/i18n/en/common.json` に英語翻訳追加
3. `app/static/i18n/ja/common.json` に日本語翻訳追加
4. `make test-i18n` で翻訳正常性確認

### 📈 パフォーマンス最適化

**パフォーマンス監視:**
```bash
# パフォーマンステスト実行
make performance-test   # APIレスポンスタイム測定

# ロードテスト実行
make load-test         # 高負荷時の動作確認

# メモリプロファイリング
make profile-memory    # メモリリーク検出
```

**最適化ガイドライン:**
- **Chart.jsレンダリング**: 大量データポイント最適化
- **Redisキャッシュ**: 計算結果キャッシュ戦略
- **データベースクエリ**: N+1問題回避
- **静的ファイル**: nginxキャッシュ最適化

### 🛠 Docker基盤開発ワークフロー

**Docker開発サイクル:**
```bash
# Docker環境での開発
make docker-dev         # コンテナ内開発環境起動

# コンテナ内テスト
make docker-test        # 本番環境シミュレーション

# イメージビルド
make docker-build       # Multi-stage本番用ビルド

# コンテナプロファイリング
make docker-profile     # コンテナリソース使用量確認
```

**コンテナ最適化:**
- **Multi-stage builds**: 開発/本番用イメージ分離
- **.dockerignore**: 不要ファイル除外で軽量化
- **Alpine Linux**: セキュリティ更新対応
- **ヘルスチェック**: コンテナ正常性監視

### 📋 コード品質管理

**コミット前チェック:**
```bash
# 全品質チェック (コミット前必須)
make check              # format + lint + test + security

# 項目別チェック
make format             # ruff + isortコードフォーマット
make lint               # ruff + mypyコード品質チェック
make type-check         # mypy型チェックのみ
```

**コードスタイル準拠:**
- **PEP 8**: Python標準コーディングスタイル
- **型ヒント必須**: 全関数・メソッドで必須
- **Docstring必須**: 公開API・クラスで必須
- **コメント品質**: なぜ(理由)を重視、何を(内容)はコードで表現

### 🔄 Gitワークフロー (エンタープライズ)

**機能開発フロー:**
```bash
# 1. フィーチャーブランチ作成
git checkout -b feature/PBI-XX-new-functionality

# 2. TDDサイクル開発
make test-e2e           # 失敗するテストを作成
# 実装...
make test               # テスト通過確認

# 3. 品質チェック
make check              # 全チェッククリア

# 4. コミット (自動フック実行)
git add .
git commit -m "feat: implement PBI-XX new functionality"

# 5. プッシュ・プルリクエスト
git push origin feature/PBI-XX-new-functionality
gh pr create --title "feat: PBI-XX implementation"
```

**コミットメッセージ標準:**
- `feat:` - 新機能追加
- `fix:` - バグ修正
- `docs:` - ドキュメント更新
- `test:` - テスト追加/修正
- `refactor:` - リファクタリング
- `security:` - セキュリティ対応

## 🔌 REST API仕様 (包括的エンドポイント)

### 📊 コスト計算 API (`app/api/calculator_api.py`)

**メインコスト計算:**
- `POST /api/v1/calculator/lambda` - AWS Lambdaコスト計算
- `POST /api/v1/calculator/serverless` - マルチサーバーレス計算 (AWS Lambda + GCP Functions)
- `POST /api/v1/calculator/vm` - マルチクラウドVM計算 (6プロバイダー)
- `POST /api/v1/calculator/comparison` - 総合コスト比較 (サーバーレス vs VM)
- `POST /api/v1/calculator/egress` - Egress費用計算 (全プロバイダー対応)

**メタデータ API:**
- `GET /api/v1/calculator/instances` - 利用可能インスタンス一覧取得
- `GET /api/v1/calculator/providers` - 対応プロバイダー一覧取得
- `GET /api/v1/calculator/regions` - 対応リージョン一覧取得

### 🔐 認証・Auth API (`app/api/auth_api.py`)

**JWT認証システム:**
- `POST /api/v1/auth/login` - ユーザーログイン (JWTトークン発行)
- `POST /api/v1/auth/logout` - ユーザーログアウト (トークン無効化)
- `POST /api/v1/auth/refresh` - JWTトークンリフレッシュ
- `GET /api/v1/auth/profile` - ユーザープロファイル取得
- `POST /api/v1/auth/register` - 新規ユーザー登録

**セキュリティ関連:**
- `GET /api/v1/auth/csrf-token` - CSRFトークン取得
- `POST /api/v1/auth/validate-token` - JWTトークン検証

### 📈 監視・ヘルスチェック API (`app/api/monitoring_api.py`)

**アプリケーションステータス:**
- `GET /api/v1/monitoring/health` - アプリケーションヘルスチェック
- `GET /api/v1/monitoring/ready` - レディネスプローブ (サービス依存関係確認)
- `GET /api/v1/monitoring/status` - システム全体ステータス
- `GET /api/v1/monitoring/version` - アプリケーションバージョン情報

**システムメトリクス:**
- `GET /api/v1/monitoring/metrics` - システムメトリクス (CPU/Memory/Disk)
- `GET /api/v1/monitoring/database` - データベース接続ステータス
- `GET /api/v1/monitoring/cache` - Redisキャッシュステータス

### 🚀 パフォーマンス API (`app/api/performance_api.py`)

**パフォーマンス監視:**
- `GET /api/v1/performance/metrics` - APIパフォーマンスメトリクス
- `GET /api/v1/performance/response-times` - レスポンスタイム統計
- `GET /api/v1/performance/throughput` - スループット統計
- `POST /api/v1/performance/benchmark` - パフォーマンスベンチマーク実行

**リソース使用量:**
- `GET /api/v1/performance/memory` - メモリ使用量統計
- `GET /api/v1/performance/cpu` - CPU使用量統計
- `GET /api/v1/performance/disk` - ディスク使用量統計

### 📊 レスポンス形式標準

**成功レスポンス:**
```json
{
  "success": true,
  "data": {
    "comparison_data": [
      {
        "executions_per_month": 1000000,
        "lambda_cost_usd": 8.33,
        "vm_costs": {
          "aws_ec2_t3_micro": 8.76,
          "gcp_e2_micro": 7.11,
          "azure_b1s": 7.59,
          "oci_vm_standard_e2_1": 6.13,
          "sakura_1core_1gb": 8.80
        },
        "egress_costs": {
          "aws_lambda": 1.20,
          "aws_ec2": 1.80,
          "gcp_functions": 1.00
        }
      }
    ],
    "break_even_points": {
      "aws_ec2_t3_micro": {
        "executions_per_month": 1052632,
        "executions_per_second": 0.41
      }
    },
    "metadata": {
      "calculation_time_ms": 45,
      "cache_hit": false,
      "exchange_rate": 150.0
    }
  },
  "timestamp": "2025-07-25T10:30:00Z",
  "version": "v1.0.0"
}
```

**エラーレスポンス:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "無効な入力パラメーターが含まれています",
    "details": {
      "memory_mb": ["値は128-2048の範囲で入力してください"]
    }
  },
  "timestamp": "2025-07-25T10:30:00Z",
  "request_id": "req_abc123"
}
```

### 🔒 認証・認可

**JWTトークン使用:**
```bash
# ログインしてJWTトークン取得
curl -X POST /api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# JWTトークンで認証がAPIアクセス
curl -X POST /api/v1/calculator/comparison \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**CSRF保護:**
```bash
# CSRFトークン取得
curl -X GET /api/v1/auth/csrf-token

# CSRFトークン付きフォーム送信
curl -X POST /api/v1/calculator/comparison \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### 📊 パフォーマンス特性

**APIレスポンスタイム:**
- **計算API**: <100ms (キャッシュ時: <10ms)
- **メタデータAPI**: <50ms
- **監視API**: <30ms
- **認証API**: <200ms (JWT署名・検証含む)

**レート制限:**
- **計算API**: 60リクエスト/分
- **認証API**: 10リクエスト/分
- **監視API**: 120リクエスト/分

**キャッシュ戦略:**
- **計算結果**: 5分間Redisキャッシュ
- **メタデータ**: 1時間キャッシュ
- **パフォーマンスメトリクス**: 30秒キャッシュ

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

## 🛠 包括的トラブルシューティング

### 🔧 開発環境問題

#### mise環境エラー
```bash
# mise基本診断
mise doctor                # システム診断実行
mise --version            # バージョン確認
mise current              # 現在の環境確認

# Python環境修復
mise uninstall python 3.11
mise install python 3.11
mise use python@3.11

# 完全環境リセット
rm -rf .mise/             # mise設定削除
make setup                # 環境再構築
```

#### 依存関係問題
```bash
# 段階的依存関係修復
make clean                # キャッシュクリーンアップ
rm -rf .venv/             # 仮想環境削除
mise run install          # 依存関係再インストール
pip install --upgrade pip # pip更新

# 特定パッケージ問題
pip install --force-reinstall package-name
pip check                 # 依存関係整合性確認
```

### 🧪 テスト関連問題

#### テスト実行エラー
```bash
# 詳細デバッグテスト
make test-verbose         # 最大詳細レベル
pytest -v -s --tb=long --pdb  # デバッガー付き実行

# 特定テスト分離実行
pytest tests/unit/test_specific.py::test_function -v
pytest -k "test_lambda_calculation" -v

# テストカバレッジ詳細
make test-coverage
open htmlcov/index.html   # ブラウザでカバレッジ確認
```

#### テストデータベース問題
```bash
# テスト用DB初期化
rm -f test_cost_simulator.db
make test-db-init

# テストでのDB状態確認
echo "SELECT name FROM sqlite_master WHERE type='table';" | sqlite3 test_cost_simulator.db
```

### 🐳 Docker問題

#### Docker環境エラー
```bash
# Docker診断
docker system info        # Docker状態確認
docker system df          # ディスク使用量確認

# コンテナ問題診断
make docker-logs          # コンテナログ確認
make docker-shell         # コンテナ内部調査
docker inspect cost-simulator  # コンテナ詳細情報

# Docker環境リセット
make docker-clean         # 未使用イメージ・コンテナ削除
docker system prune -a    # 完全クリーンアップ
```

#### イメージビルド問題
```bash
# ビルド詳細ログ
docker build --no-cache --progress=plain -t cost-simulator .

# マルチステージビルド個別確認
docker build --target development -t cost-sim:dev .
docker build --target production -t cost-sim:prod .

# ビルドコンテキスト確認
echo "FROM alpine" | docker build --no-cache -f- .  # コンテキストサイズ確認
```

### 🔗 API・ネットワーク問題

#### API接続エラー
```bash
# ローカルAPI診断
curl -v http://localhost:5001/api/v1/monitoring/health
curl -v -H "Content-Type: application/json" \
  -d '{"memory_mb": 128, "execution_time_seconds": 1}' \
  http://localhost:5001/api/v1/calculator/lambda

# ネットワーク診断
netstat -tlnp | grep :5001   # ポート使用状況
lsof -i :5001                # プロセス確認
```

#### CORS・認証問題
```bash
# CORS設定確認
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS http://localhost:5001/api/v1/calculator/lambda

# JWT認証テスト
# 1. ログインしてトークン取得
TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' | jq -r '.data.token')

# 2. トークンでAPI呼び出し
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5001/api/v1/calculator/instances
```

### 🗄 データベース問題

#### SQLite開発環境
```bash
# DB接続確認
sqlite3 cost_simulator_dev.db ".tables"  # テーブル一覧
sqlite3 cost_simulator_dev.db ".schema"  # スキーマ確認

# DB整合性チェック
sqlite3 cost_simulator_dev.db "PRAGMA integrity_check;"

# DB再作成
rm -f cost_simulator_dev.db
make db-init
```

#### PostgreSQL本番環境
```bash
# PostgreSQL接続テスト
psql $DATABASE_URL -c "SELECT version();"

# 接続数確認
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# テーブル状態確認
psql $DATABASE_URL -c "\dt"  # テーブル一覧
psql $DATABASE_URL -c "SELECT schemaname,tablename,n_tup_ins,n_tup_upd,n_tup_del FROM pg_stat_user_tables;"
```

### 🔄 Redis・キャッシュ問題

#### Redis接続問題
```bash
# Redis接続テスト
redis-cli ping            # 基本接続確認
redis-cli info server     # サーバー情報
redis-cli monitor         # リアルタイム監視

# キャッシュ状態確認
redis-cli keys "cost:*"   # アプリケーションキー一覧
redis-cli flushdb         # 開発用DB削除（注意）

# Redis設定確認
redis-cli config get "*"  # 全設定表示
```

### 🔐 セキュリティ・認証問題

#### JWT認証デバッグ
```bash
# JWT トークン内容確認（デバッグ用）
echo "$JWT_TOKEN" | cut -d. -f2 | base64 -d | jq

# 認証フロー確認
curl -v -X POST /api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"debug","password":"debug"}'

# CSRF トークン確認
curl -v -X GET /api/v1/auth/csrf-token
```

#### セキュリティスキャン問題
```bash
# bandit詳細スキャン
bandit -r app/ -f json -o security-report.json

# 脆弱性スキャン
pip-audit --format=json --output=vulnerability-report.json

# 環境変数セキュリティチェック
grep -r "password\|secret\|key" app/ --exclude-dir=__pycache__
```

### 🌐 フロントエンド・UI問題

#### Chart.js描画問題
```javascript
// ブラウザ開発者ツール（F12）でデバッグ

// Chart.js状態確認
console.log(Chart.instances);
console.log(window.costChart);

// APIレスポンス確認
fetch('/api/v1/calculator/comparison', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({...})
}).then(r => r.json()).then(data => console.log(data));

// i18n状態確認
console.log(window.i18n.currentLanguage);
console.log(window.i18n.translations);
```

#### CSS・レイアウト問題
```bash
# 静的ファイル確認
ls -la app/static/css/
ls -la app/static/js/

# ブラウザキャッシュクリア確認
# Chrome: Ctrl+Shift+R (ハードリロード)
# Firefox: Ctrl+F5
# Safari: Cmd+Option+R
```

### 📊 パフォーマンス問題

#### 応答時間診断
```bash
# API応答時間測定
time curl http://localhost:5001/api/v1/calculator/lambda \
  -H "Content-Type: application/json" \
  -d '{"memory_mb": 128, "execution_time_seconds": 1}'

# 詳細パフォーマンス測定
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5001/

# curl-format.txt内容:
#      time_namelookup:  %{time_namelookup}\n
#         time_connect:  %{time_connect}\n
#      time_appconnect:  %{time_appconnect}\n
#     time_pretransfer:  %{time_pretransfer}\n
#        time_redirect:  %{time_redirect}\n
#   time_starttransfer:  %{time_starttransfer}\n
#                     ----------\n
#           time_total:  %{time_total}\n
```

#### メモリ・CPU使用量
```bash
# プロセス監視
top -p $(pgrep -f "gunicorn.*app.main")
htop  # より詳細な監視

# メモリプロファイリング
make profile-memory

# システムリソース確認
free -h                   # メモリ使用量
df -h                     # ディスク使用量
iostat 1 5                # I/O統計
```

### 🔥 緊急時対応

#### サービス復旧手順
```bash
# 1. サービス状態確認
sudo systemctl status nginx
sudo supervisorctl status

# 2. ログ確認
tail -f /var/log/cost-simulator/error.log
tail -f /var/log/nginx/error.log

# 3. サービス再起動
sudo supervisorctl restart cost-simulator
sudo systemctl restart nginx

# 4. ヘルスチェック
./scripts/health-check.sh

# 5. 監視ダッシュボード確認
curl http://localhost:5001/api/v1/monitoring/metrics
```

#### データ復旧
```bash
# データベースバックアップから復旧
psql $DATABASE_URL < backup/cost_simulator_$(date +%Y%m%d).sql

# Redis データ復旧
redis-cli --rdb backup/dump.rdb

# アプリケーション設定復旧
cp backup/.env.production .env
```

### 📞 サポート・エスカレーション

**問題解決手順:**
1. 該当セクションのトラブルシューティング実行
2. ログ・エラーメッセージ収集
3. 再現手順記録
4. GitHub Issueでサポート依頼
5. 緊急時は開発チームに直接連絡

**ログ収集コマンド:**
```bash
# 統合ログ収集
make collect-logs         # 全ログを logs/debug-$(date).tar.gz に集約

# システム情報収集
make system-info          # 環境情報をsystem-info.txt に出力
```

## 🚀 本番環境デプロイ (完全対応済み)

### 🐳 Docker本番デプロイ (推奨)

**Multi-stage Docker Build:**
```bash
# 本番用最適化イメージビルド
make docker-build         # development + production ステージ対応

# 本番環境起動
make docker-run           # nginx + gunicorn + Redis 統合環境

# ヘルスチェック確認
curl http://localhost:5001/api/v1/monitoring/health
```

**カスタムDockerビルド:**
```bash
# 開発用イメージ (フル開発ツール付き)
docker build --target development -t cost-simulator:dev .

# 本番用イメージ (軽量・セキュア)
docker build --target production -t cost-simulator:prod .

# 本番コンテナ起動 (環境変数付き)
docker run -d \
  --name cost-simulator-prod \
  -p 80:80 \
  -p 443:443 \
  -e FLASK_ENV=production \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  -e JWT_SECRET_KEY=${JWT_SECRET_KEY} \
  -v /path/to/ssl:/etc/ssl/certs \
  cost-simulator:prod
```

### ⚙️ 従来型デプロイ (VPS/サーバー)

**必要な環境準備:**
```bash
# システム要件
sudo apt update && sudo apt install -y \
  python3.11 python3.11-venv \
  nginx \
  postgresql \
  redis-server \
  supervisor

# アプリケーション配置
git clone https://github.com/your-org/cost-sim-vm-lambda.git
cd cost-sim-vm-lambda

# 本番環境セットアップ
make setup-production     # 本番用依存関係インストール
```

**環境変数設定 (.env.production):**
```bash
# アプリケーション設定
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5001
WORKERS=4

# データベース設定
DATABASE_URL=postgresql://user:pass@localhost:5432/cost_simulator
REDIS_URL=redis://localhost:6379/0

# セキュリティ設定
JWT_SECRET_KEY=your-super-secret-jwt-key
CSRF_SECRET_KEY=your-csrf-secret-key
SECRET_KEY=your-flask-secret-key

# SSL/TLS設定
SSL_CERT_PATH=/etc/ssl/certs/your-domain.crt
SSL_KEY_PATH=/etc/ssl/private/your-domain.key

# 監視・ログ設定
LOG_LEVEL=INFO
MONITORING_ENABLED=True
PERFORMANCE_MONITORING=True
```

### 🌐 nginx リバースプロキシ設定

**nginx設定ファイル (/etc/nginx/sites-available/cost-simulator):**
```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL設定
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # 静的ファイル配信
    location /static {
        alias /opt/cost-simulator/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # アプリケーションプロキシ
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API レート制限
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:5001;
        # ... 他のproxy設定
    }
}

# レート制限ゾーン定義
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
}
```

### 🔧 Gunicorn WSGI設定

**gunicorn設定ファイル (deployment/gunicorn/gunicorn.conf.py):**
```python
# Gunicorn本番設定
bind = "127.0.0.1:5001"
workers = 4  # CPU コア数 * 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
keepalive = 2

# ログ設定
accesslog = "/var/log/cost-simulator/access.log"
errorlog = "/var/log/cost-simulator/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# プロセス管理
user = "www-data"
group = "www-data"
tmp_upload_dir = None
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}
```

### 📊 Supervisor プロセス管理

**supervisor設定 (/etc/supervisor/conf.d/cost-simulator.conf):**
```ini
[program:cost-simulator]
command=/opt/cost-simulator/.venv/bin/gunicorn -c deployment/gunicorn/gunicorn.conf.py app.main:app
directory=/opt/cost-simulator
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/cost-simulator/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=FLASK_ENV="production",DATABASE_URL="postgresql://..."

[program:cost-simulator-worker]
command=/opt/cost-simulator/.venv/bin/python -m app.tasks.worker
directory=/opt/cost-simulator
user=www-data
numprocs=2
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/cost-simulator/worker.log
```

### 🔍 本番環境監視設定

**ヘルスチェックスクリプト:**
```bash
#!/bin/bash
# /opt/cost-simulator/scripts/health-check.sh

# アプリケーションヘルスチェック
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/v1/monitoring/health)
if [ $response -eq 200 ]; then
    echo "✅ Application: Healthy"
else
    echo "❌ Application: Unhealthy (HTTP $response)"
    exit 1
fi

# データベース接続チェック
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/v1/monitoring/database)
if [ $response -eq 200 ]; then
    echo "✅ Database: Connected"
else
    echo "❌ Database: Connection failed"
    exit 1
fi

# Redis接続チェック
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/v1/monitoring/cache)
if [ $response -eq 200 ]; then
    echo "✅ Redis: Connected"
else
    echo "❌ Redis: Connection failed"
    exit 1
fi

echo "🎉 All systems operational"
```

### 🔐 本番セキュリティ設定

**SSL/TLS証明書設定:**
```bash
# Let's Encrypt証明書取得
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 証明書自動更新設定
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

**ファイアウォール設定:**
```bash
# UFW基本設定
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# アプリケーションポート保護
sudo ufw deny 5001  # Gunicornへの直接アクセス禁止
```

### 📈 パフォーマンス最適化

**Redis設定最適化 (/etc/redis/redis.conf):**
```conf
# メモリ最適化
maxmemory 256mb
maxmemory-policy allkeys-lru

# パフォーマンス設定
tcp-keepalive 300
timeout 0
tcp-backlog 511

# セキュリティ設定
bind 127.0.0.1
protected-mode yes
requirepass your-redis-password
```

**PostgreSQL最適化:**
```sql
-- /etc/postgresql/14/main/postgresql.conf 最適化例
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### 🔄 本番環境デプロイスクリプト

**自動デプロイスクリプト (deploy.sh):**
```bash
#!/bin/bash
# deployment/scripts/deploy.sh

set -e

echo "🚀 Starting production deployment..."

# 1. コード更新
git pull origin main

# 2. 依存関係更新
make install

# 3. データベースマイグレーション
make db-migrate

# 4. 静的ファイル収集
make collect-static

# 5. アプリケーション再起動
sudo supervisorctl restart cost-simulator
sudo supervisorctl restart cost-simulator-worker

# 6. nginx設定リロード
sudo nginx -s reload

# 7. ヘルスチェック
sleep 5
./scripts/health-check.sh

echo "✅ Deployment completed successfully!"
```

### 🎯 本番環境チェックリスト

**デプロイ前確認:**
- [ ] 全テスト通過 (`make test`)
- [ ] セキュリティスキャン完了 (`make security-scan`)
- [ ] パフォーマンステスト完了 (`make performance-test`)
- [ ] 環境変数設定完了
- [ ] SSL証明書有効
- [ ] データベースバックアップ完了

**デプロイ後確認:**
- [ ] アプリケーションヘルスチェック通過
- [ ] 全APIエンドポイント正常応答
- [ ] 監視システム正常動作
- [ ] ログ出力正常
- [ ] パフォーマンスメトリクス正常値

## 📁 包括的参考資料・ドキュメント

### 📘 コアドキュメント (必読)

**プロジェクト基礎:**
- **[プロジェクト概要](ref/project-overview.md)** - プロジェクトの目標・現状・成果物
- **[完全設計仕様](Design/Overview.md)** - 総合プロジェクト仕様書 (日本語)
- **[アーキテクチャ概要](ref/architecture-overview.md)** - システム設計・パターン・技術決定

**技術詳細:**
- **[技術仕様](ref/technical-specifications.md)** - コスト計算アルゴリズム・価格データ
- **[価格データリファレンス](ref/pricing-data-reference.md)** - 全プロバイダー価格情報
- **[APIエンドポイントリファレンス](ref/api-endpoints-reference.md)** - 全REST API仕様・サンプル

### 🛠 開発・頖状管理

**開発手法:**
- **[開発ガイド](ref/development-guide.md)** - TDDワークフロー・setup手順
- **[実装ガイド](ref/implementation-guide.md)** - ryuzeeメソドロジー・Outside-In TDD
- **[実装詳細](ref/implementation-details.md)** - 技術実装の詳細説明

**テスト戦略:**
- **[テストフレームワークガイド](ref/testing-framework-guide.md)** - Outside-In TDD + BDD手法
- **[テスト戦略](ref/testing-strategy.md)** - カバレッジ要件・実行戦略

**進捗管理:**
- **[PBI管理](Design/PBI/)** - プロダクトバックログ管理 (implemented/not-todo)
- **[機能実装状況](ref/feature-implementation-status.md)** - 100%完成状況詳細

### 🔒 セキュリティ・運用

**セキュリティ:**
- **[セキュリティアーキテクチャ](ref/security-architecture.md)** - エンタープライズグレードセキュリティ設計
- **[PBI-SEC-A セキュリティ実装レポート](Design/security-implementation-report.md)** - JWT認証・セキュリティ基盤

**運用・デプロイ:**
- **[本番デプロイガイド](ref/deployment-production-guide.md)** - 本番環境構築戦略
- **[監視・可観測性](ref/monitoring-observability.md)** - 総合監視システムガイド

### 🎨 UI・UX・フロントエンド

**フロントエンドアーキテクチャ:**
- **[UI要件](ref/ui-requirements.md)** - インターフェース仕様・UX要件
- **[フロントエンドアーキテクチャ](ref/frontend-architecture.md)** - JavaScript・CSS・テンプレート構造
- **[UIモックアップ](Design/cost-input-and-result.png)** - 初期コンセプトデザイン

### 📄 ユーザー・管理者向け

**エンドユーザー向け:**
- **[ユーザーガイド](docs/USER_GUIDE.md)** - 完全な使用方法・機能説明
- **[ユーザーガイド (日本語完全版)](docs/ja/USER_GUIDE.md)** - i18n対応日本語ガイド (必要時)

**システム管理者向け:**
- **[管理者ガイド](docs/ADMIN_GUIDE.md)** - システム管理・デプロイガイド
- **[APIリファレンス](docs/API_REFERENCE.md)** - 管理者向けAPIドキュメント

### 📈 パフォーマンス・品質

**コード品質・メトリクス:**
- **[コードカバレッジレポート](htmlcov/index.html)** - 88%カバレッジ詳細 (ローカル生成)
- **[セキュリティスキャンレポート](security-reports/)** - 定期スキャン結果
- **[パフォーマンスベンチマーク](performance-reports/)** - API応答時間等

### 🔗 クイックリンク・ショートカット

**新規開発者向け (組み合わせ推奨):**
1. **[プロジェクト概要](ref/project-overview.md)** - まずここから開始
2. **[開発ガイド](ref/development-guide.md)** - TDD環境セットアップ
3. **[アーキテクチャ概要](ref/architecture-overview.md)** - システム理解
4. **[APIリファレンス](ref/api-endpoints-reference.md)** - API仕様理解

**既存開発者向け (日常使用):**
- **[実装状況](ref/feature-implementation-status.md)** - 現在の進捗確認
- **[テスト戦略](ref/testing-strategy.md)** - テスト手法理解
- **[セキュリティアーキテクチャ](ref/security-architecture.md)** - セキュリティ実装確認

**管理者・運用担当者向け:**
- **[本番デプロイガイド](ref/deployment-production-guide.md)** - デプロイ戦略
- **[監視・可観測性](ref/monitoring-observability.md)** - 監視システム
- **[管理者ガイド](docs/ADMIN_GUIDE.md)** - 運用ガイド

### 📅 プロジェクト情報

**最終更新**: 2025-07-25  
**プロジェクトステータス**: ✅ 100%完成 - メンテナンスフェーズ  
**ライセンス**: Apache License 2.0  
**開発手法**: Outside-In TDD + ryuzeeメソドロジー  
**メンテナ**: 開発チーム

---

🎉 **おめでとうございます!** このプロジェクトは完全に実装され、本番環境での運用準備が整いました。新しい開発者の方は **[プロジェクト概要](ref/project-overview.md)** から始めてください。