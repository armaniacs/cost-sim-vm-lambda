# PBI12: 履歴管理・分析機能

## 概要
計算シナリオの保存・読み込み、履歴管理、コスト推移分析、使用パターン推奨機能を実装する。

## 背景・課題
- **現在の課題**: 計算結果が保存されず、毎回同じ設定を入力する必要がある
- **ビジネス価値**: 長期的なコスト傾向の分析と効率的な意思決定支援
- **ユーザー影響**: 計算の再現性と分析機能による戦略的判断の支援

## 機能要件

### 主要機能
1. **計算シナリオの保存・読み込み**
   - 設定の名前付き保存
   - 保存されたシナリオの一覧表示
   - ワンクリックでの設定復元
   - シナリオの編集・削除

2. **履歴管理機能**
   - 全計算結果の自動保存
   - 履歴の検索・フィルタリング
   - 履歴からの設定復元
   - 履歴の詳細表示

3. **分析機能**
   - 時系列でのコスト推移分析
   - プロバイダー別コスト変化
   - ブレークイーブンポイントの推移
   - 分析結果の可視化

4. **推奨機能**
   - 類似シナリオの自動検出
   - 使用パターンの分析
   - 最適化提案の生成
   - コスト削減の提案

## 技術要件

### データベース設計
```sql
-- 計算シナリオテーブル
CREATE TABLE calculation_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    lambda_config JSON NOT NULL,
    vm_configs JSON NOT NULL,
    execution_range JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 計算履歴テーブル
CREATE TABLE calculation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER REFERENCES calculation_scenarios(id),
    calculation_config JSON NOT NULL,
    calculation_result JSON NOT NULL,
    pricing_snapshot JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ユーザーセッションテーブル（将来的な拡張用）
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_scenarios_created_at ON calculation_scenarios(created_at);
CREATE INDEX idx_history_created_at ON calculation_history(created_at);
CREATE INDEX idx_history_scenario_id ON calculation_history(scenario_id);
```

### アーキテクチャ設計
```
app/
├── models/
│   ├── scenario.py             # シナリオモデル
│   ├── calculation_history.py  # 履歴モデル
│   └── user_session.py         # セッションモデル
├── services/
│   ├── scenario_service.py     # シナリオ管理サービス
│   ├── history_service.py      # 履歴管理サービス
│   ├── analysis_service.py     # 分析サービス
│   └── recommendation_service.py # 推奨サービス
├── database/
│   ├── database.py             # データベース接続
│   └── migrations/             # データベースマイグレーション
└── static/
    ├── js/
    │   ├── scenario-manager.js  # シナリオ管理UI
    │   ├── history-viewer.js    # 履歴表示UI
    │   └── analysis-charts.js   # 分析チャート
    └── css/
        └── history-analysis.css # 履歴・分析UI CSS
```

## 実装計画

### Phase 1: 基本的なシナリオ保存・読み込み機能 (Sprint 1)

#### 実装内容
1. **データベース初期化**
   ```python
   # app/database/database.py
   import sqlite3
   from contextlib import contextmanager
   
   class Database:
       def __init__(self, db_path: str = "app.db"):
           self.db_path = db_path
           self.init_database()
       
       @contextmanager
       def get_connection(self):
           conn = sqlite3.connect(self.db_path)
           try:
               yield conn
           finally:
               conn.close()
   ```

2. **シナリオモデル**
   ```python
   # app/models/scenario.py
   from dataclasses import dataclass
   from datetime import datetime
   from typing import Optional
   
   @dataclass
   class Scenario:
       id: Optional[int]
       name: str
       description: Optional[str]
       lambda_config: dict
       vm_configs: list
       execution_range: dict
       created_at: datetime
       updated_at: datetime
   ```

3. **シナリオサービス**
   ```python
   # app/services/scenario_service.py
   class ScenarioService:
       def save_scenario(self, scenario: Scenario) -> int:
           # シナリオを DB に保存
           
       def load_scenario(self, scenario_id: int) -> Optional[Scenario]:
           # シナリオを DB から読み込み
           
       def list_scenarios(self) -> List[Scenario]:
           # シナリオ一覧を取得
           
       def delete_scenario(self, scenario_id: int) -> bool:
           # シナリオを削除
   ```

