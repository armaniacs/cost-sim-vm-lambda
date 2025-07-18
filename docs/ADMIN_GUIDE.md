# 管理者ガイド - AWS Lambda vs VM コスト比較シミュレーター

## 概要

本ドキュメントは、AWS Lambda vs VM コスト比較シミュレーターの管理者向けガイドです。システムの導入、運用、保守、セキュリティ管理について説明します。

## システム要件

### ハードウェア要件

#### 最小構成
- **CPU**: 2コア以上
- **メモリ**: 4GB RAM以上
- **ストレージ**: 10GB以上の空き容量
- **ネットワーク**: インターネット接続

#### 推奨構成
- **CPU**: 4コア以上
- **メモリ**: 8GB RAM以上
- **ストレージ**: 50GB以上（ログ・バックアップ含む）
- **ネットワーク**: 高速インターネット接続

### ソフトウェア要件

#### 必須ソフトウェア
- **OS**: Linux (Ubuntu 20.04 LTS/22.04 LTS推奨), macOS, Windows
- **Python**: 3.11.8以上
- **Node.js**: 20.11.0以上（開発時のみ）
- **Docker**: 20.10以上（コンテナ運用時）
- **Git**: バージョン管理

#### オプション
- **Nginx**: リバースプロキシ（本番環境推奨）
- **Redis**: キャッシュ・セッション管理
- **PostgreSQL**: 本格的なデータベース（将来の拡張時）

## インストールと初期設定

### 1. 前提条件の確認

```bash
# Python バージョン確認
python3 --version  # 3.11.8以上

# Node.js バージョン確認（開発時のみ）
node --version     # 20.11.0以上

# Docker バージョン確認（コンテナ運用時）
docker --version   # 20.10以上
```

### 2. ソースコードの取得

```bash
# リポジトリのクローン
git clone <repository-url>
cd cost-sim-vm-lambda

# 権限設定
chmod +x scripts/*.sh
```

### 3. 環境構築

#### mise を使用した環境構築（推奨）

```bash
# mise のインストール（未インストールの場合）
curl https://mise.run | sh

# 依存関係インストール
make setup

# または手動で
mise install
mise run install
```

#### 手動環境構築

```bash
# Python仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 開発ツールインストール
pip install -r requirements-dev.txt
```

### 4. 設定ファイルの作成

#### 環境変数設定

```bash
# .env ファイル作成
cp .env.example .env

# 設定編集
vim .env
```

#### 基本設定項目

```bash
# Flask設定
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<strong-random-key>

# データベース設定
DATABASE_URL=sqlite:///cost_simulator.db

# セキュリティ設定
JWT_SECRET_KEY=<jwt-secret-key>
CORS_ORIGINS=https://yourdomain.com

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=/var/log/cost-simulator/app.log

# メトリクス・モニタリング
PROMETHEUS_ENABLED=True
METRICS_PORT=9090
```

### 5. データベース初期化

```bash
# データベース作成・マイグレーション
make db-init

# または手動で
python -m flask db init
python -m flask db migrate
python -m flask db upgrade
```

## 本番環境デプロイ

### 1. Docker を使用したデプロイ（推奨）

#### Docker Compose を使用

```bash
# 本番用設定
cp docker-compose.prod.yml docker-compose.yml

# 環境変数設定
vim .env.prod

# デプロイ実行
make docker-deploy

# または手動で
docker-compose -f docker-compose.prod.yml up -d
```

#### 個別 Docker コンテナ

```bash
# イメージビルド
make docker-build

# コンテナ起動
make docker-run-prod

# ログ確認
docker logs cost-simulator
```

### 2. システムサービスとして設定

#### systemd サービス設定

```bash
# サービスファイル作成
sudo cp deployment/cost-simulator.service /etc/systemd/system/

# サービス設定編集
sudo vim /etc/systemd/system/cost-simulator.service

# サービス有効化・起動
sudo systemctl enable cost-simulator
sudo systemctl start cost-simulator
sudo systemctl status cost-simulator
```

#### Nginx リバースプロキシ設定

```bash
# Nginx設定ファイル
sudo cp deployment/nginx.conf /etc/nginx/sites-available/cost-simulator
sudo ln -s /etc/nginx/sites-available/cost-simulator /etc/nginx/sites-enabled/

# SSL証明書設定（Let's Encrypt推奨）
sudo certbot --nginx -d yourdomain.com

# Nginx再起動
sudo systemctl restart nginx
```

