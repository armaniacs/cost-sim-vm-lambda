# PBI-SEC-C: 包括的入力検証・データ保護

## プロダクトバックログアイテム概要

**PBI ID**: SEC-C  
**タイトル**: 包括的入力検証・データ保護  
**見積もり**: 8ストーリーポイント  
**優先度**: 中（1週間以内実施）  
**実装タスク**: SEC-05, SEC-06, SEC-07, SEC-08

## ユーザーストーリー

**開発者**として、**悪意のある入力から保護されたAPI**がほしい、なぜなら**XSS、インジェクション、DoS攻撃を防ぎたい**から

## ビジネス価値

### 主要価値
- **攻撃防御**: XSS、SQLインジェクション、DoS攻撃の防止
- **サービス可用性**: レート制限によるサービス安定性確保
- **データ整合性**: 入力サニタイゼーションによるデータ品質向上
- **運用コスト削減**: 攻撃による障害対応コストの削減

### 測定可能な成果
- セキュリティインシデント発生率: 80%削減
- サービス可用性: 99.9%維持
- 悪意ある入力検出率: 95%以上
- システム応答時間: 5%以内の劣化

## BDD受け入れシナリオ

### シナリオ1: 通常ユーザーの正常な計算リクエスト
```gherkin
Feature: 正常入力の適切な処理
  As a エンドユーザー
  I want 入力データが安全に処理される
  So that 正確なコスト計算結果を得られる

Scenario: ユーザーが通常の計算リクエストを送信する
  Given 正常な計算パラメータを持っている
    | memory_size | 512 |
    | execution_time | 30 |
    | execution_frequency | 1000000 |
  When コスト計算APIにリクエストする
  Then 入力値が適切にサニタイズされる
  And 計算結果が正常に返される
  And セキュリティヘッダーが付与される
  And レスポンス時間が2秒以内である
```

### シナリオ2: 悪意のあるスクリプト注入の防御
```gherkin
Feature: XSS攻撃防御
  As a セキュリティ担当者
  I want XSSペイロードの無害化
  So that スクリプト注入攻撃を防げる

Scenario: 悪意のあるスクリプトが入力に含まれる
  Given XSSペイロードを含む入力データ
    | field | value |
    | instance_name | <script>alert('XSS')</script> |
    | region | javascript:void(0) |
  When 計算フォームに入力して送信する
  Then スクリプトタグが無害化される
  And HTMLエスケープが適用される
  And サニタイズされた値がデータベースに保存される
  And セキュリティログに攻撃試行が記録される
```

### シナリオ3: レート制限によるDoS攻撃防御
```gherkin
Feature: DoS攻撃防御
  As a システム管理者
  I want 大量リクエストの制限
  So that サービス可用性を維持できる

Scenario: 大量のリクエストがレート制限される
  Given 同じIPアドレス 192.168.1.100 から
  When 1分間に100回以上APIを呼び出す
  Then 制限値を超えた時点で429 Too Many Requestsエラーが返される
  And X-RateLimit-Limit: 100 ヘッダーが含まれる
  And X-RateLimit-Remaining: 0 ヘッダーが含まれる
  And X-RateLimit-Reset: [timestamp] ヘッダーが含まれる
  And 60秒後にアクセス可能になる

Scenario: 正常ユーザーは制限内でアクセス可能
  Given 通常の利用パターンのユーザー
  When 1時間に50回APIを呼び出す
  Then 全てのリクエストが正常に処理される
  And レート制限にかからない
```

### シナリオ4: システムエラー時の情報保護
```gherkin
Feature: 情報漏洩防止
  As a セキュリティ担当者
  I want 内部エラー情報の非表示
  So that システム内部構造が漏洩しない

Scenario: システムエラーが発生した際の情報保護
  Given 内部でシステムエラーが発生する状況
    | error_type | database_connection_error |
    | internal_message | Connection to 'production-db.internal:5432' failed |
  When APIレスポンスでエラーが返される
  Then 内部実装詳細が漏洩しない
  And ユーザーフレンドリーなメッセージが表示される
    | user_message | サーバーで一時的な問題が発生しました。しばらく後に再試行してください。 |
  And 詳細なエラーはサーバーログに記録される
  And エラーIDがレスポンスに含まれる
```

