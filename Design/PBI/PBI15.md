# PBI15: コスト最適化レポート機能

## 概要
包括的なコスト分析、自動最適化提案、レポート生成、自動化機能を統合したコスト最適化レポート機能を実装する。

## 背景・課題
- **現在の課題**: 計算結果の分析が個別で断片的、長期的な最適化戦略が提示されない
- **ビジネス価値**: 体系的なコスト最適化と継続的な改善の実現
- **ユーザー影響**: 戦略的なコスト管理と自動化による効率化

## 機能要件

### 主要機能
1. **自動最適化提案**
   - 現在の設定に基づく改善提案
   - 複数の最適化軸での分析（コスト、パフォーマンス、可用性）
   - 実装の優先順位付け
   - ROI計算とリスク評価

2. **リソース使用率分析**
   - 過去のデータに基づく使用率分析
   - 無駄なリソースの特定
   - 使用パターンの分析
   - 予測分析

3. **適正サイズ推奨**
   - 最適なインスタンスサイズの推奨
   - オーバープロビジョニング/アンダープロビジョニングの検出
   - 段階的な移行計画
   - コスト・パフォーマンス最適化

4. **包括的なレポート生成**
   - PDF/Excel形式でのレポート出力
   - 経営層向けサマリー
   - 技術者向け詳細レポート
   - 定期的な自動レポート配信

5. **自動化機能**
   - 定期的な自動分析
   - 閾値ベースのアラート
   - 自動レポート配信
   - ダッシュボード機能

## 技術要件

