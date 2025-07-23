# PBI #13: Google Cloud Functions/Cloud Run プロバイダー追加

**タイトル**: Google Cloud Functions/Cloud Run プロバイダー追加

**ユーザーストーリー**: 
DevOpsエンジニアとして、Google Cloud Functions と Cloud Run のコストを AWS Lambda と比較したい、なぜなら Google Cloud のサーバーレス環境での最適なデプロイ戦略を選択し、コンテナベースと関数ベースの実行モデルを比較検討したいから

**ビジネス価値**: 
- **マルチクラウド対応強化**: Google Cloud 採用企業への対応拡大（日本のGCP採用率約20%）
- **技術的差別化**: Functions（関数ベース）と Cloud Run（コンテナベース）の実行モデル比較
- **包括的サーバーレス比較**: AWS Lambda vs Google Cloud の詳細分析支援

## BDD受け入れシナリオ

```gherkin
Scenario: Google Cloud Functions のコスト計算と比較
  Given ユーザーがコスト比較ツールを開いている
  And Lambda パラメータとして "メモリ:512MB、実行時間:10秒、月間実行回数:100万回" を入力している
  When "Google Cloud Functions" のチェックボックスをオンにする
  And リージョンとして "asia-northeast1 (Tokyo)" を選択する
  And "Calculate" ボタンをクリックする
  Then グラフに Google Cloud Functions のコストラインが表示される
  And AWS Lambda、EC2、他のプロバイダーと並んで比較可能である
  And break-even point が正しく計算される
  And 無料枠（200万リクエスト/月）が考慮される

Scenario: Google Cloud Run のコスト計算
  Given ユーザーが Google Cloud サーバーレス比較を選択している
  When "Cloud Run" を選択する
  And CPU 1vCPU、メモリ 1GB を設定する
  And 実行時間 10秒、月間実行回数 100万回を入力する
  Then Cloud Run のコスト（リクエスト課金 + CPU時間課金 + メモリ課金）が計算される
  And Functions との違いがグラフ上で可視化される
  And コンテナベース実行の特徴が表示される

Scenario: Functions vs Cloud Run の比較
  Given Google Cloud の Functions と Cloud Run 両方が選択されている
  When 同一ワークロード条件で計算する
  Then 2つのサービスのコスト差が明確に表示される
  And 実行モデルの違い（関数 vs コンテナ）が説明される
  And 適用場面の推奨事項が表示される

Scenario: 通貨換算と CSV 出力
  Given 為替レートが "150円/USD" に設定されている
  When Google Cloud Functions のコストを計算する
  Then コストが USD から正しく円換算される
  And CSV 出力に Google Cloud のデータが含まれる
  And Functions と Cloud Run が別列として出力される

Scenario: 無料枠の正確な計算
  Given 月間実行回数が 150万回に設定されている
  When Google Cloud Functions を計算する
  Then 無料枠 200万リクエスト/月が適用される
  And 課金対象が 0回 と表示される
  And 無料枠超過時の課金も正確に計算される
```

## 受け入れ基準

### 機能要件
- [ ] Google Cloud Functions の料金計算実装（リクエスト + GB-s 課金）
- [ ] Google Cloud Run の料金計算実装（リクエスト + CPU時間 + メモリ課金）
- [ ] サービス選択UI（Functions vs Cloud Run）の実装
- [ ] 東京リージョン（asia-northeast1）の価格でコスト計算
- [ ] 無料枠の正確な適用（200万リクエスト/月）
- [ ] 既存プロバイダーとの統合グラフ表示
- [ ] break-even point 計算への統合
- [ ] CSV出力への Google Cloud データ追加
- [ ] 為替レート変換（USD→JPY）の対応

### 品質要件
- [ ] テストカバレッジ 88% 以上の維持
- [ ] レスポンス時間 500ms 以下
- [ ] モバイルレスポンシブ対応
- [ ] 日英両言語対応（i18n）

## t_wadaスタイル テスト戦略

### E2Eテスト
- Google Cloud Functions 選択→計算→グラフ表示の一連フロー
- Functions vs Cloud Run 同時比較シナリオ
- 無料枠適用の境界値テスト（200万リクエスト前後）
- CSV出力の完全性確認

### 統合テスト  
- /serverless APIエンドポイントでの Google Cloud リクエスト処理
- /comparison API での複数プロバイダー比較
- 料金計算の正確性（Functions: リクエスト+GB-s、Cloud Run: リクエスト+CPU+メモリ）
- 無料枠計算ロジック

### 単体テスト
- get_gcp_functions_cost() メソッドの料金計算ロジック
- get_gcp_cloudrun_cost() メソッドの料金計算ロジック
- 無料枠適用ロジック（200万リクエスト/月）
- 通貨変換の正確性
- 境界値：最小リクエスト数、最大リクエスト数
- 例外：無効なサービス種別、負の値

