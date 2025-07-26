# PBI-I18N-JP: 日本語表示サポート（国際化対応）

## プロダクトバックログアイテム概要

**PBI ID**: I18N-JP  
**タイトル**: 日本語表示サポート（国際化対応）  
**見積もり**: 8ストーリーポイント  
**優先度**: 中（重要な機能拡張）  
**実装タスク**: I18N-01, I18N-02, I18N-03, I18N-04

## ユーザーストーリー

**日本のインフラエンジニア**として、**日本語でのコスト比較シミュレーター**がほしい、なぜなら**母国語で正確にコスト分析を行い、社内での意思決定を効率化したい**から

## ビジネス価値

### 主要価値
- **アクセシビリティ向上**: 日本語ユーザーの利用障壁を除去
- **市場拡大**: 日本市場でのユーザー獲得と利用促進
- **ユーザビリティ向上**: 専門用語の日本語対応で理解度向上
- **意思決定支援**: 日本語での資料作成・報告書作成が容易

### 測定可能な成果
- 日本語ユーザーの利用率: 40%向上
- ユーザー滞在時間: 25%増加
- エラー率（設定ミス等）: 30%削減
- 日本語でのCSV出力活用率: 60%向上

## BDD受け入れシナリオ

### シナリオ1: 言語切り替え機能
```gherkin
Feature: 言語切り替え機能
  As a 日本のインフラエンジニア
  I want UIの表示言語を切り替える機能
  So that 日本語で快適にコスト比較分析を行える

Scenario: ユーザーが英語から日本語に切り替える
  Given コストシミュレーターが英語で表示されている
  When 言語切り替えボタンをクリックする
  And 言語選択ドロップダウンから「日本語」を選択する
  Then 全てのUI要素が日本語で表示される
  And メニュー、ボタン、ラベルが日本語になる
  And 通貨記号が「¥」に変更される
  And 設定値はそのまま保持される
  And ブラウザを再読み込みしても日本語が維持される
```

### シナリオ2: 計算パラメーターの日本語表示
```gherkin
Feature: 計算パラメーター日本語表示
  As a 日本のクラウドアーキテクト
  I want Lambda・VM設定項目を日本語で確認
  So that 設定ミスなく正確にコスト計算を実行できる

Scenario: ユーザーがLambda設定を日本語で入力する
  Given アプリケーションが日本語モードに設定されている
  When Lambda設定画面を表示する
  Then「メモリサイズ(MB)」「実行時間(秒)」などが日本語で表示される
  And 各設定項目に日本語の説明文が表示される
  And プレースホルダーテキストも日本語になる
  And バリデーションエラーメッセージが日本語で表示される
  When 無効な値を入力する
  Then「メモリサイズは128-10240MBの範囲で入力してください」などの日本語エラーが表示される
```

### シナリオ3: グラフ・チャートの日本語対応
```gherkin
Feature: グラフ・チャートの日本語対応
  As a 日本の意思決定者
  I want 分析結果のグラフが日本語で表示される
  So that 社内会議で正確にプレゼンテーションできる

Scenario: コスト比較グラフが日本語で表示される
  Given 日本語モードでコスト計算を完了している
  When グラフが表示される
  Then X軸ラベルが「月間実行回数」と日本語で表示される
  And Y軸ラベルが「月間コスト(円)」と日本語で表示される
  And 凡例が「AWS Lambda」「AWS EC2」などと日本語・英語併記される
  And ツールチップが「月間実行回数: 1,000,000回、コスト: ¥45,600」と日本語で表示される
  And ブレークイーブンポイントが「損益分岐点: 1,500,000回実行時」と表示される
```

### シナリオ4: CSV出力の日本語対応
```gherkin
Feature: CSV出力の日本語対応
  As a 日本のプロジェクトマネージャー
  I want CSV出力が日本語ヘッダーに対応している
  So that 日本語の報告書作成に直接活用できる

Scenario: ユーザーが日本語CSV出力をダウンロードする
  Given 日本語モードでコスト計算結果が表示されている
  When「CSVダウンロード」ボタンをクリックする
  Then CSVファイルがダウンロードされる
  And ファイル名が「コスト比較結果_20250722.csv」形式になる
  And ヘッダー行が「月間実行回数,AWS Lambda(円),AWS EC2(円),Google Cloud(円)」となる
  And 数値フォーマットが日本語表記（カンマ区切り）になる
  And 日付フォーマットが「2025/07/22」形式になる
```

