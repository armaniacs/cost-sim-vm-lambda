# PBI #14: Azure Functions プロバイダー追加

**タイトル**: Azure Functions プロバイダー追加

**ユーザーストーリー**: 
エンタープライズアーキテクトとして、Azure Functions のコストを AWS Lambda と比較したい、なぜなら Microsoft 365 環境を利用している組織で Azure エコシステム内でのサーバーレス戦略を評価したいから

**ビジネス価値**: 
- **エンタープライズ対応**: Azure 採用企業（日本の大企業採用率約25%）への対応強化
- **エコシステム統合**: Microsoft 365/Teams 連携での Total Cost of Ownership 分析
- **ハイブリッドクラウド**: オンプレミス Active Directory との統合シナリオ対応

## BDD受け入れシナリオ

```gherkin
Scenario: Azure Functions Consumption Plan のコスト計算
  Given ユーザーがコスト比較ツールを開いている
  And Lambda パラメータとして "メモリ:512MB、実行時間:5秒、月間実行回数:50万回" を入力している
  When "Azure Functions" のチェックボックスをオンにする
  And プランとして "Consumption Plan" を選択する
  And リージョンとして "Japan East" を選択する
  And "Calculate" ボタンをクリックする
  Then グラフに Azure Functions のコストラインが表示される
  And AWS Lambda、他のプロバイダーと並んで比較可能である
  And break-even point が正しく計算される
  And 無料枠（100万実行/月 + 400,000 GB-秒/月）が考慮される

Scenario: Azure Functions の無料枠境界値テスト
  Given Azure Functions が選択されている
  When 月間実行回数を 120万回に設定する
  And メモリを 512MB、実行時間を 3秒に設定する
  Then 無料枠超過分（20万実行）のみが課金対象として表示される
  And GB-秒無料枠（400,000 GB-秒）も正確に適用される
  And 超過分コストが詳細表示される

Scenario: Premium Plan との比較（将来拡張）
  Given Azure Functions が選択されている
  When プラン種別で "Premium Plan" が選択可能である
  Then Consumption Plan との違いが説明される
  And 高負荷時の推奨事項が表示される

Scenario: Microsoft エコシステム統合コスト
  Given Azure Functions でコスト計算が完了している
  When "Show ecosystem integration" オプションを選択する
  Then Logic Apps、Service Bus との連携コストが表示される
  And Microsoft 365 ライセンス割引が考慮される

Scenario: CSV出力での Azure データ詳細
  Given Azure Functions を含む比較結果が表示されている
  When "Export CSV" ボタンをクリックする
  Then Azure Functions のデータが詳細に含まれる
  And 実行課金と GB-秒課金が分離記録される
  And 無料枠適用状況も記録される
```

## 受け入れ基準

### 機能要件
- [ ] Azure Functions Consumption Plan の料金計算実装
- [ ] 実行課金（$0.20/million executions）の実装
- [ ] GB-秒課金（$0.000016/GB-秒）の実装
- [ ] 無料枠の正確な適用（100万実行/月 + 400,000 GB-秒/月）
- [ ] Japan East リージョンの価格でコスト計算
- [ ] 既存プロバイダーとの統合グラフ表示
- [ ] break-even point 計算への統合
- [ ] CSV出力への Azure データ追加
- [ ] 為替レート変換（USD→JPY）の対応

### 品質要件
- [ ] テストカバレッジ 88% 以上の維持
- [ ] レスポンス時間 500ms 以下
- [ ] モバイルレスポンシブ対応
- [ ] 日英両言語対応（i18n）
- [ ] エラーハンドリング（無効入力、API障害）

## t_wadaスタイル テスト戦略

### E2Eテスト
- Azure Functions 選択→計算→グラフ表示の一連フロー
- 無料枠境界値テスト（100万実行、400,000 GB-秒前後）
- AWS Lambda との直接比較シナリオ
- エンタープライズシナリオ（高実行回数での比較）

### 統合テスト
- /serverless APIエンドポイントでの Azure リクエスト処理
- /comparison API での複数プロバイダー比較
- 料金計算の正確性（実行課金 + GB-秒課金）
- 無料枠計算ロジック（2種類の無料枠）

### 単体テスト
- get_azure_functions_cost() メソッドの料金計算ロジック
- 無料枠適用ロジック（実行 + GB-秒）
- 通貨変換の正確性
- 境界値：無料枠境界（100万実行、400,000 GB-秒）
- 例外：負の値、範囲外値
- パフォーマンス：大量実行数での計算速度

## 実装アプローチ

- **Outside-In**: E2Eテストで「Azure Functions 選択→グラフ表示」から開始
- **Red-Green-Refactor**: 
  1. Red: E2Eテスト失敗（UI に Azure 要素なし）
  2. Green: UI→API→計算エンジンの順で実装
  3. Refactor: 既存サーバーレス計算の共通化