### 分析エンジン
```python
# app/services/cost_analysis_service.py
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans

@dataclass
class AnalysisResult:
    current_cost: float
    historical_trend: dict
    optimization_score: float
    optimization_opportunities: List[dict]
    statistical_summary: dict
    predictions: dict

class CostAnalysisService:
    def __init__(self):
        self.optimization_engine = OptimizationEngine()
        self.prediction_engine = PredictionEngine()
    
    def analyze_cost_trends(self, historical_data: List[dict]) -> dict:
        """コスト傾向分析"""
        costs = [item['total_cost'] for item in historical_data]
        dates = [item['date'] for item in historical_data]
        
        # 線形回帰による傾向分析
        X = np.array(range(len(costs))).reshape(-1, 1)
        y = np.array(costs)
        
        model = LinearRegression()
        model.fit(X, y)
        
        trend_rate = model.coef_[0]
        trend_direction = 'increasing' if trend_rate > 0 else 'decreasing'
        
        # 季節性の検出
        seasonality = self.detect_seasonality(historical_data)
        
        # 異常値の検出
        anomalies = self.detect_cost_anomalies(historical_data)
        
        return {
            'trend_direction': trend_direction,
            'trend_rate': trend_rate,
            'seasonality': seasonality,
            'anomalies': anomalies,
            'variance': np.var(costs),
            'volatility': np.std(costs) / np.mean(costs)
        }
    
    def calculate_optimization_score(self, current_config: dict, 
                                   historical_data: List[dict]) -> float:
        """最適化スコア計算"""
        scores = []
        
        # コスト効率性スコア
        cost_efficiency = self.calculate_cost_efficiency(current_config, historical_data)
        scores.append(cost_efficiency * 0.4)
        
        # リソース利用率スコア
        utilization_score = self.calculate_utilization_score(current_config)
        scores.append(utilization_score * 0.3)
        
        # プロバイダー選択スコア
        provider_score = self.calculate_provider_optimization_score(current_config)
        scores.append(provider_score * 0.2)
        
        # 設定の適切性スコア
        configuration_score = self.calculate_configuration_score(current_config)
        scores.append(configuration_score * 0.1)
        
        return sum(scores)
    
    def detect_optimization_opportunities(self, current_config: dict, 
                                        historical_data: List[dict]) -> List[dict]:
        """最適化機会の検出"""
        opportunities = []
        
        # 1. インスタンスサイズ最適化
        sizing_opportunity = self.analyze_instance_sizing(current_config, historical_data)
        if sizing_opportunity['potential_savings'] > 0:
            opportunities.append({
                'type': 'instance_sizing',
                'category': 'コンピューティング最適化',
                'title': 'インスタンスサイズ最適化',
                'description': sizing_opportunity['description'],
                'current_config': sizing_opportunity['current_config'],
                'recommended_config': sizing_opportunity['recommended_config'],
                'potential_savings': sizing_opportunity['potential_savings'],
                'confidence': sizing_opportunity['confidence'],
                'implementation_effort': sizing_opportunity['implementation_effort'],
                'risk_level': sizing_opportunity['risk_level'],
                'expected_roi': sizing_opportunity['expected_roi']
            })
        
        # 2. プロバイダー最適化
        provider_opportunity = self.analyze_provider_optimization(current_config)
        if provider_opportunity['potential_savings'] > 0:
            opportunities.append({
                'type': 'provider_optimization',
                'category': 'プロバイダー最適化',
                'title': 'プロバイダー変更による最適化',
                'description': provider_opportunity['description'],
                'current_provider': provider_opportunity['current_provider'],
                'recommended_provider': provider_opportunity['recommended_provider'],
                'potential_savings': provider_opportunity['potential_savings'],
                'confidence': provider_opportunity['confidence'],
                'implementation_effort': provider_opportunity['implementation_effort'],
                'risk_level': provider_opportunity['risk_level'],
                'expected_roi': provider_opportunity['expected_roi']
            })
        
        # 3. リージョン最適化
        region_opportunity = self.analyze_region_optimization(current_config, historical_data)
        if region_opportunity['potential_savings'] > 0:
            opportunities.append({
                'type': 'region_optimization',
                'category': 'リージョン最適化',
                'title': 'リージョン変更による最適化',
                'description': region_opportunity['description'],
                'current_region': region_opportunity['current_region'],
                'recommended_region': region_opportunity['recommended_region'],
                'potential_savings': region_opportunity['potential_savings'],
                'confidence': region_opportunity['confidence'],
                'implementation_effort': region_opportunity['implementation_effort'],
                'risk_level': region_opportunity['risk_level'],
                'expected_roi': region_opportunity['expected_roi']
            })
        
        # 4. 実行頻度最適化
        frequency_opportunity = self.analyze_execution_frequency(current_config, historical_data)
        if frequency_opportunity['potential_savings'] > 0:
            opportunities.append({
                'type': 'execution_frequency',
                'category': '実行最適化',
                'title': '実行頻度最適化',
                'description': frequency_opportunity['description'],
                'current_frequency': frequency_opportunity['current_frequency'],
                'recommended_frequency': frequency_opportunity['recommended_frequency'],
                'potential_savings': frequency_opportunity['potential_savings'],
                'confidence': frequency_opportunity['confidence'],
                'implementation_effort': frequency_opportunity['implementation_effort'],
                'risk_level': frequency_opportunity['risk_level'],
                'expected_roi': frequency_opportunity['expected_roi']
            })
        
        # 優先度スコア計算
        for opportunity in opportunities:
            opportunity['priority_score'] = self.calculate_priority_score(opportunity)
        
        # 優先度順にソート
        opportunities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return opportunities
```