4. **シナリオ管理UI**
   ```html
   <!-- シナリオ保存・読み込みUI -->
   <div class="scenario-management">
       <div class="scenario-actions">
           <button class="btn btn-primary" onclick="saveScenario()">
               <i class="bi bi-save"></i> シナリオを保存
           </button>
           <button class="btn btn-secondary" onclick="loadScenario()">
               <i class="bi bi-folder-open"></i> シナリオを読み込み
           </button>
       </div>
       <div class="saved-scenarios">
           <select class="form-select" id="scenarioSelect">
               <option value="">保存されたシナリオを選択</option>
           </select>
           <button class="btn btn-danger btn-sm" onclick="deleteScenario()">
               <i class="bi bi-trash"></i>
           </button>
       </div>
   </div>
   ```

#### 受け入れ基準
- [ ] シナリオに名前を付けて保存できる
- [ ] 保存されたシナリオを一覧表示できる
- [ ] 保存されたシナリオを読み込んで設定を復元できる
- [ ] 不要なシナリオを削除できる

### Phase 2: 履歴管理と検索機能 (Sprint 2)

#### 実装内容
1. **履歴モデル**
   ```python
   # app/models/calculation_history.py
   @dataclass
   class CalculationHistory:
       id: Optional[int]
       scenario_id: Optional[int]
       calculation_config: dict
       calculation_result: dict
       pricing_snapshot: dict
       created_at: datetime
   ```

2. **履歴サービス**
   ```python
   # app/services/history_service.py
   class HistoryService:
       def save_calculation(self, config: dict, result: dict, 
                          pricing_snapshot: dict) -> int:
           # 計算結果を履歴として保存
           
       def search_history(self, filters: dict) -> List[CalculationHistory]:
           # 履歴を検索
           
       def get_history_by_id(self, history_id: int) -> Optional[CalculationHistory]:
           # 特定の履歴を取得
           
       def delete_history(self, history_id: int) -> bool:
           # 履歴を削除
   ```

3. **履歴表示UI**
   ```html
   <!-- 履歴管理UI -->
   <div class="tab-content">
       <div class="tab-pane" id="history">
           <div class="history-search">
               <input type="text" class="form-control" 
                      placeholder="履歴を検索" id="historySearch">
               <div class="date-range">
                   <input type="date" class="form-control" id="dateFrom">
                   <span>〜</span>
                   <input type="date" class="form-control" id="dateTo">
               </div>
               <button class="btn btn-primary" onclick="searchHistory()">
                   <i class="bi bi-search"></i> 検索
               </button>
           </div>
           <div class="history-list">
               <div class="history-item" onclick="loadHistoryItem(123)">
                   <div class="history-header">
                       <span class="history-date">2025-07-14 10:30</span>
                       <span class="history-result">$45.60</span>
                   </div>
                   <div class="history-config">
                       Lambda: 512MB, 10s, 1M回/月
                   </div>
               </div>
           </div>
       </div>
   </div>
   ```

#### 受け入れ基準
- [ ] 計算結果が自動的に履歴として保存される
- [ ] 履歴を日付範囲で検索できる
- [ ] 履歴をテキストで検索できる
- [ ] 履歴をクリックして詳細を確認できる
- [ ] 履歴から設定を復元できる

### Phase 3: 分析機能と可視化 (Sprint 3)

#### 実装内容
1. **分析サービス**
   ```python
   # app/services/analysis_service.py
   class AnalysisService:
       def analyze_cost_trends(self, scenario_id: int, 
                             period: str = "30d") -> dict:
           # コスト推移分析
           return {
               'trend': 'increasing',
               'rate': 0.15,  # 15% increase
               'period': period,
               'data_points': [
                   {'date': '2025-06-15', 'cost': 40.5},
                   {'date': '2025-07-15', 'cost': 46.6}
               ]
           }
       
       def analyze_breakeven_changes(self, scenario_id: int) -> dict:
           # ブレークイーブンポイントの変化分析
           return {
               'current_breakeven': 1500000,
               'trend': 'decreasing',
               'change_rate': -0.05,
               'historical_points': [
                   {'date': '2025-06-15', 'breakeven': 1600000},
                   {'date': '2025-07-15', 'breakeven': 1500000}
               ]
           }
       
       def generate_insights(self, scenario_id: int) -> List[dict]:
           # 分析結果に基づく洞察生成
           return [
               {
                   'type': 'cost_increase',
                   'message': 'AWS Lambda のコストが過去30日間で15%上昇しています',
                   'severity': 'warning',
                   'recommendation': 'Google Cloud への移行を検討してください'
               }
           ]
   ```