### シナリオ5: エラーメッセージの日本語対応
```gherkin
Feature: エラーメッセージの日本語対応
  As a 日本のシステム管理者
  I want エラーメッセージが分かりやすい日本語で表示される
  So that 問題を迅速に特定・解決できる

Scenario: API接続エラーが日本語で通知される
  Given 日本語モードでアプリケーションを使用している
  When ネットワークエラーによりAPI呼び出しが失敗する
  Then「サーバーとの接続に失敗しました。ネットワーク接続を確認してください。」と表示される
  And エラーの詳細情報も日本語で提供される
  And 解決方法の案内も日本語で表示される
```

## 受け入れ基準

### 機能要件
- [ ] 言語切り替えボタン（日本語⇔英語）がヘッダー部に配置される
- [ ] 全UI要素（ボタン、ラベル、メニュー、フォーム項目）が日本語対応される
- [ ] バリデーションエラーメッセージが適切な日本語で表示される
- [ ] グラフ・チャートの軸ラベル、凡例、ツールチップが日本語対応される
- [ ] CSV出力のヘッダーが日本語になる
- [ ] 通貨表示が円記号（¥）に切り替わる
- [ ] 数値フォーマットが日本のロケール（カンマ区切り）になる
- [ ] 日付フォーマットが日本形式（YYYY/MM/DD）になる

### 非機能要件
- [ ] 言語切り替え応答時間: 1秒以内
- [ ] 翻訳品質: 技術用語の正確性100%
- [ ] ブラウザセッション中の言語設定保持
- [ ] 既存機能への影響なし（回帰テストクリア）
- [ ] レスポンシブデザイン維持

### 国際化要件
- [ ] Unicode（UTF-8）完全対応
- [ ] 文字化け・表示崩れなし
- [ ] 日本語入力（IME）正常動作
- [ ] 文字数制限の調整（日本語は英語の約1.5倍の表示幅）
- [ ] 右から左へのテキスト配置（RTL）は対象外

## t_wadaスタイル テスト戦略

### Outside-In TDD アプローチ
```
E2E受け入れテスト（シナリオベース） → 統合テスト（国際化機能）→ 単体テスト（翻訳関数）
```

### E2Eテスト（最小限・高価値）
- **言語切り替え完全フロー**
  - 英語→日本語切り替え→計算実行→結果確認→CSV出力
- **日本語モード完全フロー**
  - 日本語でパラメーター設定→計算実行→グラフ確認→エラーハンドリング
- **多言語セッション保持**
  - 言語切り替え→ブラウザ再読み込み→設定保持確認

### 統合テスト（国際化ライブラリ・主要パス）
- **i18n ライブラリ統合**
  - 翻訳ファイル読み込み・キー解決確認
- **フロントエンド国際化**
  - React/Vue.js国際化コンポーネント統合
- **API レスポンス国際化**
  - エラーメッセージ・バリデーションメッセージ多言語化

### 単体テスト（翻訳関数・フォーマット）
- **翻訳関数**: キー存在チェック・フォールバック動作
- **数値フォーマット**: 通貨・数値・日付の日本語ロケール変換
- **バリデーション**: 多言語エラーメッセージ生成
- **UI コンポーネント**: 言語切り替え時の再描画・状態管理

## 実装アプローチ

### Phase 1: 国際化基盤構築（Sprint 1）

#### 技術選択
```javascript
// フロントエンド: React-i18next
import i18n from 'i18next';
import { useTranslation } from 'react-i18next';

// 翻訳ファイル構造
/src/
  /i18n/
    /locales/
      /en/
        common.json
        calculator.json
        errors.json
      /ja/
        common.json
        calculator.json
        errors.json
    index.js
```

#### バックエンド国際化
```python
# Flask-Babel for backend i18n
from flask_babel import Babel, gettext, ngettext

# 翻訳ファイル
/app/translations/
  /en/LC_MESSAGES/
    messages.po
    messages.mo
  /ja/LC_MESSAGES/
    messages.po
    messages.mo
```

