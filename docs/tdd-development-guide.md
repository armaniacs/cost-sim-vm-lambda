# TDD開発ガイドライン

## t_wada流TDD実践方法

このプロジェクトでは、t_wada氏が提唱するTDD（Test-Driven Development）の原則に従って開発を進めます。

## TDDサイクル: Red → Green → Refactor

### 1. Red Phase（失敗するテストを書く）
- **目的**: 実装すべき機能の仕様を明確化
- **実践方法**:
  - まだ存在しないクラス・メソッドをimportするテストを書く
  - 期待する振る舞いを表現したアサーションを書く
  - テストを実行して失敗することを確認

```python
# 例: Redフェーズのテスト
def test_lambda_calculator_initialization():
    """LambdaCalculatorが初期化できること"""
    calculator = LambdaCalculator()  # まだ存在しない
    assert calculator is not None
```

### 2. Green Phase（テストを通す最小実装）
- **目的**: テストを通すための最小限の実装
- **実践方法**:
  - テストが通る最小限のコードのみ書く
  - 美しいコードは後回し
  - まずは動作することを優先

```python
# 例: Greenフェーズの実装
class LambdaCalculator:
    def __init__(self):
        pass  # 最小限の実装
```

### 3. Refactor Phase（コード改善）
- **目的**: テストが通った状態でコード品質を向上
- **実践方法**:
  - DRY原則の適用
  - 可読性向上
  - パフォーマンス最適化
  - 常にテストが通ることを確認

## プロジェクト固有のTDDルール

### テストファイル構成
```
tests/
├── unit/           # 単体テスト
├── integration/    # 統合テスト  
├── e2e/           # E2Eテスト
└── fixtures/      # テストデータ
```

### テスト命名規則
- テストクラス: `TestClassName`
- テストメソッド: `test_specific_behavior`
- 日本語でも可: `test_lambda料金計算_無料枠適用`

### テストマーカー使用
```python
@pytest.mark.unit
def test_lambda_calculation():
    """単体テスト用マーカー"""
    pass

@pytest.mark.integration
def test_api_endpoint():
    """統合テスト用マーカー"""
    pass

@pytest.mark.slow
def test_heavy_computation():
    """重いテスト用マーカー"""
    pass
```

## 品質ゲート

### 必須条件
- **テストカバレッジ**: 80%以上
- **全テスト成功**: 失敗テストなし
- **リントエラー**: 0件
- **型チェックエラー**: 0件

### 実行コマンド
```bash
# 全テスト実行 + カバレッジ
pytest tests/ --cov=app --cov-report=term-missing

# 特定マーカーのテストのみ
pytest -m unit
pytest -m "not slow"

# コード品質チェック
flake8 app/ tests/
black --check app/ tests/
isort --check-only app/ tests/
mypy app/
```

## TDD実践パターン

### 1. 三角測量（Triangulation）
複数のテストケースで同じメソッドをテストし、実装を確実にする。

```python
def test_calculate_request_charges_case1():
    # ケース1: 100万回実行
    assert calculator.calculate_request_charges(config1) == 0.0

def test_calculate_request_charges_case2():
    # ケース2: 200万回実行
    assert calculator.calculate_request_charges(config2) == 0.20
```

### 2. 仮実装（Fake It）
まずは定数を返す実装から開始。

```python
# 最初の実装
def calculate_request_charges(self, config):
    return 0.20  # 仮実装

# リファクタ後
def calculate_request_charges(self, config):
    return (config.executions - 1_000_000) * 0.20 / 1_000_000
```

### 3. 明白な実装（Obvious Implementation）
簡単な実装は直接実装する。

## プロジェクト固有の考慮事項

### Lambda料金計算の特徴
- 無料枠の適用有無
- メモリサイズとGB-秒の計算
- リクエスト料金と計算料金の分離

### テストデータ管理
```python
# conftest.pyでのフィクスチャ定義
@pytest.fixture
def sample_lambda_config():
    return LambdaConfig(
        memory_mb=512,
        execution_time_seconds=10,
        monthly_executions=1_000_000,
        include_free_tier=True
    )
```

### モック使用指針
- 外部API呼び出しのモック
- 重い計算処理のモック
- 時間依存処理のモック

```python
@pytest.mark.unit
def test_with_mock(mocker):
    # pytest-mockを使用
    mock_api = mocker.patch('app.external_api.call')
    mock_api.return_value = {'rate': 150}
    
    result = calculator.convert_currency(100)
    assert result == 15000
```

## 継続的改善

### リファクタリングチェックリスト
- [ ] 重複コードの除去
- [ ] メソッドの単一責任確保
- [ ] 適切な名前付け
- [ ] 適切なコメント追加
- [ ] パフォーマンス最適化

### TDDメトリクス追跡
- テスト実行時間
- カバレッジ率の推移
- 赤→緑→リファクタのサイクル時間
- テスト失敗率

この原則に従って、各PBIの実装を進めていきます。