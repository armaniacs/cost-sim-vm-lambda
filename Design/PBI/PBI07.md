# PBI #7: Docker化実装とMakefile作成

## プロダクトバックログアイテム

**タイトル**: Docker化によるポータブルデプロイメント環境の構築

**ユーザーストーリー**: 
インフラ管理者として、環境依存なしにコスト比較シミュレーターをデプロイしたい、なぜなら複数環境での一貫した動作とメンテナンス性を確保したいから

**ビジネス価値**: 
- 環境構築時間の短縮（手動セットアップ30分→Docker起動3分）
- 環境間の一貫性保証
- 配布・共有の簡易化
- 本番環境デプロイの標準化

**受け入れ基準**:
- [ ] 必要最小限のファイルのみを含むDockerイメージが作成できる
- [ ] `make docker-build`でイメージが正常にビルドされる
- [ ] `make docker-run`でコンテナが起動し、localhost:5000でアクセス可能
- [ ] 全ての機能（計算、グラフ表示、CSV出力）が正常動作する
- [ ] イメージサイズが300MB以下に最適化されている
- [ ] 開発用ファイル（tests/, docs/, .git/等）がイメージに含まれない
- [ ] コンテナの停止・再起動が正常に動作する
- [ ] 環境変数でポート番号を変更可能

**見積もり**: 5ポイント

**備考**: 
- 依存関係: PBI #6（Docker化技術調査）
- 技術的考慮事項: 
  - Python 3.11-slimベースイメージ使用
  - マルチステージビルドでサイズ最適化
  - 非rootユーザーでの実行
  - ヘルスチェック機能の実装

## 実装詳細

### Dockerfile仕様

#### マルチステージビルド構成
```dockerfile
# Stage 1: Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ ./app/
EXPOSE 5000
CMD ["python", "-m", "flask", "--app", "app.main", "run", "--host", "0.0.0.0", "--port", "5000"]
```

#### セキュリティ設定
- **非rootユーザー作成**: `RUN useradd -m -u 1000 appuser`
- **実行権限**: `USER appuser`
- **最小権限**: 必要最小限のパッケージのみインストール

#### ヘルスチェック
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1
```

### .dockerignore 設定

除外するファイル/ディレクトリ:
```
tests/
docs/
Design/
ref/
.git/
.pytest_cache/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.venv/
venv/
.coverage
.nyc_output
.DS_Store
.vscode/
.idea/
*.log
*.tmp
```

### Makefile 追加コマンド

#### Docker関連コマンド
```makefile
# Docker commands
docker-build:
	docker build -t cost-sim-vm-lambda .

docker-run:
	docker run -d -p 5000:5000 --name cost-sim cost-sim-vm-lambda

docker-stop:
	docker stop cost-sim || true
	docker rm cost-sim || true

docker-clean:
	docker-stop
	docker rmi cost-sim-vm-lambda || true

docker-logs:
	docker logs cost-sim

docker-exec:
	docker exec -it cost-sim /bin/bash

# Combined commands
docker-restart: docker-stop docker-run

docker-rebuild: docker-clean docker-build docker-run
```

#### 環境変数対応
```makefile
# Environment variables
PORT ?= 5000
ENV ?= production

docker-run-env:
	docker run -d -p $(PORT):$(PORT) \
		-e PORT=$(PORT) \
		-e FLASK_ENV=$(ENV) \
		--name cost-sim cost-sim-vm-lambda
```

### アプリケーション設定変更

#### 環境変数対応
```python
# app/config.py
import os

class Config:
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
```

#### 起動スクリプト調整
```python
# app/main.py
if __name__ == '__main__':
    from config import Config
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
```

### 動作検証項目

#### 基本動作確認
1. **イメージビルド**: `make docker-build`
2. **コンテナ起動**: `make docker-run`
3. **アクセス確認**: `curl http://localhost:5000`
4. **UI動作確認**: ブラウザでの全機能テスト

#### 性能・サイズ確認
1. **イメージサイズ**: `docker images cost-sim-vm-lambda`
2. **起動時間**: コンテナ起動から応答までの時間
3. **メモリ使用量**: `docker stats cost-sim`

#### セキュリティ確認
1. **ユーザー確認**: `docker exec cost-sim whoami`
2. **ファイル権限**: 不要なファイルが含まれていないか確認
3. **脆弱性スキャン**: `docker scan cost-sim-vm-lambda`

## 成果物
1. **Dockerfile** - 最適化されたマルチステージビルド
2. **.dockerignore** - 除外ファイル設定
3. **Makefile追加** - Docker関連コマンド
4. **設定変更** - 環境変数対応
5. **動作確認書** - 検証結果レポート

## 運用ガイド

### 日常運用コマンド
```bash
# 初回セットアップ
make docker-build
make docker-run

# 日常運用
make docker-restart    # 再起動
make docker-logs       # ログ確認
make docker-stop       # 停止

# 開発・デバッグ
make docker-exec       # コンテナ内アクセス
make docker-rebuild    # 完全再構築
```

### トラブルシューティング
- **起動失敗**: `make docker-logs`でログ確認
- **ポート衝突**: `PORT=8000 make docker-run-env`で別ポート使用
- **権限エラー**: Dockerデーモンの実行権限確認

## 次フェーズへの展開
- **Docker Compose**: 複数コンテナ連携
- **Kubernetes**: オーケストレーション
- **CI/CD**: 自動ビルド・デプロイ
- **監視**: ログ集約・メトリクス収集