## 受け入れ基準

### 機能要件
- [ ] セキュリティミドルウェアが全エンドポイントで有効
- [ ] 全入力フィールドでHTMLエスケープ・サニタイゼーション実装
- [ ] レート制限（1時間100リクエスト/IP）の実装
- [ ] エラーレスポンスで内部情報非表示
- [ ] セキュリティイベントの包括的ログ記録

### 非機能要件
- [ ] 入力サニタイゼーション処理時間: 50ms以下
- [ ] レート制限チェック時間: 10ms以下
- [ ] セキュリティミドルウェアオーバーヘッド: 5%以下
- [ ] ログ記録遅延: 100ms以下

### セキュリティ要件
- [ ] OWASP XSS防御ガイドライン準拠
- [ ] SQLインジェクション完全防御
- [ ] 分散DoS攻撃への基本防御
- [ ] セキュリティログの改ざん防止

## t_wadaスタイル テスト戦略

### Outside-In TDD アプローチ
```
E2E（攻撃シナリオ）→ 統合テスト（ミドルウェア）→ 単体テスト（検証ロジック）
```

### E2Eテスト
- **XSSペイロード入力拒否テスト**
  - 各種XSSパターンの注入テスト
  - JavaScript実行の防止確認
- **SQLインジェクション防御テスト**
  - 悪意のあるSQL構文注入テスト
  - パラメータ化クエリの動作確認
- **レート制限動作テスト**
  - 大量リクエストでの制限発動確認
  - 制限解除後の正常動作確認
- **エラーハンドリングテスト**
  - 各種エラー条件での情報漏洩防止確認

### 統合テスト
- **サニタイゼーション機能テスト**
  - Flask-WTF、bleachライブラリ統合確認
  - フォームバリデーション動作確認
- **レート制限ミドルウェアテスト**
  - Flask-Limiterミドルウェア動作確認
  - Redis/Memcachedとの連携確認
- **セキュリティヘッダー付与テスト**
  - SecurityHeadersミドルウェア動作確認
  - 全エンドポイントでのヘッダー確認

### 単体テスト
- **入力検証ルール**
  - HTMLタグ除去機能
  - SQLキーワード検出機能
  - JavaScript実行文字列検出
- **HTMLエスケープ機能**
  - 特殊文字エスケープ処理
  - URL エンコーディング処理
- **レート制限アルゴリズム**
  - Token Bucket アルゴリズム
  - Sliding Window アルゴリズム
- **エラーメッセージフィルタリング**
  - 内部情報マスキング機能
  - ユーザーフレンドリーメッセージ生成

## 実装アプローチ

### Phase 1: セキュリティミドルウェア有効化
1. **包括的セキュリティミドルウェア初期化**
   ```python
   # app/main.py
   from app.security.middleware import SecurityMiddleware
   
   security_middleware = SecurityMiddleware()
   security_middleware.init_app(app)
   ```

2. **セキュリティヘッダー自動付与**
   ```python
   @app.after_request
   def add_security_headers(response):
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       return response
   ```

### Phase 2: 入力サニタイゼーション実装
1. **HTML エスケープ処理**
   ```python
   import bleach
   from markupsafe import escape
   
   def sanitize_input(data):
       if isinstance(data, str):
           # HTMLタグ除去
           clean_data = bleach.clean(data, tags=[], strip=True)
           # HTMLエスケープ
           return escape(clean_data)
       return data
   ```

2. **フォームバリデーション強化**
   ```python
   from wtforms import validators
   
   class SecureCalculatorForm(FlaskForm):
       memory_size = IntegerField('Memory Size', [
           validators.NumberRange(min=128, max=10240),
           validators.DataRequired()
       ])
       # XSS防御バリデーター追加
       custom_validator = StringField('Custom Input', [
           validators.Length(max=100),
           NoXSSValidator()
       ])
   ```

### Phase 3: レート制限実装
1. **Flask-Limiter設定**
   ```python
   from flask_limiter import Limiter
   from flask_limiter.util import get_remote_address
   
   limiter = Limiter(
       app,
       key_func=get_remote_address,
       default_limits=[\"200 per day\", \"50 per hour\"],
       storage_uri=\"redis://localhost:6379\"
   )
   
   @app.route('/api/calculator/calculate')
   @limiter.limit(\"100 per hour\")
   def calculate_cost():
       # 計算処理
   ```