#### 実装内容
1. **国際化ライブラリセットアップ**
   ```bash
   # フロントエンド依存関係
   npm install react-i18next i18next i18next-browser-languagedetector
   
   # バックエンド依存関係
   pip install Flask-Babel babel
   ```

2. **翻訳ファイル構造設計**
   ```json
   // /src/i18n/locales/ja/calculator.json
   {
     "calculator": {
       "title": "Lambda vs VM コスト比較シミュレーター",
       "lambda": {
         "memory_size": "メモリサイズ (MB)",
         "execution_time": "実行時間 (秒)",
         "executions_per_month": "月間実行回数"
       },
       "vm": {
         "instance_type": "インスタンスタイプ",
         "cpu_cores": "CPUコア数",
         "memory_gb": "メモリ (GB)"
       },
       "buttons": {
         "calculate": "計算実行",
         "reset": "リセット",
         "csv_download": "CSVダウンロード"
       }
     }
   }
   ```

### Phase 2: UI要素の日本語化（Sprint 2）

#### React コンポーネント国際化
```jsx
// CalculatorForm.jsx
import { useTranslation } from 'react-i18next';

const CalculatorForm = () => {
  const { t } = useTranslation('calculator');
  
  return (
    <form>
      <label>{t('lambda.memory_size')}</label>
      <input 
        placeholder={t('lambda.memory_size_placeholder')}
        aria-label={t('lambda.memory_size_desc')}
      />
      <button>{t('buttons.calculate')}</button>
    </form>
  );
};
```

#### 言語切り替えコンポーネント
```jsx
// LanguageSwitcher.jsx
const LanguageSwitcher = () => {
  const { i18n } = useTranslation();
  
  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
  };
  
  return (
    <div className="language-switcher">
      <button 
        onClick={() => changeLanguage('en')}
        className={i18n.language === 'en' ? 'active' : ''}
      >
        English
      </button>
      <button 
        onClick={() => changeLanguage('ja')}
        className={i18n.language === 'ja' ? 'active' : ''}
      >
        日本語
      </button>
    </div>
  );
};
```

### Phase 3: グラフ・チャートの日本語対応（Sprint 3）

#### Chart.js 国際化
```javascript
// chartConfig.js
import { useTranslation } from 'react-i18next';

const useChartConfig = () => {
  const { t } = useTranslation('calculator');
  
  return {
    options: {
      plugins: {
        title: {
          display: true,
          text: t('chart.title')
        },
        legend: {
          labels: {
            generateLabels: (chart) => {
              // 動的に日本語ラベル生成
              return chart.data.datasets.map((dataset, i) => ({
                text: t(`chart.legend.${dataset.label}`),
                fillStyle: dataset.backgroundColor[i]
              }));
            }
          }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: t('chart.x_axis')
          }
        },
        y: {
          title: {
            display: true,
            text: t('chart.y_axis')
          }
        }
      }
    }
  };
};
```

#### 数値フォーマット（通貨・数値）
```javascript
// formatters.js
import { useTranslation } from 'react-i18next';

const useNumberFormatters = () => {
  const { i18n } = useTranslation();
  
  const formatCurrency = (amount) => {
    const locale = i18n.language === 'ja' ? 'ja-JP' : 'en-US';
    const currency = i18n.language === 'ja' ? 'JPY' : 'USD';
    
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0
    }).format(amount);
  };
  
  const formatNumber = (num) => {
    const locale = i18n.language === 'ja' ? 'ja-JP' : 'en-US';
    return new Intl.NumberFormat(locale).format(num);
  };
  
  return { formatCurrency, formatNumber };
};
```

### Phase 4: CSV出力・エラーメッセージ日本語化（Sprint 4）

#### CSV出力の国際化
```javascript
// csvExporter.js
const generateCSV = (data, language = 'en') => {
  const headers = {
    en: ['Executions', 'AWS Lambda', 'AWS EC2', 'Google Cloud', 'Azure'],
    ja: ['月間実行回数', 'AWS Lambda', 'AWS EC2', 'Google Cloud', 'Azure']
  };
  
  const csvHeaders = headers[language];
  const csvData = [csvHeaders, ...data];
  
  const filename = language === 'ja' 
    ? `コスト比較結果_${new Date().toISOString().split('T')[0].replace(/-/g, '')}.csv`
    : `cost-comparison_${new Date().toISOString().split('T')[0]}.csv`;
    
  return { csvData, filename };
};
```

