# PBI #10: インターネット転送割合設定機能

**タイトル**: インターネット転送割合設定機能

**ユーザーストーリー**: 
**インフラ設計者**として、**インターネット転送割合を設定できる機能**がほしい、なぜなら**現実的なネットワーク構成でのegress費用を正確に評価し、最適なアーキテクチャ選択を行いたい**から

**ビジネス価値**:
- **正確性向上**: 実際のシステムは100%インターネット転送することは稀。現実的な割合でのコスト予測が可能
- **設計支援**: 完全閉域（0%）から完全パブリック（100%）まで、ネットワーク設計の選択肢を数値で比較可能  
- **コスト最適化**: ネットワーク構成がegress費用に与える影響を定量的に評価

### 優先度
**High** - 既存egress計算機能の精度向上に直結

### 見積もり
**5ストーリーポイント**
- UI拡張: 2SP
- API拡張: 1SP  
- 計算ロジック拡張: 1SP
- テスト実装: 1SP

---

## BDD受け入れシナリオ

### Scenario 1: プリセット転送割合での計算
```gherkin
Given コスト比較シミュレーターが起動している
When ユーザーがインターネット転送割合として "50%" を選択する
And 他のパラメータ（Lambda設定、VM設定）を入力する
And "計算実行" ボタンをクリックする
Then egress費用が50%として計算される
And グラフに反映された結果が表示される
And CSV出力にも50%適用後の費用が含まれる
```

### Scenario 2: カスタム転送割合での計算
```gherkin
Given コスト比較シミュレーターが起動している
When ユーザーがカスタム入力欄に "75" を入力する
And 他のパラメータを設定して計算を実行する
Then egress費用が75%として計算される
And カスタム値がUIに保持される
```

### Scenario 3: 無効な転送割合の入力
```gherkin
Given コスト比較シミュレーターが起動している
When ユーザーがカスタム入力欄に "-10" を入力する
And 計算を実行しようとする
Then "転送割合は0-100の範囲で入力してください" エラーが表示される
And 計算は実行されない
```

### Scenario 4: 完全閉域環境での計算
```gherkin
Given コスト比較シミュレーターが起動している
When ユーザーがインターネット転送割合として "0%" を選択する
And 計算を実行する
Then 全プロバイダのegress費用が0として計算される
And Lambda vs VM の比較で egress影響が除外される
```

---

## 受け入れ基準

### 機能要件
- [ ] プリセット値（100%, 50%, 10%, 0%）をボタンまたはドロップダウンで選択可能
- [ ] カスタム値（0-100の数値）を入力欄で設定可能
- [ ] 入力値のバリデーション（0-100範囲外はエラー表示）
- [ ] 設定した割合がLambda・全VMプロバイダのegress計算に正しく適用される
- [ ] グラフ表示に転送割合の影響が反映される
- [ ] CSV出力に転送割合適用後の費用が含まれる
- [ ] UI設定値がブラウザセッション中保持される

### 非機能要件
- [ ] レスポンス時間: 計算実行後2秒以内に結果表示
- [ ] ブラウザ互換性: Chrome, Firefox, Safari, Edge対応
- [ ] アクセシビリティ: キーボード操作、スクリーンリーダー対応

---

## t_wadaスタイル テスト戦略

### E2Eテスト (最小限・高価値)
- プリセット値選択→計算→グラフ確認の完全フロー
- カスタム値入力→計算→CSV出力の完全フロー
- バリデーションエラー→修正→再計算の完全フロー

### 統合テスト (APIコントラクト・主要パス)
- API: 転送割合パラメータの受け渡し確認
- 計算エンジン: Lambda/VM egress計算での割合適用確認
- データフロー: UI→API→計算→結果表示の統合確認

### 単体テスト (ビジネスロジック・境界値)
- egress計算ロジック: 割合適用前後の費用計算精度
- バリデーション: 境界値テスト（0, 100, -1, 101, 50.5）
- UI コンポーネント: プリセット選択、カスタム入力の動作
- API エンドポイント: パラメータ検証とエラーレスポンス

---

## 実装アプローチ

### Outside-In TDD実装順序
1. **E2E受け入れテスト作成**: BDDシナリオをテストコードに変換
2. **API層実装**: 転送割合パラメータの受け取り・検証
3. **計算ロジック拡張**: 既存egress計算に割合適用機能を追加
4. **UI実装**: プリセット選択・カスタム入力コンポーネント
5. **統合・リファクタリング**: コードの可読性・保守性向上

### Red-Green-Refactor適用
- **Red**: 失敗するテストを先に作成
- **Green**: 最小限の実装でテストを通す
- **Refactor**: グリーン状態でコードの品質を改善

---

## 技術的考慮事項

### 依存関係
- **既存機能**: egress計算ロジックを非破壊的に拡張
- **API変更**: 新しいパラメータ追加（後方互換性確保）
- **外部依存**: なし

### パフォーマンス
- **計算負荷**: 割合の乗算処理のみ（軽微な影響）
- **メモリ使用量**: 新規パラメータ1つのみ（影響なし）

### セキュリティ
- **入力検証**: 0-100範囲チェック、数値型検証
- **XSS対策**: 入力値のサニタイズ

### UI/UX設計
- **一貫性**: 既存デザインシステムに準拠
- **ユーザビリティ**: プリセット値で簡単操作、カスタム値で柔軟性
- **レスポンシブ**: モバイル・タブレット対応

---

## Definition of Done

### 品質基準
- [ ] BDD受け入れシナリオが全て自動テストで検証される
- [ ] テストカバレッジが90%以上を維持する
- [ ] ESLint・Prettier・型チェックが全て通る
- [ ] 既存機能に対するリグレッションテストが通る

### レビュー・ドキュメント
- [ ] コードレビュー完了（セキュリティ・パフォーマンス観点含む）
- [ ] API仕様書更新（新パラメータ追加）
- [ ] ユーザードキュメント更新（操作手順・設定例追加）

### デプロイ・監視
- [ ] ステージング環境での動作確認完了
- [ ] 本番デプロイ手順書確認
- [ ] エラー監視・ログ設定確認

---

## 関連情報

### 参照ドキュメント
- `Design/Overview.md` - プロジェクト概要とegress料金体系
- `ref/technical-specifications.md` - 計算ロジック仕様
- `ref/api-reference.md` - API仕様書

### 関連PBI
- PBI-009: Egress費用計算機能（前提条件）
- 将来PBI: ネットワーク構成テンプレート機能（発展可能性）

### ステークホルダー
- **プロダクトオーナー**: 機能仕様承認・受け入れテスト立会い
- **インフラアーキテクト**: ドメイン知識提供・実地検証
- **開発チーム**: 実装・テスト・レビュー
- **QAチーム**: 品質検証・ユーザビリティテスト

---

**作成日**: 2025-07-13  
**作成者**: 開発チーム  
**承認者**: プロダクトオーナー（承認待ち）  
**ステータス**: Ready for Sprint Planning