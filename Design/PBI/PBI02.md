# PBI #2: Lambda単体コスト計算機能

## プロダクトバックログアイテム

**タイトル**: AWS Lambdaのコスト計算エンジン実装

**ユーザーストーリー**: 
インフラ担当者として、Lambdaの月間コストを計算したい、なぜなら現在のワークロードでのコストを把握したいから

**ビジネス価値**: 
Lambdaの正確なコスト予測により、予算計画が可能になる

**受け入れ基準**:
- [ ] メモリ（128/512/1024/2048MB）×実行時間（1/10/30/60秒）の組み合わせでコスト計算可能
- [ ] 月間実行回数からコストを算出
- [ ] Web UIで入力・結果表示が可能
- [ ] 東京リージョンの最新料金に基づく計算

**見積もり**: 5ポイント

**備考**: 
- 依存関係: PBI #1（技術スタック選定）
- 技術的考慮事項:
  - AWS料金体系の正確な実装
  - 無料枠の考慮（オプション）
  - リアルタイム計算とレスポンシブUI

## 実装詳細

### Lambda料金計算ロジック
```
月間コスト = リクエスト料金 + コンピューティング料金

リクエスト料金 = (月間実行回数 - 無料枠100万回) × $0.20 / 100万回
コンピューティング料金 = GB秒 × $0.0000166667

GB秒 = (メモリサイズ(MB) / 1024) × 実行時間(秒) × 月間実行回数
```

### 入力パラメータ
- **メモリサイズ**: 128MB, 512MB, 1024MB, 2048MB（ドロップダウン）
- **実行時間**: 1秒, 10秒, 30秒, 60秒（ドロップダウン）
- **実行頻度**: 
  - 月間100万回
  - 秒間1回（月間約259万回）
  - 秒間10回（月間約2,592万回）
  - 秒間100回（月間約2.59億回）

### UI要件
- 入力フォーム（3つのドロップダウン）
- 計算結果表示エリア
  - 月間リクエスト料金
  - 月間コンピューティング料金
  - 月間合計（USD）
  - 月間合計（JPY）※デフォルト150円/ドル

### エラーハンドリング
- 入力値の検証
- 計算オーバーフロー対策
- ユーザーフレンドリーなエラーメッセージ