2. **分析可視化UI**
   ```html
   <!-- 分析タブUI -->
   <div class="tab-content">
       <div class="tab-pane" id="analysis">
           <div class="analysis-controls">
               <select class="form-select" id="analysisScenario">
                   <option value="">分析対象シナリオを選択</option>
               </select>
               <select class="form-select" id="analysisPeriod">
                   <option value="7d">過去7日間</option>
                   <option value="30d" selected>過去30日間</option>
                   <option value="90d">過去90日間</option>
               </select>
           </div>
           <div class="analysis-charts">
               <div class="chart-container">
                   <h5>コスト推移</h5>
                   <canvas id="trendChart"></canvas>
               </div>
               <div class="chart-container">
                   <h5>ブレークイーブンポイント変化</h5>
                   <canvas id="breakevenChart"></canvas>
               </div>
           </div>
           <div class="analysis-insights">
               <div class="insight-card warning">
                   <h5><i class="bi bi-exclamation-triangle"></i> 注意</h5>
                   <p>AWS Lambda のコストが過去30日間で15%上昇しています</p>
                   <small>Google Cloud への移行を検討してください</small>
               </div>
           </div>
       </div>
   </div>
   ```

#### 受け入れ基準
- [ ] 同一シナリオのコスト推移をグラフで確認できる
- [ ] ブレークイーブンポイントの変化を可視化できる
- [ ] 分析結果に基づく洞察が提供される
- [ ] 分析期間を選択できる

### Phase 4: 推奨機能 (Sprint 4)

#### 実装内容
1. **推奨サービス**
   ```python
   # app/services/recommendation_service.py
   class RecommendationService:
       def find_similar_scenarios(self, current_config: dict) -> List[Scenario]:
           # 類似シナリオの検索
           
       def suggest_optimizations(self, scenario_id: int) -> List[dict]:
           # 最適化提案
           return [
               {
                   'type': 'provider_switch',
                   'message': 'Google Cloud に切り替えることで月額 $50 削減可能',
                   'current_cost': 150.00,
                   'optimized_cost': 100.00,
                   'savings': 50.00,
                   'confidence': 0.85
               },
               {
                   'type': 'instance_optimization',
                   'message': 'メモリサイズを512MBから256MBに変更することで30%削減',
                   'savings': 45.00,
                   'confidence': 0.90
               }
           ]
       
       def detect_usage_patterns(self, user_session: str) -> dict:
           # 使用パターンの検出
           return {
               'frequent_configs': [
                   {'memory': 512, 'execution_time': 10, 'frequency': 0.6},
                   {'memory': 1024, 'execution_time': 30, 'frequency': 0.3}
               ],
               'cost_sensitivity': 'high',
               'preferred_providers': ['aws', 'google_cloud']
           }
   ```

2. **推奨UI**
   ```html
   <!-- 推奨タブUI -->
   <div class="tab-content">
       <div class="tab-pane" id="recommendations">
           <div class="recommendation-section">
               <h5>コスト最適化提案</h5>
               <div class="recommendation-card">
                   <div class="recommendation-header">
                       <span class="savings">$50 削減可能</span>
                       <span class="confidence">信頼度: 85%</span>
                   </div>
                   <p>Google Cloud に切り替えることで月額 $50 削減可能</p>
                   <button class="btn btn-primary btn-sm" onclick="applyRecommendation()">
                       適用
                   </button>
               </div>
           </div>
           <div class="recommendation-section">
               <h5>類似シナリオ</h5>
               <div class="similar-scenarios">
                   <div class="similar-scenario" onclick="loadSimilarScenario(456)">
                       <span class="scenario-name">本番環境設定</span>
                       <span class="similarity">類似度: 92%</span>
                   </div>
               </div>
           </div>
       </div>
   </div>
   ```

#### 受け入れ基準
- [ ] 現在の設定に基づく最適化提案が表示される
- [ ] 類似シナリオが自動検出される
- [ ] 推奨内容をワンクリックで適用できる
- [ ] 使用パターンが分析される

## BDD受け入れ基準

### シナリオ1: シナリオ保存・読み込み
```gherkin
Given ユーザーがコスト計算の設定を完了している
When "シナリオを保存" ボタンをクリックする
And シナリオ名に "本番環境設定" を入力する
And 保存ボタンをクリックする
Then 設定がデータベースに保存される
And 保存されたシナリオが一覧に表示される
And 保存されたシナリオを選択して読み込める
And 読み込んだ設定で正常に計算が実行される
```