#### バックエンド エラーメッセージ国際化
```python
# app/api/calculator_api.py
from flask_babel import gettext as _

@app.route('/api/calculate', methods=['POST'])
def calculate_costs():
    try:
        data = request.json
        # バリデーション
        if not data.get('lambda_memory'):
            return jsonify({
                'error': _('validation.lambda_memory_required')
            }), 400
    except Exception as e:
        return jsonify({
            'error': _('errors.calculation_failed'),
            'details': _('errors.server_error')
        }), 500
```

### Red-Green-Refactor サイクル適用

#### Red フェーズ
```javascript
// 失敗するテスト例
describe('Language Switching', () => {
  it('should display UI in Japanese when language is switched', () => {
    render(<Calculator />);
    
    // 現在は失敗する（日本語対応前）
    fireEvent.click(screen.getByText('日本語'));
    expect(screen.getByText('メモリサイズ (MB)')).toBeInTheDocument();
  });
});
```

#### Green フェーズ
```javascript
// 最小限の実装でテストを通す
const Calculator = () => {
  const [language, setLanguage] = useState('en');
  const labels = {
    en: { memory_size: 'Memory Size (MB)' },
    ja: { memory_size: 'メモリサイズ (MB)' }
  };
  
  return (
    <div>
      <button onClick={() => setLanguage('ja')}>日本語</button>
      <label>{labels[language].memory_size}</label>
    </div>
  );
};
```

#### Refactor フェーズ
```javascript
// i18n ライブラリを使用した改善版
import { useTranslation } from 'react-i18next';

const Calculator = () => {
  const { t, i18n } = useTranslation();
  
  return (
    <div>
      <button onClick={() => i18n.changeLanguage('ja')}>
        日本語
      </button>
      <label>{t('lambda.memory_size')}</label>
    </div>
  );
};
```

## 技術的考慮事項

### 依存関係
- **フロントエンド**: react-i18next, i18next, i18next-browser-languagedetector
- **バックエンド**: Flask-Babel, babel
- **既存機能**: 現在のUI/API構造を非破壊的に拡張

### パフォーマンス
- **翻訳ファイル**: 言語別に分割してオンデマンド読み込み
- **初期読み込み**: デフォルト言語のみ読み込み、切り替え時に追加読み込み
- **メモリ使用量**: 翻訳データのキャッシュ効率化

### セキュリティ
- **XSS対策**: 翻訳テキストのサニタイズ
- **入力検証**: 多言語文字セット対応のバリデーション
- **文字エンコーディング**: UTF-8統一

### UI/UX設計
- **デザイン一貫性**: 既存デザインシステムとの整合性
- **レスポンシブ**: 日本語テキストの長さに応じたレイアウト調整
- **アクセシビリティ**: スクリーンリーダー対応、キーボードナビゲーション

## Definition of Done

### 機能完了基準
- [ ] 全BDD受け入れシナリオが自動テストでパス
- [ ] 言語切り替えがシームレスに動作
- [ ] 全UI要素が適切な日本語で表示
- [ ] グラフ・チャートが日本語ロケールで描画
- [ ] CSV出力が日本語ヘッダー対応
- [ ] エラーメッセージが適切な日本語で表示

### 品質基準
- [ ] テストカバレッジ: 90%以上維持
- [ ] 翻訳品質レビュー: 技術用語の正確性確認
- [ ] パフォーマンステスト: 言語切り替え時1秒以内
- [ ] アクセシビリティ: WCAG 2.1 AA準拠
- [ ] ブラウザ互換性: Chrome, Firefox, Safari, Edge

### セキュリティ・運用基準
- [ ] セキュリティスキャン: 多言語入力に対するXSS対策確認
- [ ] 負荷テスト: 翻訳ファイル読み込み時の性能確認
- [ ] 監視設定: 言語切り替えエラーのログ監視設定