### レポート生成エンジン
```python
# app/services/report_generator.py
from jinja2 import Template
from weasyprint import HTML
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
import base64
import io

class ReportGenerator:
    def __init__(self):
        self.template_loader = TemplateLoader()
        self.chart_generator = ChartGenerator()
    
    def generate_cost_optimization_report(self, analysis_data: dict, 
                                        report_type: str = "comprehensive") -> dict:
        """コスト最適化レポート生成"""
        
        if report_type == "executive":
            return self.generate_executive_report(analysis_data)
        elif report_type == "technical":
            return self.generate_technical_report(analysis_data)
        elif report_type == "financial":
            return self.generate_financial_report(analysis_data)
        else:
            return self.generate_comprehensive_report(analysis_data)
    
    def generate_executive_report(self, analysis_data: dict) -> dict:
        """経営層向けレポート"""
        
        # キーメトリクス
        key_metrics = {
            'current_monthly_cost': analysis_data['current_cost'],
            'potential_savings': analysis_data['total_potential_savings'],
            'optimization_score': analysis_data['optimization_score'],
            'payback_period': analysis_data.get('payback_period', '3ヶ月'),
            'roi_12_months': analysis_data.get('roi_12_months', 250)
        }
        
        # 主要な発見事項
        key_findings = analysis_data.get('key_findings', [])[:5]
        
        # 最優先推奨事項
        top_recommendations = analysis_data.get('optimization_opportunities', [])[:3]
        
        # チャート生成
        charts = [
            self.chart_generator.create_cost_trend_chart(analysis_data['historical_data']),
            self.chart_generator.create_savings_opportunity_chart(analysis_data['optimization_opportunities']),
            self.chart_generator.create_optimization_score_chart(analysis_data['optimization_score'])
        ]
        
        return {
            'report_type': 'executive',
            'title': 'コスト最適化 - 経営サマリー',
            'generated_at': datetime.now().isoformat(),
            'key_metrics': key_metrics,
            'key_findings': key_findings,
            'top_recommendations': top_recommendations,
            'charts': charts,
            'summary': self.generate_executive_summary(key_metrics, key_findings)
        }
    
    def generate_technical_report(self, analysis_data: dict) -> dict:
        """技術者向け詳細レポート"""
        
        return {
            'report_type': 'technical',
            'title': 'コスト最適化 - 技術詳細レポート',
            'generated_at': datetime.now().isoformat(),
            'detailed_analysis': analysis_data['detailed_analysis'],
            'all_opportunities': analysis_data['optimization_opportunities'],
            'implementation_roadmap': self.generate_implementation_roadmap(
                analysis_data['optimization_opportunities']
            ),
            'technical_considerations': analysis_data.get('technical_considerations', []),
            'performance_impact': analysis_data.get('performance_impact', {}),
            'risk_assessment': analysis_data.get('risk_assessment', {}),
            'monitoring_recommendations': analysis_data.get('monitoring_recommendations', [])
        }
    
    def export_to_pdf(self, report_data: dict, template_name: str = None) -> bytes:
        """PDF形式でレポートをエクスポート"""
        
        if template_name is None:
            template_name = f"{report_data['report_type']}_report.html"
        
        template = self.template_loader.get_template(template_name)
        html_content = template.render(report_data)
        
        # WeasyPrintでPDF生成
        html_doc = HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        return pdf_bytes
    
    def export_to_excel(self, report_data: dict) -> bytes:
        """Excel形式でレポートをエクスポート"""
        
        wb = Workbook()
        
        # サマリーシート
        summary_sheet = wb.active
        summary_sheet.title = "サマリー"
        self.populate_summary_sheet(summary_sheet, report_data)
        
        # 詳細分析シート
        analysis_sheet = wb.create_sheet("詳細分析")
        self.populate_analysis_sheet(analysis_sheet, report_data)
        
        # 最適化提案シート
        recommendations_sheet = wb.create_sheet("最適化提案")
        self.populate_recommendations_sheet(recommendations_sheet, report_data)
        
        # チャートシート
        charts_sheet = wb.create_sheet("チャート")
        self.populate_charts_sheet(charts_sheet, report_data)
        
        # バイナリデータとして出力
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return output.read()
```

