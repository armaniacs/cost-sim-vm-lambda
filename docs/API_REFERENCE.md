# Cost Simulator - API Reference

## 概要

Cost Simulator REST API v1の詳細仕様書です。32のエンドポイントを提供し、認証、計算、通知、監視機能をサポートします。

## 認証

### JWT認証

すべてのAPIリクエストには、認証が必要です（一部のパブリックエンドポイントを除く）。

```http
Authorization: Bearer <jwt_token>
```

### 認証エンドポイント

#### POST /api/v1/auth/login
ユーザー認証を行い、JWTトークンを取得します。

**リクエスト**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**レスポンス**:
```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "roles": ["viewer"],
    "permissions": ["calculator:read", "pricing:read"]
  },
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

#### POST /api/v1/auth/refresh
リフレッシュトークンを使用して新しいアクセストークンを取得します。

**リクエスト**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 計算API

### POST /api/v1/calculator/compare
Lambda vs VM のコスト比較計算を実行します。

**権限**: `calculator:write`

**リクエスト**:
```json
{
  "execution_frequency": 1000,
  "execution_time": 5.0,
  "memory_mb": 512,
  "storage_gb": 10,
  "data_transfer_gb": 50,
  "region": "us-east-1",
  "currency": "USD",
  "calculation_period": "monthly"
}
```

**レスポンス**:
```json
{
  "success": true,
  "results": {
    "lambda_cost": 125.50,
    "vm_cost": 89.20,
    "breakeven_point": 850,
    "recommendation": "vm",
    "savings": 36.30,
    "savings_percentage": 28.91
  },
  "calculation_id": "calc_123456",
  "timestamp": "2025-01-17T10:30:00Z"
}
```

## 通知API

### GET /api/v1/notifications/health
通知システムのヘルスチェックを実行します。

**権限**: なし（パブリック）

**レスポンス**:
```json
{
  "overall_status": "healthy",
  "timestamp": "2025-01-17T10:30:00Z",
  "checks": {
    "email_config": {
      "status": "healthy",
      "response_time": 0.15
    },
    "webhook_config": {
      "status": "healthy", 
      "response_time": 0.08
    }
  }
}
```

### GET /api/v1/notifications/metrics
通知システムのメトリクスを取得します。

**権限**: `system:read`

**レスポンス**:
```json
{
  "notifications_sent": 145,
  "notifications_failed": 3,
  "email_sent": 89,
  "webhook_sent": 56,
  "average_response_time": 1.25,
  "success_rate": 0.979,
  "error_counts": {
    "email_smtp_timeout": 2,
    "webhook_http_500": 1
  }
}
```

## 監視・メトリクスAPI

### GET /api/v1/performance/metrics
システムパフォーマンスメトリクスを取得します。

**権限**: `system:read`

**レスポンス**:
```json
{
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "disk_usage": 23.1,
  "network_io": {
    "bytes_sent": 1024000,
    "bytes_received": 2048000
  },
  "response_time_ms": 125,
  "active_connections": 15
}
```

### GET /api/v1/performance/database
データベースパフォーマンスメトリクスを取得します。

**権限**: `system:admin`

**レスポンス**:
```json
{
  "connection_count": 12,
  "avg_query_time": 45.3,
  "slow_queries": 2,
  "cache_hit_ratio": 0.89,
  "database_size_mb": 1024,
  "top_queries": [
    {
      "query": "SELECT * FROM calculations WHERE...",
      "avg_time": 125.5,
      "call_count": 89
    }
  ]
}
```

## エラーハンドリング

### エラーレスポンス形式

```json
{
  "success": false,
  "error": "エラーの種類",
  "message": "詳細なエラーメッセージ",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-17T10:30:00Z",
  "request_id": "req_123456"
}
```

### HTTPステータスコード

- `200 OK`: 成功
- `201 Created`: リソース作成成功
- `400 Bad Request`: リクエストエラー
- `401 Unauthorized`: 認証エラー
- `403 Forbidden`: 権限エラー
- `404 Not Found`: リソース未発見
- `429 Too Many Requests`: レート制限
- `500 Internal Server Error`: サーバーエラー

### エラーコード一覧

| コード | 説明 |
|--------|------|
| `AUTH_001` | 認証トークンが無効 |
| `AUTH_002` | 権限が不足 |
| `CALC_001` | 計算パラメータが無効 |
| `CALC_002` | 計算処理でエラー |
| `NOTIF_001` | 通知設定エラー |
| `NOTIF_002` | 通知送信失敗 |
| `SYS_001` | システムリソース不足 |
| `RATE_001` | レート制限に達した |

## レート制限

### 制限値

- **認証済みユーザー**: 1分間に60リクエスト
- **管理者**: 1分間に120リクエスト
- **API専用**: 1分間に300リクエスト

### レート制限ヘッダー

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642428000
```

## SDKとライブラリ

### Python SDK

```python
from cost_simulator_sdk import Client

client = Client(
    base_url="https://api.costsimulator.com",
    api_key="your_api_key"
)

# 計算実行
result = client.calculator.compare({
    "execution_frequency": 1000,
    "execution_time": 5.0,
    "memory_mb": 512
})

print(result.recommendation)
```

### JavaScript SDK

```javascript
import { CostSimulatorClient } from 'cost-simulator-js';

const client = new CostSimulatorClient({
  baseUrl: 'https://api.costsimulator.com',
  apiKey: 'your_api_key'
});

// 計算実行
const result = await client.calculator.compare({
  executionFrequency: 1000,
  executionTime: 5.0,
  memoryMb: 512
});

console.log(result.recommendation);
```

## Webhook

### 価格変更通知

価格に変更があった場合、登録されたWebhookエンドポイントに通知が送信されます。

**ペイロード例**:
```json
{
  "event": "price_change",
  "timestamp": "2025-01-17T10:30:00Z",
  "data": {
    "service": "lambda",
    "region": "us-east-1",
    "old_price": 0.20,
    "new_price": 0.18,
    "change_percent": -10.0
  }
}
```

### Webhook署名検証

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## バージョニング

### APIバージョン管理

- **現在**: v1
- **サポート**: v1のみ
- **非推奨予定**: なし

### バージョン指定

```http
GET /api/v1/calculator/compare
Accept: application/vnd.costsimulator.v1+json
```

## テスト環境

### テストAPI URL

```
https://api-test.costsimulator.com
```

### テストデータ

テスト環境では以下のテストアカウントが利用可能:

```json
{
  "email": "test@costsimulator.com",
  "password": "TestPassword123!",
  "roles": ["admin"]
}
```

---

**API Version**: 1.0.0  
**Last Updated**: 2025-01-17  
**Status**: Production Ready