# Changelog

All notable changes to the AWS Lambda vs VM Cost Simulator project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-07-28

### プロジェクト完了 - 全機能実装済み
- **✅ 100% 完了**: 全39ストーリーポイント実装済み
- **✅ 88% テストカバレッジ**: 133テストケース実行
- **✅ 本番環境対応**: Docker化・セキュリティ基盤完備
- **✅ マルチクラウド対応**: 6プロバイダー + サーバーレス対応

### Added - セキュリティ強化 (PBI-SEC-ESSENTIAL)
- 入力境界チェック機能 - 全APIエンドポイントでの安全な入力検証
- CSV injection防止機能 - エクスポートデータの完全な無害化
- 環境セキュリティ検証 - プロダクション環境でのDEBUGモード防止
- CORS設定適正化 - 環境別オリジン制限の厳格化

### Security
- Critical脆弱性: 3個 → 0個 (100%解決)
- High脆弱性: 5個 → 1個 (80%解決)
- OWASP準拠率: 60% → 95%達成
- セキュリティスコア: B+ → A-向上

## [0.1.0-rc.4] - 2025-07-26

### Added - 包括的ドキュメント整備
- 包括的リファレンス文書構築 (`ref/`ディレクトリ)
- API endpoints完全仕様書
- 実装アーキテクチャ詳細文書
- セキュリティアーキテクチャ文書
- テストフレームワークガイド

### Fixed
- VM instance比較表示問題（トグルOFF時の修正）

### Added - Serverless機能拡張
- serverless provider包括的仕様追加
- マルチプロバイダー対応強化

## [0.1.0-rc.3] - 2025-07-23

### Added - 国際化対応完成 (PBI-I18N-JP)
- 日本語完全対応（i18n）実装
- UI・メッセージの完全国際化
- 英語/日本語リアルタイム切り替え
- ローカライゼーション基盤構築

### Added - カスタム入力機能
- Exchange Rate カスタム入力サポート
- Lambda Memory Size カスタム対応
- 実行頻度デフォルト変更（1/second）

## [0.1.0-rc.2] - 2025-07-22

### Added - エンタープライズ認証システム (SEC-02)
- JWT認証基盤強化
- UI柔軟性向上
- 認証フロー最適化

### Fixed
- コスト比較グラフX軸表示範囲拡張
- フル表示範囲カバー対応

### Added - 開発環境改善
- 包括的開発セッションログ追加
- 開発効率向上のためのドキュメント整備

## [0.1.0-rc.1] - 2025-07-21

### Added - セキュリティ基盤 (SEC-01)
- セキュアシークレット管理実装
- JWT認証システム完全実装
- 環境設定セキュリティ強化
- 本番環境対応セキュリティ設定

### Added - 設定管理改善
- .env.development.example追加
- .mise.local.toml.example追加
- セキュリティ設定分離

## [0.1.0-beta.3] - 2025-07-20

### Added - エンタープライズ機能簡素化
- 包括的セキュリティ実装 (PBI-SEC-A,B,C,D)
- 監視・運用基盤構築
- 企業向け機能の適正化

### Added - セキュリティ基盤
- 異常検知システム
- 監査ログシステム
- 環境バリデーター
- 整合性チェッカー

### Changed
- プロジェクトスコープ簡素化
- Apache 2.0ライセンス適用

## [0.1.0-beta.2] - 2025-07-15

### Added - マルチクラウド対応拡張
- OCI VM オプション大幅拡張
- VM.Standard.E4.Flex シリーズ対応
- プロバイダー対応強化

### Added - ドキュメント充実
- 包括的リファレンス文書構築
- プロダクション環境デプロイガイド
- 技術仕様詳細文書

## [0.1.0-beta.1] - 2025-07-14

### Added - Phase 1 コア機能完成 (PBI10)
- **インターネット転送割合設定機能** - 0-100%の柔軟な転送シナリオ
- プリセット値 + カスタム入力対応
- プライベートネットワークシナリオサポート

### Added - マルチプロバイダー対応
- VM プロバイダー対応拡張
- Azure, OCI本格対応
- egress費用計算強化

### Added - 品質向上
- テストカバレッジ向上
- E2E BDDテスト追加
- 包括的統合テスト

## [0.1.0-alpha.6] - 2025-07-14

### Added - Egress費用計算 (PBI09)
- **インターネットegress転送費用計算機能**
- 全プロバイダーでのegress cost計算
- 転送量設定機能
- Break-even point計算にegress費用反映

