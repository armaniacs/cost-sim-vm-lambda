# PBI #9: インターネットegress転送費用計算機能の追加

**タイトル**: インターネットegress転送費用計算機能の追加

**ユーザーストーリー**: 
システムアーキテクトとして、Lambda実行やVM運用時のインターネットegress転送費用を含めた総合的なコスト比較がしたい、なぜならデータ転送費用は高トラフィックアプリケーションで大きなコスト要因となり、正確な意思決定には不可欠だから

**ビジネス価値**: 
- **正確なコスト比較**: egress費用を含めたより現実的なコスト分析の実現
- **アーキテクチャ最適化**: 高転送量アプリケーションでの適切な選択肢の特定支援
- **予算計画精度向上**: データ転送費用を考慮した正確な予算策定の支援

## BDD受け入れシナリオ

```gherkin
Scenario: egress費用を含む基本的なコスト比較
  Given コストシミュレーターでLambda 512MB、5秒実行、月間100万回が設定されている
  When egress転送量として100KBを入力する
  And AWS EC2 t3.smallを比較対象として選択する
  And 計算ボタンをクリックする
  Then グラフにLambda総コスト（実行費用+egress費用）が表示される
  And EC2総コスト（固定費用+egress費用）が表示される
  And break-evenポイントがegress費用込みで再計算される
  And 費用内訳でegress費用が個別表示される

Scenario: リアルタイムegress費用計算
  Given 基本設定が完了している
  When egress転送量を10KB→100KB→1MBと変更する
  Then グラフが即座に更新される
  And egress費用増加でbreak-evenポイントが移動する
  And 高転送量でVM有利性が視覚化される

Scenario: CSV出力でegress費用詳細確認
  Given egress費用込みコスト計算が完了している
  When CSV出力ボタンをクリックする
  Then ダウンロードCSVにegress費用列が含まれる
  And 実行費用とegress費用が分離記録される
  And 各プロバイダーのegress単価も記録される

Scenario: 無効入力のエラーハンドリング
  Given コストシミュレーター画面が表示されている
  When egress転送量に負の値または非数値を入力する
  Then 適切なエラーメッセージが表示される
  And 計算ボタンが無効化される
```

## 受け入れ基準

### 機能要件
- [ ] egress転送量入力フィールドの追加 (10KB, 100KB, 1MB選択 + 自由入力対応)
- [ ] AWS Lambda egress料金計算の実装 (0.09 USD/GB)
- [ ] AWS EC2 egress料金計算の実装 (0.09 USD/GB)
- [ ] Sakura Cloud egress料金計算の実装 (既存料金体系準拠)
- [ ] Google Cloud egress料金計算の実装 (0.085 USD/GB)
- [ ] グラフでegress費用を含む総コスト表示
- [ ] break-evenポイントの再計算 (egress費用込み)
- [ ] CSV出力でegress費用詳細の出力
- [ ] 入力値検証とエラーハンドリング

### 品質要件
- [ ] 既存機能への影響がないこと
- [ ] リアルタイム計算 <100ms の維持
- [ ] テストカバレッジ95%以上の維持

## t_wadaスタイル テスト戦略

### E2Eテスト (最小限、ハッピーパス重視)
- egress転送量入力→計算→グラフ表示の完全フロー
- CSV出力でegress費用確認

### 統合テスト (APIコントラクトと主要パス)
- POST /api/v1/calculator/comparison (egress費用対応)
- 各プロバイダーegress料金計算API
- Currency conversion with egress fees
- CSV export format validation

### 単体テスト (ビジネスロジックと境界値)
- EgressCalculator.calculate_*_egress() methods
- 各プロバイダー料金レート計算
- 境界値テスト (0KB, 最大値, 無効値)
- 通貨変換精度テスト
- Cost aggregation logic