### 3. 設定の検証

```bash
# アプリケーション動作確認
curl http://localhost:5001/health

# ヘルスチェック確認
curl http://localhost:5001/api/health

# メトリクス確認（有効な場合）
curl http://localhost:9090/metrics
```

## 運用・保守

### 1. 日常運用コマンド

#### サービス状態確認

```bash
# システム状態確認
make status

# ログ確認
make logs

# リソース使用量確認
make monitor
```

#### サービス制御

```bash
# サービス開始
make start

# サービス停止
make stop

# サービス再起動
make restart

# 設定リロード
make reload
```

### 2. ログ管理

#### ログファイルの場所

```
/var/log/cost-simulator/
├── app.log              # アプリケーションログ
├── error.log            # エラーログ
├── access.log           # アクセスログ
├── security.log         # セキュリティログ
└── audit.log           # 監査ログ
```

#### ログローテーション設定

```bash
# logrotate設定
sudo cp deployment/logrotate.conf /etc/logrotate.d/cost-simulator

# 手動ローテーション実行
sudo logrotate -f /etc/logrotate.d/cost-simulator
```

#### ログレベル設定

```bash
# 環境変数での設定
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# 実行時変更
curl -X POST http://localhost:5001/admin/log-level -d '{\"level\": \"DEBUG\"}'
```

### 3. データベース管理

#### バックアップ

```bash
# 自動バックアップ設定
make backup-setup

# 手動バックアップ実行
make backup

# バックアップファイル確認
ls -la backups/
```

#### データベースメンテナンス

```bash
# データベース最適化
make db-optimize

# 統計情報更新
make db-analyze

# 古いデータクリーンアップ
make db-cleanup
```

### 4. アップデート・メンテナンス

#### アプリケーションアップデート

```bash
# 新バージョン取得
git pull origin main

# 依存関係更新
make update-deps

# データベースマイグレーション
make db-migrate

# アプリケーション再起動
make restart
```

#### ゼロダウンタイム・アップデート

```bash
# Blue-Green デプロイメント
make deploy-blue-green

# ローリングアップデート（Kubernetes等）
kubectl rolling-update cost-simulator
```

## セキュリティ管理

### 1. セキュリティ設定

#### SSL/TLS設定

```bash
# SSL証明書の自動更新設定
sudo crontab -e
# 0 12 * * * /usr/bin/certbot renew --quiet

# SSL設定の確認
openssl s_client -connect yourdomain.com:443
```

#### ファイアウォール設定

```bash
# ufw設定例
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw deny 5001/tcp     # アプリケーション（直接アクセス拒否）
sudo ufw enable
```

#### セキュリティヘッダー設定

Nginx設定ファイルに以下を追加：

```nginx
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

### 2. 認証・認可管理

#### JWT設定

```bash
# JWT秘密鍵の定期更新
openssl rand -base64 64 > /etc/cost-simulator/jwt-secret

# 設定ファイル更新
sed -i 's/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=new-secret/' .env
```

#### API認証設定

```bash
# API キーの生成
python -c "import secrets; print(secrets.token_urlsafe(32))"

# API キーの設定
echo "API_KEYS=key1,key2,key3" >> .env
```

### 3. セキュリティ監査

#### セキュリティログの確認

```bash
# 失敗したログイン試行
grep "Failed login" /var/log/cost-simulator/security.log

# 異常なアクセスパターン
grep "Rate limit exceeded" /var/log/cost-simulator/security.log

# SQL インジェクション試行
grep "SQL injection" /var/log/cost-simulator/security.log
```

#### 脆弱性スキャン

```bash
# 依存関係の脆弱性チェック
make security-scan

# または手動で
pip-audit
bandit -r app/
```

## モニタリング・アラート

### 1. システムモニタリング

#### Prometheus + Grafana設定

```bash
# Prometheus設定
cp monitoring/prometheus.yml /etc/prometheus/

# Grafana ダッシュボード
# monitoring/grafana-dashboard.json をインポート
```

#### ヘルスチェック設定

```bash
# アプリケーションヘルスチェック
curl http://localhost:5001/health

