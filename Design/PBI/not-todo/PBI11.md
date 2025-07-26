# PBI11: リアルタイム料金取得機能

## 概要
外部APIからクラウドプロバイダーの最新料金情報を自動取得し、計算に反映する機能を実装する。

## 背景・課題
- **現在の課題**: 各プロバイダーの料金がハードコードされており、価格変動に対応できない
- **ビジネス価値**: 常に最新の料金で正確なコスト比較が可能になる
- **ユーザー影響**: より信頼性の高いコスト算出結果を提供

## 機能要件

### 主要機能
1. **外部API統合**
   - Azure Retail Prices API統合
   - AWS Pricing API統合
   - Google Cloud Billing API統合
   - 為替レートAPI統合 (USD/JPY)

2. **料金管理機能**
   - 定期的な料金更新（日次）
   - 料金履歴の保存
   - 料金変動の検出とアラート
   - インテリジェントキャッシュ機能

3. **UI/UX改善**
   - 料金の最終更新時刻表示
   - 手動更新ボタン
   - 接続状態表示
   - 料金変動の可視化

## 技術要件

### アーキテクチャ設計
```
app/
├── services/
│   ├── pricing_service.py      # 外部API統合サービス
│   ├── azure_pricing_service.py # Azure Retail Prices API
│   ├── aws_pricing_service.py  # AWS Pricing API
│   └── gcp_pricing_service.py  # Google Cloud Billing API
├── models/
│   ├── pricing_data.py         # 料金データモデル
│   └── pricing_history.py      # 料金履歴モデル
├── tasks/
│   └── pricing_update.py       # 定期更新タスク
├── cache/
│   └── pricing_cache.py        # Redis/メモリキャッシュ
└── config/
    └── pricing_config.py       # API設定
```

### 外部API仕様
1. **Azure Retail Prices API**
   - エンドポイント: `https://prices.azure.com/api/retail/prices`
   - 認証: 不要
   - レート制限: 比較的緩い
   - 対象: B2ms, D3, D4インスタンス

2. **AWS Pricing API**
   - エンドポイント: AWS Price List API
   - 認証: AWS認証が必要
   - レート制限: 1000リクエスト/日
   - 対象: Lambda, EC2インスタンス

3. **Google Cloud Billing API**
   - エンドポイント: Cloud Billing API
   - 認証: サービスアカウント必要
   - レート制限: 1000リクエスト/日
   - 対象: Compute Engineインスタンス

4. **為替レートAPI**
   - エンドポイント: `https://api.exchangerate-api.com/v4/latest/USD`
   - 認証: 不要 (無料枠: 1500リクエスト/月)
   - レート制限: 1500リクエスト/月

## 実装計画

### Phase 1: 基盤実装 (Sprint 1)
**目標**: Azure API + 為替レート API + 基本キャッシュ

#### 実装内容
1. **料金データモデル**
   ```python
   @dataclass
   class PricingData:
       provider: str
       instance_type: str
       region: str
       hourly_cost_usd: float
       last_updated: datetime
       source: str  # "api" or "hardcoded"
   ```

2. **Azure Pricing Service**
   ```python
   class AzurePricingService:
       def fetch_vm_pricing(self, region: str) -> List[PricingData]:
           # Azure Retail Prices API統合
       
       def update_pricing_cache(self) -> None:
           # キャッシュ更新
   ```

3. **基本キャッシュ機能**
   - メモリキャッシュ実装
   - 24時間TTL
   - フォールバック機能

#### 受け入れ基準
- [ ] Azure VMの料金をAPIから取得できる
- [ ] 為替レートを自動取得できる
- [ ] API障害時はハードコード値を使用する
- [ ] 料金データがキャッシュされる

### Phase 2: 拡張実装 (Sprint 2)
**目標**: AWS API + Google Cloud API + 料金履歴

#### 実装内容
1. **AWS Pricing Service**
   ```python
   class AWSPricingService:
       def fetch_lambda_pricing(self, region: str) -> PricingData:
           # AWS Pricing API統合
       
       def fetch_ec2_pricing(self, region: str) -> List[PricingData]:
           # EC2料金取得
   ```

2. **Google Cloud Pricing Service**
   ```python
   class GCPPricingService:
       def fetch_compute_pricing(self, region: str) -> List[PricingData]:
           # Google Cloud Billing API統合
   ```

3. **料金履歴機能**
   ```python
   class PricingHistory:
       def save_pricing_snapshot(self, pricing_data: List[PricingData]) -> None:
           # 料金履歴保存
       
       def detect_price_changes(self) -> List[PriceChange]:
           # 料金変動検出
   ```

#### 受け入れ基準
- [ ] AWS Lambda/EC2の料金をAPIから取得できる
- [ ] Google Cloud Compute Engineの料金をAPIから取得できる
- [ ] 料金履歴が保存される
- [ ] 料金変動が検出される

### Phase 3: UI/UX改善 (Sprint 3)
**目標**: 料金更新状況の可視化