### テストピラミッド設計
```
E2Eテスト (3テスト):
✓ 基本egress費用計算フロー
✓ CSV出力でegress費用確認
✓ エラーハンドリング

統合テスト (10テスト):
✓ Lambda egress API
✓ EC2 egress API
✓ Sakura Cloud egress API
✓ Google Cloud egress API
✓ Currency conversion with egress
✓ Break-even calculation with egress
✓ CSV format validation

単体テスト (25テスト):
✓ AWS Lambda egress pricing calculation
✓ AWS EC2 egress pricing calculation
✓ Sakura Cloud egress pricing calculation
✓ Google Cloud egress pricing calculation
✓ Egress volume validation (境界値)
✓ Invalid input handling
✓ Cost aggregation logic
✓ Currency conversion precision
```

## 実装アプローチ

### Outside-In TDD
1. **E2Eテスト作成**: egress入力→グラフ表示の完全フローから開始
2. **API統合テスト**: 各プロバイダーのegress計算APIテスト
3. **単体テスト**: EgressCalculatorクラスの詳細ロジック

### Red-Green-Refactor サイクル
- 各プロバイダーのegress計算をTDDで段階的実装
- 既存Calculatorクラスの責任分離リファクタリング
- テストカバレッジ維持した継続的品質改善

### 技術的考慮事項

**依存関係**: 
- 既存VM/Lambdaコスト計算エンジンの拡張
- Chart.jsグラフ表示の更新
- CSV出力フォーマットの拡張

**テスタビリティ**: 
- EgressCalculatorクラスで料金計算ロジック分離
- プロバイダー別料金レートのモック化
- 外部APIに依存しない単体テスト設計

**パフォーマンス**: 
- リアルタイム計算 <100ms の維持
- 大量転送量入力時の計算最適化
- 既存グラフ描画パフォーマンスへの影響最小化

## 見積もり
**5ストーリーポイント** (要チーム見積もり確認)

**詳細内訳:**
- UI実装 (入力フィールド追加): 1SP
- APIエンドポイント拡張: 1SP  
- 各プロバイダーegress計算ロジック: 2SP
- テスト実装 (E2E〜単体): 1SP

## Definition of Done

### 機能完了基準
- [ ] 全BDD受け入れシナリオが通る
- [ ] 受け入れ基準が全て満たされる
- [ ] エラーハンドリングが適切に動作する

### 品質基準
- [ ] テストカバレッジ95%以上維持
- [ ] 全既存テストが通る (回帰テストクリア)
- [ ] 静的解析 (lint, type check) エラーゼロ

### レビュー・ドキュメント
- [ ] コードレビュー完了
- [ ] API仕様書更新
- [ ] ユーザードキュメント更新 (README.md等)

### デプロイ準備
- [ ] 本番環境での動作確認
- [ ] パフォーマンステスト通過
- [ ] セキュリティチェック完了

## INVEST原則チェック ✅

- **I**ndependent: 既存機能から独立、単独で価値提供
- **N**egotiable: egress料金レートや入力UI詳細は実装中調整可能  
- **V**aluable: データ転送費用を含む正確なコスト比較という明確な価値
- **E**stimable: 5SP、既存アーキテクチャ拡張で見積もり可能
- **S**mall: 1スプリント(2週間)で完了可能
- **T**estable: BDDシナリオで明確な受け入れ基準

## 品質保証メトリクス

- **ビヘイビアカバレッジ**: 4つの主要シナリオで100%
- **テストピラミッド比率**: E2E(3):統合(10):単体(25) ≈ 1:3:8
- **リファクタリング指標**: 各グリーン後のリファクタリング実施

---

## 開発プロセス（BDD×TDD統合）

### 1. BDDシナリオ作成
ステークホルダーとの協働でユーザーシナリオ定義

### 2. 受け入れテスト実装
Gherkinシナリオをテストコードに変換

### 3. Outside-In TDD
外側（E2E）から内側（単体）へテスト駆動で実装

### 4. 継続的リファクタリング
グリーンになったら品質改善のリファクタリング

### 5. シナリオ検証
ステークホルダーとシナリオ実行確認

このPBIは、ryuzeeの垂直分割でエンドツーエンドの価値を提供し、BDDでステークホルダーとの共通理解を確保し、t_wadaスタイルのテスト戦略で堅牢な実装品質を保証する統合アプローチで設計されています。