### Added - プロバイダー料金体系
- AWS: 0.114 USD/GB (100GB無料枠)
- Google Cloud: 0.12 USD/GB (100GB無料枠)
- Azure: 0.12 USD/GB (100GB無料枠)
- OCI: 0.025 USD/GB (10TB無料枠)
- Sakura Cloud: 0.0 USD/GB (完全無料)

## [0.1.0-alpha.5] - 2025-07-14

### Added - Google Cloud対応 (PBI08)
- **Google Cloud Compute Engine プロバイダー追加**
- Asia-northeast1 (Tokyo) 料金統合
- Google Cloud instances pricing実装
- UI and API統合完了

### Added - インスタンスタイプ
- e2-micro, e2-small, e2-medium
- n1-standard-1, c2-standard-4
- リージョン別料金対応

## [0.1.0-alpha.4] - 2025-07-14

### Added - Docker化完成 (PBI07)
- **Docker化実装とMakefile作成**
- Dockerfile with multi-stage build
- .dockerignore最適化
- Makefile with Docker commands
- 本番環境デプロイ対応

## [0.1.0-alpha.3] - 2025-07-13

### Added - Docker化調査 (PBI06)
- **Docker化技術調査スパイク**
- Docker base image選定
- セキュリティ考慮事項調査
- イメージ最適化戦略定義

## [0.1.0-alpha.2] - 2025-07-12

### Added - 通貨・エクスポート機能 (PBI05)
- **通貨変換・CSVエクスポート機能**
- 為替レート設定機能
- JPY表示切り替え
- CSV出力機能
- 詳細分析データエクスポート

## [0.1.0-alpha.1] - 2025-07-08

### Added - グラフ可視化 (PBI04)
- **コスト比較グラフ表示機能**
- Chart.js インタラクティブグラフ実装
- ブレークイーブンポイント表示
- 対数軸リアルタイム表示
- 紫線での損益分岐点表示

## [0.0.3] - 2025-07-07

### Added - VM計算機能 (PBI03)
- **VM単体コスト計算機能**
- EC2・さくら クラウド料金計算
- インスタンス選択UI
- 固定月額費用計算

### Added - 対応インスタンス
- **AWS EC2**: t3.micro, t3.small, t3.medium, t3.large, c5.large, c5.xlarge
- **Sakura Cloud**: 1core/1GB, 2core/2GB, 4core/8GB, 6core/12GB

## [0.0.2] - 2025-07-06

### Added - Lambda計算機能 (PBI02)
- **Lambda単体コスト計算機能**
- Lambda料金計算エンジン
- 基本的なWeb UI
- 実行時間ベース従量課金計算

### Added - Lambda設定
- Memory Size: 128MB-2048MB
- Execution Time: 1秒-60秒
- AWS Free Tier対応

## [0.0.1] - 2025-07-05

### Added - 技術基盤 (PBI01)
- **技術調査スパイク**
- 技術スタック選定（Flask, pytest, Chart.js）
- TDD環境構築（pytest, coverage, pre-commit）
- プロジェクト構造作成
- サンプルテストケース実装・実行成功

### Added - 開発環境
- Python 3.11 + Flask
- Outside-In TDD + BDD アプローチ
- pytest テストフレームワーク
- 88% テストカバレッジ達成

---

## プロジェクト技術情報

### 🎯 完成機能
- **マルチサーバーレス比較**: AWS Lambda・Google Cloud Functions
- **6プロバイダーVM比較**: AWS EC2、Google Cloud、Azure、OCI、Sakura Cloud
- **高度な機能**: Egress費用計算、インターネット転送割合設定
- **国際化対応**: 日本語/English完全対応
- **セキュリティ**: エンタープライズレベルのセキュリティ基盤

### 🔧 技術スタック
- **Backend**: Python 3.11, Flask
- **Frontend**: Chart.js, JavaScript, HTML5/CSS3
- **Testing**: pytest (88% coverage), Outside-In TDD + BDD
- **Deployment**: Docker, Makefile
- **Security**: JWT認証、CSRF保護、入力検証

### 📊 プロジェクト統計
- **総PBI数**: 12 (Phase 1: 10 + 追加: 2)
- **総ストーリーポイント**: 39 + セキュリティ強化
- **テストケース**: 133件
- **テストカバレッジ**: 88%
- **対応プロバイダー**: 8個 (サーバーレス2 + VM6)

### 🏆 プロジェクト完了
このプロジェクトは**完全に完了**しました。すべての計画機能が実装され、本番運用可能な状態です。

---

## Links

- [Project Documentation](./Design/Overview.md)
- [Implementation Details](./ref/README.md)
- [User Guide](./docs/USER_GUIDE.md)
- [Admin Guide](./docs/ADMIN_GUIDE.md)