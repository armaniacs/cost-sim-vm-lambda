# PBI #15: Oracle Cloud Infrastructure (OCI) Functions プロバイダー追加

**タイトル**: Oracle Cloud Infrastructure (OCI) Functions プロバイダー追加

**ユーザーストーリー**: 
コストエンジニアとして、OCI Functions のコストを AWS Lambda と比較したい、なぜなら Oracle Database を利用している組織で OCI エコシステム全体でのコスト最適化を検討したいから

**ビジネス価値**: 
- **Oracle エコシステム統合**: Oracle Database 利用企業でのサーバーレス戦略支援
- **コスト競争力**: OCI の aggressive pricing による Total Cost 削減可能性の提示
- **Always Free 対応**: OCI の充実した無料枠によるコスト優位性の可視化

## BDD受け入れシナリオ

```gherkin
Scenario: OCI Functions の基本コスト計算
  Given ユーザーがコスト比較ツールを開いている
  And Lambda パラメータとして "メモリ:256MB、実行時間:3秒、月間実行回数:50万回" を入力している
  When "OCI Functions" のチェックボックスをオンにする
  And リージョンとして "ap-tokyo-1" を選択する
  And "Calculate" ボタンをクリックする
  Then グラフに OCI Functions のコストラインが表示される
  And AWS Lambda、他のプロバイダーと並んで比較可能である
  And break-even point が正しく計算される
  And Always Free 枠（200万リクエスト/月、400,000 GB-秒/月）が考慮される

Scenario: OCI Functions Always Free 枠の威力
  Given OCI Functions が選択されている
  When 月間実行回数を 150万回に設定する
  And メモリを 128MB、実行時間を 2秒に設定する
  Then GB-秒が 150万 × 2秒 × 0.125GB = 375,000 GB-秒 と計算される
  And Always Free 枠内（200万リクエスト、400,000 GB-秒）のため課金が $0.00 となる
  And 他のプロバイダーとの大きなコスト差が可視化される

Scenario: 全リージョン同一価格の確認
  Given OCI Functions が選択されている
  When リージョンを "ap-tokyo-1" から "us-ashburn-1" に変更する
  Then 価格が変わらないことが確認される
  And "All regions same pricing" メッセージが表示される
  And 他のプロバイダーとの違いが強調される

Scenario: Oracle Database 統合シナリオ
  Given OCI Functions でコスト計算が完了している
  When "Oracle Database integration" オプションを選択する
  Then Autonomous Database との連携コストが表示される
  And データ転送コスト（10TB無料）が考慮される
  And Oracle ecosystem での Total Cost が算出される

Scenario: Fn Project オープンソース説明
  Given OCI Functions が選択されている
  When "Technical Details" を展開する
  Then Fn Project（オープンソース）ベースであることが説明される
  And ベンダーロックイン回避のメリットが表示される
  And コンテナベース実行の特徴が説明される
```

## 受け入れ基準

### 機能要件
- [ ] OCI Functions の料金計算実装（リクエスト + GB-秒課金）
- [ ] Always Free 枠の正確な適用（200万リクエスト/月 + 400,000 GB-秒/月）
- [ ] 全リージョン同一価格の表示
- [ ] Tokyo リージョン（ap-tokyo-1）でのコスト計算
- [ ] 既存プロバイダーとの統合グラフ表示
- [ ] break-even point 計算への統合
- [ ] CSV出力への OCI データ追加
- [ ] 為替レート変換（USD→JPY）の対応

### 品質要件
- [ ] テストカバレッジ 88% 以上の維持
- [ ] レスポンス時間 500ms 以下
- [ ] モバイルレスポンシブ対応
- [ ] 日英両言語対応（i18n）
- [ ] エラーハンドリング（無効入力、API障害）

## t_wadaスタイル テスト戦略

### E2Eテスト
- OCI Functions 選択→計算→グラフ表示の一連フロー
- Always Free 枠の境界値テスト（200万リクエスト、400,000 GB-秒前後）
- 全リージョン同一価格の確認
- Oracle ecosystem 統合シナリオ

### 統合テスト
- /serverless APIエンドポイントでの OCI リクエスト処理
- /comparison API での複数プロバイダー比較
- 料金計算の正確性（リクエスト + GB-秒課金）
- Always Free 枠計算ロジック

### 単体テスト
- get_oci_functions_cost() メソッドの料金計算ロジック
- Always Free 枠適用ロジック（2軸の無料枠）
- 通貨変換の正確性
- 境界値：Always Free 枠境界値
- 例外：負の値、範囲外値
- 全リージョン同一価格のロジック

## 実装アプローチ

- **Outside-In**: E2Eテストで「OCI Functions 選択→グラフ表示」から開始
- **Red-Green-Refactor**: 
  1. Red: E2Eテスト失敗（UI に OCI 要素なし）
  2. Green: UI→API→計算エンジンの順で実装
  3. Refactor: サーバーレス計算の共通化推進
- **シンプル実装**: AWS Lambda パターンの最適化活用

## 見積もり

**3ストーリーポイント**
- シンプルな料金体系（AWS Lambda 類似）
- Always Free 枠の豊富さがむしろ実装を簡素化
- Oracle 固有機能は最小限
- 既存パターンの活用により高い開発効率