### 自動化サービス
```python
# app/services/automation_service.py
from celery import Celery
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class AutomationService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.cost_analysis_service = CostAnalysisService()
        self.report_generator = ReportGenerator()
        self.notification_service = NotificationService()
    
    def schedule_periodic_analysis(self, user_id: str, schedule_config: dict) -> None:
        """定期的な分析のスケジュール"""
        
        schedule_type = schedule_config.get('type', 'weekly')
        
        if schedule_type == 'daily':
            self.scheduler.add_job(
                self.run_automated_analysis,
                'cron',
                hour=schedule_config.get('hour', 9),
                minute=schedule_config.get('minute', 0),
                args=[user_id, schedule_config]
            )
        elif schedule_type == 'weekly':
            self.scheduler.add_job(
                self.run_automated_analysis,
                'cron',
                day_of_week=schedule_config.get('day_of_week', 0),  # Monday
                hour=schedule_config.get('hour', 9),
                minute=schedule_config.get('minute', 0),
                args=[user_id, schedule_config]
            )
        elif schedule_type == 'monthly':
            self.scheduler.add_job(
                self.run_automated_analysis,
                'cron',
                day=schedule_config.get('day', 1),
                hour=schedule_config.get('hour', 9),
                minute=schedule_config.get('minute', 0),
                args=[user_id, schedule_config]
            )
    
    def setup_cost_alerts(self, user_id: str, alert_config: dict) -> None:
        """コストアラートの設定"""
        
        # 閾値アラート
        if 'cost_threshold' in alert_config:
            self.scheduler.add_job(
                self.check_cost_threshold,
                'interval',
                hours=alert_config.get('check_interval_hours', 1),
                args=[user_id, alert_config['cost_threshold']]
            )
        
        # 異常検出アラート
        if alert_config.get('anomaly_detection', False):
            self.scheduler.add_job(
                self.check_cost_anomalies,
                'interval',
                hours=alert_config.get('anomaly_check_interval_hours', 6),
                args=[user_id, alert_config.get('anomaly_sensitivity', 0.8)]
            )
        
        # 最適化機会アラート
        if alert_config.get('optimization_alerts', False):
            self.scheduler.add_job(
                self.check_optimization_opportunities,
                'cron',
                hour=alert_config.get('optimization_check_hour', 10),
                args=[user_id, alert_config.get('min_savings_threshold', 100)]
            )
    
    def run_automated_analysis(self, user_id: str, analysis_config: dict) -> dict:
        """自動化された分析の実行"""
        
        # 最新データを取得
        latest_data = self.get_latest_user_data(user_id)
        
        # 分析実行
        analysis_result = self.cost_analysis_service.run_comprehensive_analysis(
            latest_data, analysis_config
        )
        
        # レポート生成
        report_type = analysis_config.get('report_type', 'comprehensive')
        report = self.report_generator.generate_cost_optimization_report(
            analysis_result, report_type
        )
        
        # 保存
        self.save_analysis_result(user_id, analysis_result, report)
        
        # 自動配信
        if analysis_config.get('auto_delivery', False):
            self.deliver_report(user_id, report, analysis_config['delivery_settings'])
        
        # アラート確認
        self.check_and_send_alerts(user_id, analysis_result, analysis_config)
        
        return {
            'analysis_result': analysis_result,
            'report': report,
            'timestamp': datetime.now().isoformat()
        }
    
    def deliver_report(self, user_id: str, report: dict, delivery_settings: dict) -> None:
        """レポートの配信"""
        
        delivery_method = delivery_settings.get('method', 'email')
        
        if delivery_method == 'email':
            self.send_email_report(user_id, report, delivery_settings)
        elif delivery_method == 'slack':
            self.send_slack_report(user_id, report, delivery_settings)
        elif delivery_method == 'webhook':
            self.send_webhook_report(user_id, report, delivery_settings)
    
    def create_cost_dashboard(self, user_id: str) -> dict:
        """コスト最適化ダッシュボード生成"""
        
        # 現在の状況
        current_status = self.get_current_cost_status(user_id)
        
        # 最近の傾向
        recent_trends = self.get_recent_cost_trends(user_id)
        
        # アクティブな推奨事項
        active_recommendations = self.get_active_recommendations(user_id)
        
        # アラート
        active_alerts = self.get_active_alerts(user_id)
        
        # スケジュールされたレポート
        scheduled_reports = self.get_scheduled_reports(user_id)
        
        return {
            'dashboard_type': 'cost_optimization',
            'user_id': user_id,
            'generated_at': datetime.now().isoformat(),
            'current_status': current_status,
            'recent_trends': recent_trends,
            'active_recommendations': active_recommendations,
            'active_alerts': active_alerts,
            'scheduled_reports': scheduled_reports,
            'quick_actions': self.get_quick_actions(user_id)
        }
```

## 実装計画

### Phase 1: 基本的な分析機能 (Sprint 1)

#### 実装内容
1. **過去データの統計的分析**
   - 平均、分散、トレンド分析
   - 基本的な異常検出
   - 使用パターン分析

2. **基本的な最適化機会検出**
   - 明らかな過剰リソース検出
   - 基本的な提案生成
   - 節約可能額の計算

3. **分析結果表示UI**
   - 統計サマリー表示
   - 基本的なチャート
   - 最適化提案の一覧