### ドキュメント・レビュー
- [ ] 翻訳精度レビュー完了（ネイティブスピーカーによる確認）
- [ ] API仕様書更新（多言語レスポンス対応）
- [ ] ユーザーガイド更新（言語切り替え手順追加）
- [ ] 開発者ドキュメント更新（i18n実装ガイド）

### デプロイ・保守
- [ ] 翻訳ファイルのバージョン管理体制確立
- [ ] 新規文言追加時のワークフロー確立
- [ ] 本番環境での言語切り替え動作確認
- [ ] 翻訳更新の継続的インテグレーション設定

## リスクと軽減策

### 主要リスク
1. **翻訳品質**: 技術用語の誤訳によるユーザー混乱
   - **軽減策**: 専門用語辞書作成、ネイティブレビュー実施
2. **パフォーマンス劣化**: 翻訳ファイル読み込みによる応答速度低下
   - **軽減策**: 遅延読み込み、CDN利用、キャッシュ戦略
3. **レイアウト崩れ**: 日本語テキストの長さによるUI破綻
   - **軽減策**: 文字数制限、レスポンシブデザイン強化
4. **既存機能への影響**: 国際化実装による回帰
   - **軽減策**: 包括的な回帰テスト、段階的デプロイ

### 軽減策詳細
- **段階的ロールアウト**: 機能フラグによる部分リリース
- **A/Bテスト**: 言語切り替え機能のユーザビリティ検証
- **モニタリング**: 言語別のユーザー行動・エラー率分析
- **フォールバック**: 翻訳取得失敗時の英語フォールバック機能

## 関連PBI

### 前提条件
- **完了済み**: PBI01-PBI10（基本機能）、セキュリティPBI（SEC-A〜D）

### 依存関係
- **なし**: 独立した機能拡張として実装可能

### 後続PBI
- **I18N-KR**: 韓国語対応（将来的拡張）
- **I18N-CN**: 中国語（簡体字）対応（将来的拡張）

### 関連機能
- **CSV出力機能**: 多言語ヘッダー対応
- **グラフ表示機能**: 軸ラベル・凡例国際化
- **エラーハンドリング**: 多言語エラーメッセージ

## ステークホルダー

### プロダクトオーナー
- **責任**: 翻訳仕様承認・受け入れテスト立会い
- **成果物**: 翻訳要件定義、品質基準設定

### 日本語ネイティブレビューワー
- **責任**: 翻訳品質確認・専門用語検証
- **成果物**: 翻訳品質レポート、用語集

### 開発チーム
- **責任**: 国際化機能実装・テスト・技術レビュー
- **成果物**: i18n実装、テストコード、技術ドキュメント

### UX/UIデザイナー
- **責任**: 多言語対応UIデザイン・ユーザビリティ確認
- **成果物**: 多言語UIデザイン、UXテストレポート

---

## 実装チェックリスト

### Sprint 1: 国際化基盤
- [ ] react-i18next セットアップ
- [ ] Flask-Babel セットアップ
- [ ] 翻訳ファイル構造設計
- [ ] 言語切り替え基本機能実装
- [ ] 言語設定永続化機能

### Sprint 2: UI要素日本語化
- [ ] フォーム項目ラベル翻訳
- [ ] ボタン・メニュー翻訳
- [ ] プレースホルダーテキスト翻訳
- [ ] バリデーションメッセージ翻訳
- [ ] ツールチップ・ヘルプテキスト翻訳

### Sprint 3: グラフ・データ可視化
- [ ] Chart.js 軸ラベル国際化
- [ ] 凡例・ツールチップ日本語化
- [ ] 数値フォーマット（通貨・日付）
- [ ] グラフタイトル・説明文翻訳

### Sprint 4: 出力・エラー対応
- [ ] CSV出力ヘッダー日本語化
- [ ] ファイル名日本語対応
- [ ] API エラーメッセージ翻訳
- [ ] ネットワークエラー等の日本語化
- [ ] 404・500エラーページ翻訳

---

**作成日**: 2025-07-22  
**作成者**: 開発チーム  
**承認者**: プロダクトオーナー（承認待ち）  
**ステータス**: Ready for Sprint Planning  
**想定開始日**: 2025-07-29  
**想定完了日**: 2025-08-26（4週間）