## 技術的考慮事項

### OCI Functions 料金体系（2025年1月時点、全リージョン同一）

#### 基本料金
- **リクエスト課金**: $0.20 per million requests
- **GB-秒課金**: $0.00001417 per GB-second
- **Always Free 枠**: 
  - 2,000,000 requests/月
  - 400,000 GB-second/月

#### 計算例
```
月間実行回数: 3,000,000回
メモリ: 512MB (0.5GB)
実行時間: 4秒
実行時間合計: 3,000,000 × 4 = 12,000,000秒
GB-秒: 12,000,000 × 0.5 = 6,000,000 GB-秒

リクエスト課金: (3,000,000 - 2,000,000) × $0.20/1,000,000 = $0.20
GB-秒課金: (6,000,000 - 400,000) × $0.00001417 = $79.35
合計: $79.55
```

### OCI の特徴
1. **全リージョン同一価格**: グローバル展開時のコスト予測が容易
2. **充実した Always Free**: 他社を圧倒する無料枠
3. **Fn Project ベース**: オープンソース基盤によるベンダーロックイン回避
4. **Oracle Database 統合**: データベース中心アーキテクチャでの最適化

### UI実装パターン

```html
<!-- OCI Functions 選択 -->
<div class="form-check">
  <input class="form-check-input" type="checkbox" id="compareOCIFunctions">
  <label class="form-check-label" for="compareOCIFunctions">
    <i class="fas fa-database"></i> Compare with OCI Functions
    <small class="badge bg-success ms-1">Always Free</small>
  </label>
</div>

<!-- OCI 特徴説明 -->
<div class="mt-2" id="ociFunctionsInfo" style="display: none;">
  <div class="alert alert-info alert-sm">
    <strong>OCI Benefits:</strong>
    <ul class="mb-0 mt-1">
      <li>Same pricing across all regions globally</li>
      <li>Generous Always Free tier (2M requests/month)</li>
      <li>Based on open-source Fn Project</li>
      <li>10TB free egress per month</li>
    </ul>
  </div>
  
  <!-- Oracle エコシステム統合 -->
  <div class="form-check mt-2">
    <input class="form-check-input" type="checkbox" id="oracleEcosystem">
    <label class="form-check-label" for="oracleEcosystem">
      Include Oracle Database ecosystem benefits
    </label>
  </div>
</div>
```

### API仕様

```json
{
  "provider": "oci_functions",
  "memory_mb": 512,
  "execution_time_seconds": 4,
  "monthly_executions": 3000000,
  "include_always_free": true,
  "include_oracle_ecosystem": false,
  "exchange_rate": 150
}
```

### レスポンス仕様

```json
{
  "success": true,
  "data": {
    "provider": "oci_functions",
    "total_cost_usd": 79.55,
    "total_cost_jpy": 11932,
    "breakdown": {
      "request_cost_usd": 0.20,
      "gb_second_cost_usd": 79.35,
      "always_free_savings": {
        "request_savings": 0.40,
        "gb_second_savings": 5.67
      }
    },
    "always_free_usage": {
      "requests_used": 3000000,
      "requests_free": 2000000,
      "gb_seconds_used": 6000000,
      "gb_seconds_free": 400000
    },
    "features": {
      "same_pricing_all_regions": true,
      "open_source_fn_project": true,
      "free_egress_10tb": true
    }
  }
}
```

### グラフ表示設定

- **色**: #FF0000（Oracle Red）
- **線のスタイル**: 一点鎖線
- **凡例**: "OCI Functions (Always Free)"
- **アイコン**: Oracle クラウドロゴ

## Definition of Done

- [ ] BDD受け入れシナリオが全て通る
- [ ] テストカバレッジ88%以上を維持
- [ ] コードレビュー完了（Always Free 枠ロジック重点確認）
- [ ] リファクタリング完了（サーバーレス共通基盤の完成）
- [ ] ドキュメント更新（README、API仕様）
- [ ] i18n対応完了（日英両言語）
- [ ] lintエラー0、型チェック通過
- [ ] パフォーマンステスト通過（レスポンス時間500ms以下）
- [ ] Oracle エコシステム特徴の説明完了

## 実装詳細補足

### Oracle エコシステム特化機能
1. **Autonomous Database 統合**: データベースワークロード最適化
2. **10TB無料 Egress**: 大量データ転送シナリオでのコスト優位性
3. **全リージョン同一価格**: グローバル展開での予算計画簡素化

### 技術的特徴
1. **Fn Project**: オープンソースによる技術的透明性
2. **コンテナベース**: Docker コンテナでの関数実行
3. **Always Free の豊富さ**: 他社を圧倒する無料枠

### コスト競争力
1. **GB-秒単価**: AWS Lambda の約1/3の低価格
2. **Always Free**: AWS の10倍のリクエスト数無料
3. **Egress**: 月10TB無料（AWS は1GB）

### 実装の簡素性
1. **料金体系**: AWS Lambda とほぼ同じ構造
2. **API設計**: 既存パターンの再利用
3. **UI要素**: 最小限の追加で最大効果