#### 受け入れ基準
- [ ] 履歴データから基本的な統計情報を算出できる
- [ ] 明らかな最適化機会を検出できる
- [ ] 分析結果が分かりやすく表示される
- [ ] 節約可能額が正確に計算される

### Phase 2: 最適化提案機能 (Sprint 2)

#### 実装内容
1. **高度な最適化アルゴリズム**
   - 機械学習による予測
   - 複数軸での最適化
   - ROI計算

2. **優先度付き提案生成**
   - リスク評価
   - 実装難易度評価
   - 優先度スコア計算

3. **シミュレーション機能**
   - 提案適用時の影響予測
   - What-if分析
   - リスク評価

#### 受け入れ基準
- [ ] 複数の最適化軸で提案が生成される
- [ ] 提案が優先度順に表示される
- [ ] ROIとリスクが適切に評価される
- [ ] シミュレーション結果が信頼できる

### Phase 3: レポート生成機能 (Sprint 3)

#### 実装内容
1. **包括的なレポート生成**
   - 経営層向けサマリー
   - 技術者向け詳細レポート
   - 財務分析レポート

2. **エクスポート機能**
   - PDF形式でのエクスポート
   - Excel形式でのエクスポート
   - チャートとグラフの自動生成

3. **カスタマイズ機能**
   - レポートテンプレート
   - カスタムメトリクス
   - ブランディング対応

#### 受け入れ基準
- [ ] 複数のレポート形式が生成できる
- [ ] PDF/Excel形式でエクスポートできる
- [ ] レポートが実用的で分かりやすい
- [ ] カスタマイズが可能である

### Phase 4: 自動化機能 (Sprint 4)

#### 実装内容
1. **定期的な自動分析**
   - スケジュール設定
   - 自動実行
   - 結果の保存

2. **アラート機能**
   - 閾値ベースのアラート
   - 異常検出アラート
   - 最適化機会アラート

3. **自動配信機能**
   - メール配信
   - Slack通知
   - Webhook連携

4. **ダッシュボード機能**
   - リアルタイム状況表示
   - 傾向分析
   - アクション管理

#### 受け入れ基準
- [ ] 定期的な自動分析が正常に実行される
- [ ] 適切なタイミングでアラートが送信される
- [ ] 自動配信が設定通りに動作する
- [ ] ダッシュボードが有用な情報を提供する

## BDD受け入れ基準

### シナリオ1: 分析結果の生成
```gherkin
Given 過去3ヶ月間の計算履歴が存在する
When コスト最適化分析を実行する
Then 現在のコスト状況が分析される
And 最適化機会が検出される
And 最適化スコアが算出される
And 分析結果がダッシュボードに表示される
And 分析結果に信頼性指標が含まれる
```

### シナリオ2: 最適化提案の生成
```gherkin
Given 分析結果が生成されている
When 最適化提案を生成する
Then 複数の最適化提案が生成される
And 各提案に節約額が表示される
And 実装難易度とリスクレベルが表示される
And 提案が優先度順に並べられる
And 各提案にROI情報が含まれる
```

### シナリオ3: レポートの生成・エクスポート
```gherkin
Given 分析結果と最適化提案が準備されている
When レポート生成を実行する
And レポートタイプを「経営サマリー」に選択する
Then 経営層向けのレポートが生成される
And PDF形式でエクスポートできる
And Excel形式でエクスポートできる
And レポートに実用的な洞察が含まれる
```

### シナリオ4: 自動化機能
```gherkin
Given 週次の自動分析が設定されている
When 設定されたスケジュールに従って自動分析が実行される
Then 最新データで分析が実行される
And 自動レポートが生成される
And 設定された配信先にレポートが送信される
And 重要な変化があった場合はアラートが送信される
```

## セキュリティ考慮

### データ保護
- **分析データの保護**: 機密性の高い分析結果の適切な保護
- **レポートの暗号化**: 生成されたレポートの暗号化
- **アクセス制御**: 適切なアクセス権限の管理

### 自動化のセキュリティ
- **自動配信の認証**: 配信先の認証とセキュリティ
- **API連携のセキュリティ**: Webhook等の外部連携のセキュリティ
- **スケジュール処理の保護**: 自動処理のセキュリティ

## テスト戦略