## 実装アプローチ

- **Outside-In**: E2Eテストで「Google Cloud 選択→グラフ表示」から開始
- **Red-Green-Refactor**: 
  1. Red: E2Eテスト失敗（UI に Google Cloud 要素なし）
  2. Green: UI→API→計算エンジンの順で実装
  3. Refactor: サーバーレスプロバイダー抽象化
- **段階的実装**: Functions → Cloud Run → 比較機能の順

## 見積もり

**8ストーリーポイント**
- 2サービス（Functions + Cloud Run）の複雑な料金体系
- コンテナ vs 関数の実行モデル差の表現
- 無料枠計算の複雑性
- 既存システムとの統合作業

## 技術的考慮事項

### Google Cloud 料金体系（2025年1月時点、asia-northeast1）

#### Google Cloud Functions（第2世代）
- **リクエスト課金**: $0.0000004/リクエスト
- **実行時間課金**: $0.0000025/GB-秒
- **無料枠**: 200万リクエスト/月 + 400,000 GB-秒/月

#### Google Cloud Run
- **リクエスト課金**: $0.0000024/リクエスト  
- **CPU課金**: $0.00001800/vCPU-秒
- **メモリ課金**: $0.000002/GB-秒
- **無料枠**: 200万リクエスト/月 + 180,000 vCPU-秒/月 + 360,000 GB-秒/月

### UI実装パターン

```html
<!-- Google Cloud サーバーレスサービス選択 -->
<div class="form-check">
  <input class="form-check-input" type="checkbox" id="compareGCPServerless">
  <label class="form-check-label" for="compareGCPServerless">
    Compare with Google Cloud Serverless
  </label>
</div>

<!-- サービス選択 -->
<div class="mt-2" id="gcpServerlessOptions" style="display: none;">
  <div class="form-check">
    <input class="form-check-input" type="radio" name="gcpService" id="gcpFunctions" value="functions">
    <label class="form-check-label" for="gcpFunctions">
      Cloud Functions (Function-as-a-Service)
    </label>
  </div>
  <div class="form-check">
    <input class="form-check-input" type="radio" name="gcpService" id="gcpCloudRun" value="cloudrun">
    <label class="form-check-label" for="gcpCloudRun">
      Cloud Run (Container-as-a-Service)
    </label>
  </div>
</div>

<!-- Cloud Run 設定 -->
<div class="mt-2" id="cloudRunConfig" style="display: none;">
  <select class="form-select" id="cloudRunCPU">
    <option value="1">1 vCPU</option>
    <option value="2">2 vCPU</option>
    <option value="4">4 vCPU</option>
  </select>
  <select class="form-select mt-1" id="cloudRunMemory">
    <option value="1">1 GB Memory</option>
    <option value="2">2 GB Memory</option>
    <option value="4">4 GB Memory</option>
    <option value="8">8 GB Memory</option>
  </select>
</div>
```

### API仕様

```json
{
  "provider": "google_cloud",
  "service_type": "functions", // "functions" or "cloudrun"
  "memory_mb": 512,
  "cpu_count": 1, // Cloud Run のみ
  "execution_time_seconds": 10,
  "monthly_executions": 1000000,
  "include_free_tier": true,
  "exchange_rate": 150
}
```

### グラフ表示設定

- **Functions**: 色 #4285F4（Google Blue）、実線
- **Cloud Run**: 色 #0F9D58（Google Green）、破線
- **凡例**: "GCP Functions" / "GCP Cloud Run"

## Definition of Done

- [ ] BDD受け入れシナリオが全て通る
- [ ] テストカバレッジ88%以上を維持
- [ ] コードレビュー完了（料金計算の正確性重点確認）
- [ ] リファクタリング完了（サーバーレスプロバイダー抽象化）
- [ ] ドキュメント更新（README、API仕様）
- [ ] i18n対応完了（日英両言語）
- [ ] lintエラー0、型チェック通過
- [ ] パフォーマンステスト通過（レスポンス時間500ms以下）

## 実装詳細補足

### 差別化要素
1. **実行モデル比較**: 関数ベース vs コンテナベースの可視化
2. **柔軟なリソース設定**: Cloud Run の CPU/メモリ組み合わせ
3. **無料枠の複雑性**: 複数リソース（リクエスト+CPU+メモリ）の無料枠適用

### 技術的挑戦
1. **料金計算の複雑さ**: 3つの課金軸（リクエスト+CPU+メモリ）の正確な計算
2. **UI/UX**: 2つのサーバーレスサービスの違いの分かりやすい表現
3. **パフォーマンス**: 計算複雑度向上に対する応答速度維持