### シナリオ2: 履歴管理と検索
```gherkin
Given 複数の計算履歴が保存されている
When 履歴タブを開く
And 日付範囲を "2025-07-01" から "2025-07-15" に設定する
And 検索ボタンをクリックする
Then 指定期間内の計算履歴が表示される
And 履歴をクリックして詳細を確認できる
And 履歴から設定を復元できる
And 復元した設定で正常に計算が実行される
```

### シナリオ3: 分析機能
```gherkin
Given 同一シナリオの計算履歴が複数存在する
When 分析タブを開く
And 分析対象シナリオを選択する
And 分析期間を "過去30日間" に設定する
Then コスト推移グラフが表示される
And ブレークイーブンポイントの変化が可視化される
And 分析結果に基づく洞察が提供される
And 洞察には具体的な改善提案が含まれる
```

### シナリオ4: 推奨機能
```gherkin
Given 現在の計算設定がある
When 推奨タブを開く
Then 現在の設定に基づく最適化提案が表示される
And 類似シナリオが自動検出される
And 推奨内容の信頼度が表示される
When 推奨内容の "適用" ボタンをクリックする
Then 設定が自動的に更新される
And 更新された設定で計算が実行される
```

## セキュリティ考慮

### データベースセキュリティ
- **SQL インジェクション対策**: パラメータ化クエリの使用
- **データ暗号化**: 機密データの暗号化保存
- **アクセス制御**: 適切な権限管理

### アプリケーションセキュリティ
- **XSS 攻撃対策**: 入力データのサニタイズ
- **CSRF 対策**: トークンベースの認証
- **セッション管理**: セキュアなセッション管理

## テスト戦略

### 単体テスト
```python
# tests/unit/test_scenario_service.py
def test_save_scenario():
    service = ScenarioService()
    scenario = Scenario(
        name="テストシナリオ",
        lambda_config={"memory_mb": 512},
        vm_configs=[],
        execution_range={"min": 0, "max": 1000000}
    )
    scenario_id = service.save_scenario(scenario)
    assert scenario_id > 0
    
    loaded_scenario = service.load_scenario(scenario_id)
    assert loaded_scenario.name == "テストシナリオ"
```

### 統合テスト
```python
# tests/integration/test_history_integration.py
def test_calculation_history_integration():
    # 計算実行 → 履歴保存 → 履歴検索の一連のテスト
    pass
```

### E2Eテスト
```python
# tests/e2e/test_scenario_management.py
def test_scenario_save_and_load_e2e():
    # シナリオ保存から読み込みまでのE2Eテスト
    pass
```

## パフォーマンス考慮

### データベース最適化
- **インデックス**: 検索頻度の高いカラムにインデックス設定
- **クエリ最適化**: 効率的なクエリ設計
- **ページネーション**: 大量データの効率的な表示

### キャッシュ戦略
- **メモリキャッシュ**: 頻繁にアクセスされるデータのキャッシュ
- **ブラウザキャッシュ**: 静的リソースのキャッシュ

## 成功指標

### 機能指標
- [ ] シナリオ保存成功率 > 99%
- [ ] 履歴検索応答時間 < 2秒
- [ ] 分析結果生成時間 < 5秒
- [ ] 推奨機能の適用成功率 > 95%

### 品質指標
- [ ] テストカバレッジ > 85%
- [ ] データベース整合性 100%
- [ ] UI応答性 < 1秒

## 完了定義 (DoD)

### 技術的完了条件
- [ ] 全てのPhaseが実装されている
- [ ] データベースが正常に動作する
- [ ] 全てのAPIが実装されている
- [ ] UIが正常に動作する

### 品質保証
- [ ] 全てのテストが合格する
- [ ] セキュリティチェックが完了している
- [ ] パフォーマンステストが合格する
- [ ] 全てのBDD受け入れ基準が満たされる

### ユーザー体験
- [ ] シナリオ保存・読み込みが直感的に操作できる
- [ ] 履歴検索が効率的に実行できる
- [ ] 分析結果が分かりやすく表示される
- [ ] 推奨機能が有用な提案を提供する

---

**PBI12 見積もり**: 13ストーリーポイント (4 Sprint)  
**依存関係**: PBI01-PBI10 (基本機能)  
**優先度**: 中  
**実装開始日**: PBI11完了後