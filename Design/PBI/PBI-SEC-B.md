# PBI-SEC-B: セキュア通信基盤

## プロダクトバックログアイテム概要

**PBI ID**: SEC-B  
**タイトル**: セキュア通信基盤  
**見積もり**: 3ストーリーポイント  
**優先度**: 高（緊急対応）  
**実装タスク**: SEC-03, SEC-04

## ユーザーストーリー

**エンドユーザー**として、**クロスサイト攻撃から保護された通信**がほしい、なぜなら**安全にWebアプリケーションを利用したい**から

## ビジネス価値

### 主要価値
- **攻撃防御**: CSRF、XSSなどのクロスサイト攻撃を防止
- **通信制御**: 信頼できるドメインのみとの通信許可
- **ユーザー保護**: セッション乗っ取りや不正操作を防止

### 測定可能な成果
- クロスサイト攻撃防御率: 100%
- 不正ドメインからのアクセス拒否率: 100%
- セキュリティインシデント発生率: 0件/月

## BDD受け入れシナリオ

### シナリオ1: 信頼できるドメインからの正常アクセス
```gherkin
Feature: CORS設定による通信制御
  As a エンドユーザー
  I want 信頼できるドメインからの安全なアクセス
  So that セキュアにアプリケーションを利用できる

Scenario: ユーザーが信頼できるドメインからアプリケーションにアクセスする
  Given CORS設定で許可されたドメインからアクセスしている
  And ブラウザが現在 https://cost-simulator.example.com にいる
  When コスト計算フォームを送信する
  Then リクエストが正常に処理される
  And CORSヘッダーが適切に設定される
  And Access-Control-Allow-Origin ヘッダーに許可ドメインが含まれる
```

### シナリオ2: 悪意のあるサイトからのアクセス拒否
```gherkin
Feature: 不正ドメイン防御
  As a セキュリティ担当者
  I want 許可されていないドメインからのアクセス拒否
  So that クロスオリジン攻撃を防げる

Scenario: 悪意のあるサイトからのリクエストがブロックされる
  Given 許可されていないドメイン https://malicious-site.com からのリクエスト
  When APIエンドポイント /api/calculator/calculate にアクセスを試みる
  Then CORS エラーでリクエストが拒否される
  And ブラウザが通信をブロックする
  And セキュリティログに不正アクセス試行が記録される
```

### シナリオ3: CSRF保護によるフォーム送信
```gherkin
Feature: CSRF攻撃防御
  As a エンドユーザー
  I want CSRF攻撃から保護されたフォーム送信
  So that 意図しない操作を実行させられない

Scenario: ユーザーがフォーム送信時にCSRF保護される
  Given Webページにアクセスしている
  When コスト計算フォームが表示される
  Then CSRF トークンがフォームに含まれる
  And meta タグにCSRFトークンが設定される
  
Scenario: 無効なCSRFトークンでの送信拒否
  Given 改ざんまたは古いCSRFトークンを持つフォーム
  When フォーム送信を試みる
  Then 403 Forbiddenエラーが返される
  And CSRF保護エラーメッセージが表示される
  And セキュリティログに試行が記録される
```

## 受け入れ基準

### 機能要件
- [ ] CORS設定で特定ドメインのみ許可（ワイルドカード削除）
- [ ] credentialsサポート有効化（Cookie、認証ヘッダー対応）
- [ ] CSRF保護がFlaskアプリで初期化済み
- [ ] 全フォームにCSRFトークン自動挿入
- [ ] CSRFトークン検証失敗時の適切なエラーレスポンス

### 非機能要件
- [ ] CORS プリフライトリクエスト処理時間: 50ms以下
- [ ] CSRFトークン生成時間: 10ms以下
- [ ] フォーム表示時のCSRFトークン埋め込み: 自動
- [ ] セキュリティログの即座記録

### セキュリティ要件
- [ ] 許可ドメインリストの適切な管理
- [ ] CSRFトークンの予測不可能性
- [ ] CSRFトークンの適切な有効期限設定
- [ ] セキュリティヘッダーの適切な設定

## t_wadaスタイル テスト戦略

### Outside-In TDD アプローチ
```
E2Eテスト（ブラウザベース）→ 統合テスト（APIレベル）→ 単体テスト（ロジック）
```

### E2Eテスト
- **許可ドメインからの正常アクセステスト**
  - Selenium WebDriverで実際のブラウザテスト
  - 正常なフォーム送信フローテスト
- **不正ドメインからのアクセス拒否テスト**
  - 異なるオリジンからのAjaxリクエストテスト
  - ブラウザのCORS拒否確認
- **CSRFトークン検証テスト**
  - 正常なCSRFトークンでの送信成功
  - 改ざんトークンでの送信失敗

### 統合テスト
- **CORS ミドルウェア設定テスト**
  - Flask-CORS設定の動作確認
  - プリフライトリクエスト処理確認
- **CSRF 保護機能テスト**
  - Flask-WTF CSRFProtect動作確認
  - トークン生成・検証機能確認