2. **カスタムレート制限ロジック**
   ```python
   def custom_rate_limit_key():
       # IPアドレス + ユーザーIDベースの制限
       return f\"{get_remote_address()}:{session.get('user_id', 'anonymous')}\"
   ```

### Phase 4: エラーハンドリング改善
1. **セキュアエラーレスポンス**
   ```python
   @app.errorhandler(500)
   def internal_error(error):
       error_id = str(uuid.uuid4())
       
       # 詳細ログは内部記録
       app.logger.error(f\"Error {error_id}: {str(error)}\", exc_info=True)
       
       # ユーザーには簡潔なメッセージ
       return jsonify({
           'error': 'Internal server error',
           'message': 'サーバーで一時的な問題が発生しました',
           'error_id': error_id,
           'support_contact': 'support@example.com'
       }), 500
   ```

### Red-Green-Refactor サイクル
1. **Red**: XSSペイロード注入テスト作成（失敗）
2. **Green**: サニタイゼーション実装でテスト成功
3. **Refactor**: パフォーマンス最適化とセキュリティ強化

## 技術的考慮事項

### 依存関係
- **Flask-Limiter**: レート制限機能
- **bleach**: HTMLサニタイゼーション
- **WTForms**: フォームバリデーション
- **Redis**: レート制限ストレージ

### パフォーマンス最適化
- サニタイゼーション結果のキャッシュ
- レート制限チェックの最適化
- 非同期ログ記録

### セキュリティ考慮事項
- サニタイゼーション回避の防止
- レート制限回避対策
- ログインジェクション攻撃防止

## Configuration

### セキュリティ設定
```python
# config/security.py
SECURITY_CONFIG = {
    'SANITIZATION': {
        'ALLOWED_TAGS': [],  # HTMLタグ全て拒否
        'ALLOWED_ATTRIBUTES': {},
        'STRIP_COMMENTS': True
    },
    'RATE_LIMITING': {
        'GLOBAL_LIMIT': '200 per day',
        'API_LIMIT': '100 per hour',
        'BURST_LIMIT': '10 per minute'
    },
    'ERROR_HANDLING': {
        'EXPOSE_INTERNAL_ERRORS': False,
        'LOG_LEVEL': 'INFO',
        'MASK_SENSITIVE_DATA': True
    }
}
```

## Definition of Done

### 機能完了基準
- [ ] 全受け入れシナリオがパスする
- [ ] XSS攻撃が完全に防御される
- [ ] レート制限が適切に動作する
- [ ] 内部エラー情報が漏洩しない
- [ ] セキュリティログが包括的に記録される

### 品質基準
- [ ] セキュリティテストカバレッジ: 95%以上
- [ ] パフォーマンス劣化: 5%以内
- [ ] OWASP ZAP スキャンで脆弱性検出なし
- [ ] 負荷テストでレート制限正常動作

### ドキュメント
- [ ] セキュリティ機能開発者ガイド
- [ ] 入力検証ルールドキュメント
- [ ] レート制限設定ガイド
- [ ] エラーハンドリング手順書

### デプロイ準備
- [ ] 本番環境でのRedis設定完了
- [ ] セキュリティミドルウェア動作確認
- [ ] ログ監視アラート設定
- [ ] 緊急時対応手順確立

## 関連PBI
- **前提条件**: PBI-SEC-A（認証基盤）、PBI-SEC-B（通信基盤）
- **依存PBI**: なし
- **後続PBI**: PBI-SEC-D（監査ログとの統合）

## リスクと軽減策

### 主要リスク
1. **パフォーマンス影響** → 段階的実装と詳細な監視
2. **既存機能への影響** → 包括的な回帰テスト
3. **レート制限によるUX悪化** → 適切な制限値設定と明確なエラーメッセージ

### 軽減策
- A/Bテストによる段階的ロールアウト
- リアルタイム監視とアラート設定
- ユーザビリティテストによるUX確認
- フォールバック機能の準備