# データベースヘルスチェック
curl http://localhost:5001/health/database

# 外部依存サービスヘルスチェック
curl http://localhost:5001/health/external
```

### 2. アラート設定

#### 基本的なアラート条件

```yaml
# alertmanager.yml例
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://slack-webhook-url'
```

#### 監視対象メトリクス

- **レスポンス時間**: 95パーセンタイル > 2秒
- **エラー率**: 5分間平均 > 5%
- **CPU使用率**: > 80%
- **メモリ使用率**: > 85%
- **ディスク使用量**: > 90%
- **データベース接続**: 失敗率 > 1%

### 3. パフォーマンス最適化

#### アプリケーション最適化

```bash
# プロファイリング実行
make profile

# ボトルネック特定
make performance-test

# キャッシュ設定最適化
make cache-optimize
```

#### データベース最適化

```bash
# スロークエリ分析
make analyze-slow-queries

# インデックス最適化
make optimize-indexes

# 統計情報更新
make update-statistics
```

## トラブルシューティング

### 1. 一般的な問題と解決策

#### アプリケーションが起動しない

```bash
# ログ確認
tail -f /var/log/cost-simulator/app.log

# 設定確認
make check-config

# 依存関係確認
make check-deps

# ポート使用状況確認
netstat -tlnp | grep 5001
```

#### データベース接続エラー

```bash
# データベース状態確認
make db-status

# 接続テスト
make db-test-connection

# データベース修復
make db-repair
```

#### 高負荷時の問題

```bash
# プロセス状況確認
top -p $(pgrep -d, python)

# メモリ使用量詳細
smem -k -c pss

# ネットワーク状況
netstat -i
ss -tuln
```

### 2. エラーコード一覧

| エラーコード | 説明 | 対処法 |
|------------|------|--------|
| 500 | 内部サーバーエラー | ログ確認、アプリケーション再起動 |
| 503 | サービス利用不可 | データベース接続確認 |
| 429 | レート制限 | レート制限設定確認 |
| 401 | 認証エラー | JWT設定確認 |
| 404 | リソース未発見 | ルーティング設定確認 |

### 3. 緊急時対応

#### サービス停止手順

```bash
# 緊急停止
make emergency-stop

# メンテナンスページ表示
make maintenance-mode

# ユーザー通知
make notify-users
```

#### バックアップからの復旧

```bash
# データベース復旧
make restore-database BACKUP_FILE=backup-20250118.sql

# アプリケーション復旧
make restore-application

# 設定ファイル復旧
make restore-config
```

## 設定リファレンス

### 1. 環境変数一覧

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `FLASK_ENV` | `development` | 環境設定 |
| `FLASK_DEBUG` | `False` | デバッグモード |
| `SECRET_KEY` | - | セッション暗号化キー |
| `DATABASE_URL` | `sqlite:///app.db` | データベースURL |
| `JWT_SECRET_KEY` | - | JWT暗号化キー |
| `LOG_LEVEL` | `INFO` | ログレベル |
| `REDIS_URL` | - | Redis接続URL |
| `PROMETHEUS_ENABLED` | `False` | Prometheusメトリクス |

### 2. 設定ファイル場所

```
/etc/cost-simulator/
├── app.conf              # アプリケーション設定
├── database.conf         # データベース設定
├── security.conf         # セキュリティ設定
├── monitoring.conf       # モニタリング設定
└── ssl/                  # SSL証明書
    ├── cert.pem
    └── private.key
```

## 付録

### A. 有用なコマンド集

```bash
# システム情報収集
make system-info

# 診断レポート生成
make diagnostic-report

# パフォーマンステスト
make load-test

# セキュリティチェック
make security-check

# バックアップ検証
make verify-backup
```

### B. 連絡先・サポート

- **技術サポート**: admin@yourdomain.com
- **緊急連絡**: +81-XX-XXXX-XXXX
- **ドキュメント**: https://docs.yourdomain.com
- **コミュニティ**: https://community.yourdomain.com

### C. 変更履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|----------|
| 1.0.0 | 2025-01-18 | 初回リリース |

---

**最終更新**: 2025年1月18日  
**ドキュメントバージョン**: 1.0  
**対応アプリケーションバージョン**: 1.0.0