#### 実装内容
1. **料金状況表示**
   ```html
   <div class="pricing-status">
       <span class="last-updated">最終更新: 2025-07-14 10:30</span>
       <button class="btn-update">手動更新</button>
       <div class="connection-status">
           <span class="status-badge status-connected">接続OK</span>
       </div>
   </div>
   ```

2. **料金変動可視化**
   - 料金変動グラフ
   - 変動アラート
   - 履歴表示機能

#### 受け入れ基準
- [ ] 料金の最終更新時刻が表示される
- [ ] 手動更新ボタンが機能する
- [ ] 接続状態が表示される
- [ ] 料金変動が可視化される

## BDD受け入れ基準

### シナリオ1: 外部APIから料金取得
```gherkin
Given コスト比較シミュレーターが起動している
When 外部API統合が有効になっている
And Azure Retail Prices APIから最新料金を取得する
Then 計算結果にAPI料金が反映される
And 料金の最終更新時刻が表示される
```

### シナリオ2: API障害時のフォールバック
```gherkin
Given 外部APIが利用できない状態
When コスト計算を実行する
Then ハードコード料金が使用される
And 「料金データが古い可能性があります」の警告が表示される
```

### シナリオ3: 料金変動の検出
```gherkin
Given 前回の料金データが保存されている
When 外部APIから新しい料金を取得する
And 料金に変動がある場合
Then 料金変動アラートが表示される
And 変動内容が履歴に記録される
```

### シナリオ4: キャッシュ機能の動作
```gherkin
Given 料金データがキャッシュされている
When キャッシュが有効期限内の場合
Then APIを呼び出さずにキャッシュデータを使用する
And 高速に計算結果を返す
```

### シナリオ5: 為替レート自動更新
```gherkin
Given USD/JPY為替レートが変動している
When 為替レートAPIから最新レートを取得する
Then JPY表示の料金が自動更新される
And 更新時刻が表示される
```

## エラー処理

### API障害への対応
1. **段階的フォールバック**
   ```python
   def get_pricing_data(provider: str, instance_type: str) -> PricingData:
       try:
           # 1. APIから取得を試行
           return api_service.fetch_pricing(provider, instance_type)
       except APIException:
           # 2. キャッシュから取得を試行
           cached_data = cache.get_pricing(provider, instance_type)
           if cached_data and not cache.is_expired(cached_data):
               return cached_data
           # 3. ハードコード値を使用
           return hardcoded_pricing.get(provider, instance_type)
   ```

2. **ユーザー通知**
   - API接続状態の表示
   - 料金データの鮮度表示
   - 警告メッセージの表示

### レート制限対応
1. **指数バックオフ**
   - 429エラー時の自動リトライ
   - 指数的な待機時間増加

2. **クォータ管理**
   - 日次API呼び出し数の管理
   - 制限近接時の警告

## テスト戦略

### 単体テスト
- [ ] 各外部API serviceの単体テスト
- [ ] キャッシュ機能のテスト
- [ ] エラー処理のテスト
- [ ] 料金データモデルのテスト

### 統合テスト
- [ ] 外部API統合のテスト（モック使用）
- [ ] フォールバック機能のテスト
- [ ] 料金変動検出のテスト

### E2Eテスト
- [ ] 料金取得から計算までの一連のテスト
- [ ] UI表示の確認テスト
- [ ] API障害時のユーザー体験テスト

## 設定管理

### 環境変数
```bash
# AWS API設定
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-northeast-1

# Google Cloud API設定
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCP_PROJECT_ID=your_project_id

# 為替レートAPI設定
EXCHANGE_RATE_API_KEY=your_api_key

# キャッシュ設定
REDIS_URL=redis://localhost:6379
CACHE_TTL_HOURS=24

# 更新設定
PRICING_UPDATE_INTERVAL_HOURS=24
```

## 成功指標

### 機能指標
- [ ] 外部API統合成功率 > 99%
- [ ] 料金データ更新頻度: 日次
- [ ] API応答時間 < 5秒
- [ ] キャッシュヒット率 > 90%

### 品質指標
- [ ] テストカバレッジ > 85%
- [ ] エラー処理の網羅性 100%
- [ ] ユーザビリティテスト合格

## 完了定義 (DoD)

### 技術的完了条件
- [ ] 全ての外部API統合が実装されている
- [ ] キャッシュ機能が正常に動作する
- [ ] エラー処理が網羅的に実装されている
- [ ] 定期更新タスクが動作する

### 品質保証
- [ ] 全てのテストが合格する
- [ ] コードレビューが完了している
- [ ] セキュリティチェックが完了している
- [ ] パフォーマンステストが合格する

### ユーザー体験
- [ ] 料金更新状況が分かりやすく表示される
- [ ] API障害時も正常に動作する
- [ ] 料金変動が適切に通知される
- [ ] 手動更新機能が正常に動作する

---

**PBI11 見積もり**: 8ストーリーポイント (3 Sprint)  
**依存関係**: なし  
**優先度**: 高  
**実装開始日**: 2025-07-14