- **フォームトークン生成テスト**
  - Jinjaテンプレートでのトークン埋め込み確認

### 単体テスト
- **CORS設定バリデーション**
  - 許可ドメインリスト検証機能
  - オリジンヘッダー解析機能
- **CSRFトークン生成・検証**
  - トークン生成アルゴリズム
  - トークン有効性検証ロジック
- **ドメイン許可リスト機能**
  - ドメインマッチング処理
  - ワイルドカード処理ロジック

## 実装アプローチ

### Phase 1: CORS設定強化
1. **ワイルドカード削除と特定ドメイン許可**
   ```python
   # app/main.py の修正
   CORS(app, origins=[
       'https://cost-simulator.example.com',
       'https://localhost:5001',  # 開発環境
       'https://staging.cost-simulator.example.com'  # ステージング
   ], supports_credentials=True)
   ```

2. **動的ドメイン設定対応**
   ```python
   # 環境変数からの許可ドメイン読み込み
   allowed_origins = os.environ.get('CORS_ORIGINS', '').split(',')
   CORS(app, origins=allowed_origins, supports_credentials=True)
   ```

### Phase 2: CSRF保護初期化
1. **CSRFProtect初期化**
   ```python
   from flask_wtf.csrf import CSRFProtect
   
   csrf = CSRFProtect()
   csrf.init_app(app)
   ```

2. **全フォームでのCSRFトークン自動挿入**
   ```html
   <!-- base.html テンプレート修正 -->
   <meta name=\"csrf-token\" content=\"{{ csrf_token() }}\">
   <input type=\"hidden\" name=\"csrf_token\" value=\"{{ csrf_token() }}\" />
   ```

3. **Ajax リクエスト対応**
   ```javascript
   // CSRFトークンをAjaxヘッダーに自動追加
   $.ajaxSetup({
       beforeSend: function(xhr, settings) {
           if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
               xhr.setRequestHeader(\"X-CSRFToken\", $(\"meta[name=csrf-token]\").attr(\"content\"));
           }
       }
   });
   ```

### Red-Green-Refactor サイクル
1. **Red**: 不正オリジンでのアクセステスト作成（失敗）
2. **Green**: CORS設定適用でテスト成功
3. **Refactor**: 設定の外部化とパフォーマンス最適化

## 技術的考慮事項

### 依存関係
- **Flask-CORS**: CORS設定管理
- **Flask-WTF**: CSRF保護機能
- **python-dotenv**: 環境変数管理

### パフォーマンス
- プリフライトリクエストキャッシュ設定
- CSRFトークンの適切な有効期限
- セッション管理最適化

### セキュリティ
- CSRFトークンのセキュアなランダム生成
- CORS設定の最小権限原則
- セキュリティヘッダーとの連携

## Configuration

### 本番環境設定例
```bash
# 環境変数設定
CORS_ORIGINS=https://cost-simulator.example.com,https://app.cost-simulator.example.com
CSRF_TIME_LIMIT=3600  # 1時間
WTF_CSRF_TIME_LIMIT=3600
```

### 開発環境設定例
```bash
# 開発用設定
CORS_ORIGINS=http://localhost:5001,http://127.0.0.1:5001
CSRF_TIME_LIMIT=7200  # デバッグ用に長め
```

## Definition of Done

### 機能完了基準
- [ ] 全受け入れシナリオがパスする
- [ ] 許可されたドメインからのアクセスが正常動作
- [ ] 不正ドメインからのアクセスが確実に拒否される
- [ ] 全フォームでCSRF保護が有効

### 品質基準
- [ ] E2Eテストカバレッジ: 100%（重要シナリオ）
- [ ] セキュリティスキャンでCSRF/CORS脆弱性なし
- [ ] パフォーマンステスト基準クリア
- [ ] ブラウザ互換性テスト完了

### ドキュメント
- [ ] CORS設定ガイドライン作成
- [ ] CSRF保護の開発者向けドキュメント
- [ ] セキュリティ設定手順書更新
- [ ] トラブルシューティングガイド作成

### デプロイ準備
- [ ] 本番環境でのドメイン設定完了
- [ ] CORS/CSRF動作確認完了
- [ ] セキュリティヘッダー設定確認
- [ ] 監視アラート設定完了

## 関連PBI
- **前提条件**: PBI-SEC-A（認証基盤と連携）
- **依存PBI**: なし（独立実装可能）
- **後続PBI**: PBI-SEC-C（包括的入力検証と統合）

## リスクと軽減策

### 主要リスク
1. **既存ユーザーへの影響** → 段階的デプロイとフォールバック準備
2. **CORS設定ミス** → 十分なテストと設定検証
3. **CSRF UX影響** → ユーザーフレンドリーなエラーメッセージ

### 軽減策
- 複数ブラウザでのクロスブラウザテスト
- 段階的な機能有効化（Feature Flag使用）
- ユーザビリティテストによるUX確認
- セキュリティ設定の自動検証