### 単体テスト
```python
# tests/unit/test_cost_analysis.py
def test_cost_trend_analysis():
    service = CostAnalysisService()
    historical_data = [
        {'date': '2025-06-01', 'total_cost': 100.0},
        {'date': '2025-06-15', 'total_cost': 110.0},
        {'date': '2025-07-01', 'total_cost': 115.0}
    ]
    
    result = service.analyze_cost_trends(historical_data)
    assert result['trend_direction'] == 'increasing'
    assert result['trend_rate'] > 0

def test_optimization_opportunity_detection():
    service = CostAnalysisService()
    current_config = {
        'provider': 'aws',
        'instance_type': 't3.large',
        'total_cost': 200.0
    }
    historical_data = []
    
    opportunities = service.detect_optimization_opportunities(current_config, historical_data)
    assert len(opportunities) >= 0
    for opportunity in opportunities:
        assert 'potential_savings' in opportunity
        assert 'confidence' in opportunity

def test_optimization_score_calculation():
    service = CostAnalysisService()
    current_config = {'total_cost': 150.0}
    historical_data = []
    
    score = service.calculate_optimization_score(current_config, historical_data)
    assert 0 <= score <= 100
```

### 統合テスト
```python
# tests/integration/test_analysis_pipeline.py
def test_full_analysis_pipeline():
    """分析 → 最適化提案 → レポート生成の統合テスト"""
    service = CostAnalysisService()
    report_generator = ReportGenerator()
    
    # 分析実行
    analysis_result = service.run_comprehensive_analysis(sample_data)
    
    # レポート生成
    report = report_generator.generate_cost_optimization_report(
        analysis_result, "comprehensive"
    )
    
    # 結果検証
    assert analysis_result['optimization_score'] > 0
    assert len(analysis_result['optimization_opportunities']) > 0
    assert report['report_type'] == 'comprehensive'
```

### E2Eテスト
```python
# tests/e2e/test_optimization_report_e2e.py
def test_dashboard_to_report_generation_e2e():
    """ダッシュボード → 分析実行 → レポート生成 → エクスポートのE2E"""
    # 1. ダッシュボードアクセス
    # 2. 分析実行
    # 3. 結果表示確認
    # 4. レポート生成
    # 5. エクスポート実行
    # 6. ファイル生成確認
    pass

def test_automated_analysis_e2e():
    """自動分析 → レポート生成 → 配信のE2E"""
    pass
```

## パフォーマンス考慮

### 分析パフォーマンス
- **大容量データ処理**: 効率的なデータ処理アルゴリズム
- **並列処理**: 複数の分析タスクの並列実行
- **キャッシュ**: 計算結果のキャッシュ

### レポート生成パフォーマンス
- **テンプレート最適化**: 効率的なレポート生成
- **チャート生成**: 高速なチャート生成
- **エクスポート最適化**: 大容量ファイルの効率的な生成

## 成功指標

### 機能指標
- [ ] 分析実行時間 < 10秒
- [ ] レポート生成時間 < 30秒
- [ ] 最適化提案の精度 > 85%
- [ ] 自動化機能の成功率 > 99%

### 品質指標
- [ ] テストカバレッジ > 90%
- [ ] 分析結果の信頼性 > 95%
- [ ] レポートの実用性評価 > 4.0/5.0

## 完了定義 (DoD)

### 技術的完了条件
- [ ] 全ての Phase が実装されている
- [ ] 分析エンジンが正確に動作する
- [ ] レポート生成機能が正常に動作する
- [ ] 自動化機能が安定して動作する

### 品質保証
- [ ] 全てのテストが合格する
- [ ] 分析結果の正確性が検証されている
- [ ] レポートの品質が確認されている
- [ ] 全てのBDD受け入れ基準が満たされる

### ユーザー体験
- [ ] 分析結果が分かりやすく表示される
- [ ] 最適化提案が実用的で信頼できる
- [ ] レポートが有用で実用的である
- [ ] 自動化機能が期待通りに動作する

---

**PBI15 見積もり**: 15ストーリーポイント (4 Sprint)  
**依存関係**: PBI11 (リアルタイム料金取得), PBI12 (履歴管理), PBI14 (マルチリージョン対応)  
**優先度**: 高  
**実装開始日**: PBI11-14完了後