# PBI #8: Google Cloud Compute Engineプロバイダー追加

**タイトル**: Google Cloud Compute Engineプロバイダー追加

**ユーザーストーリー**: 
DevOpsエンジニアとして、Google Cloud Compute Engineのコストを比較したい、なぜならGCPを利用している組織でも最適なデプロイ戦略を選択できるようにしたいから

**ビジネス価値**: 
- Google Cloud利用企業（日本のGCP採用率約15%）へのリーチ拡大
- マルチクラウド環境での総合的なコスト最適化支援
- 競合ツールとの差別化（3大クラウド対応）

## BDD受け入れシナリオ

```gherkin
Scenario: Google Cloud Compute Engineのコスト計算と比較
  Given ユーザーがコスト比較ツールを開いている
  And Lambdaパラメータとして"メモリ:512MB、実行時間:10秒、月間実行回数:100万回"を入力している
  When "Google Cloud"のチェックボックスをオンにする
  And インスタンスタイプとして"e2-micro"を選択する
  And "Calculate"ボタンをクリックする
  Then グラフにGoogle Cloudのコストラインが表示される
  And AWS Lambda、EC2、さくらクラウドと並んで比較可能である
  And break-even pointが正しく計算される

Scenario: Google Cloudインスタンスタイプ選択の検証
  Given ユーザーがGoogle Cloudを選択している
  When インスタンスタイプのドロップダウンを開く
  Then 以下のインスタンスタイプが選択可能である:
    | Instance Type | vCPU | Memory |
    | e2-micro     | 0.25 | 1GB    |
    | e2-small     | 0.5  | 2GB    |
    | e2-medium    | 1    | 4GB    |
    | n2-standard-1| 1    | 4GB    |
    | n2-standard-2| 2    | 8GB    |
    | c2-standard-4| 4    | 16GB   |

Scenario: 通貨換算を含むコスト表示
  Given 為替レートが"150円/USD"に設定されている
  When Google Cloudのコストを計算する
  Then コストがUSD価格から正しく円換算される
  And グラフにUSD/JPY両方の軸で表示される

Scenario: CSV出力でのGoogle Cloudデータ
  Given Google Cloudを含む比較結果が表示されている
  When "Export CSV"ボタンをクリックする
  Then Google CloudのコストデータがCSVに含まれる
  And 列名が"Google Cloud (e2-micro)"形式で出力される
```

## 受け入れ基準

- [ ] Google Cloud Compute Engineの6種類のインスタンスタイプが選択可能
- [ ] 東京リージョン（asia-northeast1）の価格でコスト計算される
- [ ] 既存のEC2、さくらクラウドと同じグラフ上で比較表示される
- [ ] break-even point計算にGoogle Cloudが含まれる
- [ ] CSV出力にGoogle Cloudのデータが含まれる
- [ ] 為替レート設定によるUSD→JPY変換が正しく機能する
- [ ] レスポンシブデザインでモバイルでも操作可能

## t_wadaスタイル テスト戦略

### E2Eテスト
- Google Cloud選択→計算→グラフ表示の一連フロー
- 3プロバイダー同時比較シナリオ
- CSV出力の完全性確認

### 統合テスト
- /vm APIエンドポイントでのGoogle Cloudリクエスト処理
- /comparison APIでの複数プロバイダー比較
- 価格計算の正確性（月額料金変換）

### 単体テスト
- get_gcp_cost()メソッドの価格計算ロジック
- インスタンスタイプ別の料金取得
- 時間料金→月額料金変換（730時間/月）
- 境界値：最小インスタンス（e2-micro）、最大インスタンス（c2-standard-4）
- 例外：無効なインスタンスタイプ

## 実装アプローチ

- **Outside-In**: E2Eテストで「Google Cloud選択→グラフ表示」から開始
- **Red-Green-Refactor**: 
  1. Red: E2Eテスト失敗（UIにGoogle Cloud要素なし）
  2. Green: UI→API→計算機の順で実装
  3. Refactor: 共通プロバイダーインターフェース抽出
- **リファクタリング**: プロバイダー追加を容易にする設計改善

## 見積もり

**5ストーリーポイント**
- 既存パターンの踏襲により実装は標準的
- GCP価格体系の調査が必要
- E2E含む包括的なテスト実装

## 技術的考慮事項

- 依存関係: なし（外部API不要、価格はハードコード）
- テスタビリティ: 既存VMCalculatorのモックパターン利用
- パフォーマンス: 価格データ増加による影響は軽微
- GCP価格: 東京リージョン、オンデマンド価格を使用
- 価格更新: 四半期ごとの価格見直しプロセスに含める

## Definition of Done

- [ ] BDD受け入れシナリオが全て通る
- [ ] テストカバレッジ96%以上を維持
- [ ] コードレビュー完了（特に価格データの正確性）
- [ ] リファクタリング完了（プロバイダー抽象化）
- [ ] ドキュメント更新（README、API仕様）
- [ ] lintエラー0、型チェック通過

## 実装詳細

### Google Cloud価格データ（2025年1月時点、asia-northeast1）

| Instance Type | vCPU | Memory | Hourly Price (USD) |
|--------------|------|--------|-------------------|
| e2-micro     | 0.25 | 1GB    | $0.0084           |
| e2-small     | 0.5  | 2GB    | $0.0168           |
| e2-medium    | 1    | 4GB    | $0.0335           |
| n2-standard-1| 1    | 4GB    | $0.0485           |
| n2-standard-2| 2    | 8GB    | $0.0970           |
| c2-standard-4| 4    | 16GB   | $0.2088           |

### UI実装パターン

```html
<!-- 既存パターンに従う -->
<div class="form-check">
  <input class="form-check-input" type="checkbox" id="compareGCP">
  <label class="form-check-label" for="compareGCP">
    Compare with Google Cloud
  </label>
</div>
<select class="form-select mt-2" id="gcpInstanceType" disabled>
  <option value="e2-micro">e2-micro (0.25 vCPU, 1GB)</option>
  <option value="e2-small">e2-small (0.5 vCPU, 2GB)</option>
  <option value="e2-medium">e2-medium (1 vCPU, 4GB)</option>
  <option value="n2-standard-1">n2-standard-1 (1 vCPU, 4GB)</option>
  <option value="n2-standard-2">n2-standard-2 (2 vCPU, 8GB)</option>
  <option value="c2-standard-4">c2-standard-4 (4 vCPU, 16GB)</option>
</select>
```

### APIリクエスト形式

```json
{
  "provider": "google_cloud",
  "instance_type": "e2-micro",
  "exchange_rate": 150
}
```

### グラフ表示設定

- 色: #FFC107（Amber/黄色系）
- 線のスタイル: 実線
- 凡例: "Google Cloud (インスタンスタイプ)"