- **AWS Lambda 類似**: 既存 Lambda コードパターンの活用

## 見積もり

**5ストーリーポイント**
- AWS Lambda に近い料金体系で実装が標準的
- 2種類の無料枠の正確な適用が必要
- エンタープライズ向け機能説明の充実
- 既存パターンの踏襲により開発効率向上

## 技術的考慮事項

### Azure Functions 料金体系（2025年1月時点、Japan East）

#### Consumption Plan
- **実行課金**: $0.20 per million executions
- **リソース消費課金**: $0.000016 per GB-second
- **無料枠**: 
  - 1,000,000 executions/月
  - 400,000 GB-second/月

#### 計算例
```
月間実行回数: 2,000,000回
メモリ: 512MB (0.5GB)
実行時間: 5秒
実行時間合計: 2,000,000 × 5 = 10,000,000秒
GB-秒: 10,000,000 × 0.5 = 5,000,000 GB-秒

実行課金: (2,000,000 - 1,000,000) × $0.20/1,000,000 = $0.20
GB-秒課金: (5,000,000 - 400,000) × $0.000016 = $73.60
合計: $73.80
```

### UI実装パターン

```html
<!-- Azure Functions 選択 -->
<div class="form-check">
  <input class="form-check-input" type="checkbox" id="compareAzureFunctions">
  <label class="form-check-label" for="compareAzureFunctions">
    <i class="fab fa-microsoft"></i> Compare with Azure Functions
  </label>
</div>

<!-- プラン選択（将来拡張用） -->
<div class="mt-2" id="azureFunctionsOptions" style="display: none;">
  <select class="form-select form-select-sm" id="azureFunctionsPlan">
    <option value="consumption">Consumption Plan</option>
    <option value="premium" disabled>Premium Plan (Coming Soon)</option>
  </select>
  
  <!-- エコシステム統合オプション -->
  <div class="form-check mt-2">
    <input class="form-check-input" type="checkbox" id="azureEcosystem">
    <label class="form-check-label" for="azureEcosystem">
      Include Microsoft 365 ecosystem benefits
    </label>
  </div>
</div>
```

### API仕様

```json
{
  "provider": "azure_functions",
  "plan": "consumption", // "consumption", "premium" (future)
  "memory_mb": 512,
  "execution_time_seconds": 5,
  "monthly_executions": 2000000,
  "include_free_tier": true,
  "include_ecosystem": false, // Microsoft 365 integration
  "exchange_rate": 150
}
```

### レスポンス仕様

```json
{
  "success": true,
  "data": {
    "provider": "azure_functions",
    "plan": "consumption",
    "total_cost_usd": 73.80,
    "total_cost_jpy": 11070,
    "breakdown": {
      "execution_cost_usd": 0.20,
      "gb_second_cost_usd": 73.60,
      "free_tier_savings": {
        "execution_savings": 0.20,
        "gb_second_savings": 6.40
      }
    },
    "free_tier_usage": {
      "executions_used": 2000000,
      "executions_free": 1000000,
      "gb_seconds_used": 5000000,
      "gb_seconds_free": 400000
    }
  }
}
```

### グラフ表示設定

- **色**: #0078D4（Microsoft Blue）
- **線のスタイル**: 実線
- **凡例**: "Azure Functions (Consumption)"
- **アイコン**: Microsoft/Azure ロゴ

## Definition of Done

- [ ] BDD受け入れシナリオが全て通る
- [ ] テストカバレッジ88%以上を維持
- [ ] コードレビュー完了（無料枠計算ロジック重点確認）
- [ ] リファクタリング完了（サーバーレス共通機能の抽出）
- [ ] ドキュメント更新（README、API仕様）
- [ ] i18n対応完了（日英両言語）
- [ ] lintエラー0、型チェック通過
- [ ] パフォーマンステスト通過（レスポンス時間500ms以下）
- [ ] エンタープライズシナリオテスト完了

## 実装詳細補足

### エンタープライズ特化機能
1. **Microsoft 365 統合**: ライセンス最適化の示唆
2. **Active Directory 統合**: ハイブリッドシナリオでのコスト影響
3. **Logic Apps 連携**: ワークフロー全体でのコスト分析

### 技術的特徴
1. **AWS Lambda 類似性**: 移行コスト分析の容易さ
2. **無料枠の複雑性**: 2軸（実行回数 + GB-秒）の正確な適用
3. **スケールメリット**: 大量実行時の cost-effectiveness

### パフォーマンス考慮事項
1. **計算効率**: AWS Lambda と同様の O(1) 計算複雑度
2. **メモリ使用量**: 既存プロバイダーと同等
3. **レスポンス時間**: 500ms以下の維持