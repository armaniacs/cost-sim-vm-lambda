# AWS Lambda vs VM Cost Simulator

AWS Lambda・Google Cloud FunctionsとVirtual Machine（AWS EC2、Google Cloud Compute Engine、Azure、Oracle Cloud Infrastructure、Sakura Cloud）のマルチクラウド コスト比較シミュレーター

## 概要

このアプリケーションは、AWS Lambda・Google Cloud Functionsなどのサーバーレス実行頻度に応じたコストと、6つのクラウドプロバイダーのVirtual Machineの固定コストを比較し、ブレークイーブンポイント（損益分岐点）を視覚化するWebツールです。

## 🎯 プロジェクト完了状況

- ✅ **100% 完了** - 全39ストーリーポイント実装済み
- ✅ **88% テストカバレッジ** - 133テストケース実行
- ✅ **本番環境対応** - Docker化・セキュリティ基盤完備
- ✅ **マルチクラウド対応** - 6プロバイダー + 2サーバーレス対応

## 機能

### 📊 コア機能
- **マルチサーバーレス比較** - AWS Lambda ・ Google Cloud Functions の選択可能比較
- **6プロバイダーVM比較** - AWS EC2、Google Cloud Compute Engine、Azure、Oracle Cloud Infrastructure、Sakura Cloud
- **インタラクティブグラフ** - Chart.jsによる対数軸リアルタイム表示
- **ブレークイーブンポイント表示** - サーバーレスとVMのコスト交差点を紫線表示

### 🚀 高度な機能
- **Egress費用計算** - データ転送費用の詳細計算（全プロバイダー対応）
- **インターネット転送割合設定** - 0-100%の柔軟な転送シナリオ設定
- **通貨変換サポート** - USD/JPY自動変換・カスタムレート対応
- **CSVエクスポート** - 詳細分析データの完全CSV出力
- **日本語完全対応** - UI・メッセージの完全国際化（i18n）対応

### 🔒 セキュリティ機能
- **エンタープライズ認証基盤** - JWTベース認証・認可システム
- **包括的入力検証** - CSRF保護・レート制限機能
- **セキュリティヘッダー** - 本番環境対応セキュリティ設定

## 使い方

### 1. アプリケーション起動

```bash
make dev
```

ブラウザで http://localhost:5001 にアクセス

### 2. サーバーレス設定

#### AWS Lambda
- **Memory Size**: 128MB〜2048MBから選択
- **Execution Time**: 1秒〜60秒から選択
- **Include AWS Free Tier**: AWSフリーティアの適用有無

#### Google Cloud Functions
- **Memory Size**: 128MB〜2048MBから選択
- **Generation**: 1st/2nd Generation選択対応
- **Runtime**: 各種ランタイム対応
- **Include GCP Free Tier**: Google Cloudフリーティア適用

#### 共通設定
- **Execution Frequency**: 月間実行回数を選択
- **Egress Transfer**: リクエストあたりKB設定
- **Internet Transfer Ratio**: 0-100%のプリセットまたはカスタム入力

### 3. VM比較設定（6プロバイダー対応）

- **AWS EC2**: t3.micro, t3.small, t3.medium, t3.large, c5.large, c5.xlarge
- **Google Cloud Compute Engine**: e2-micro, e2-small, e2-medium, n1-standard-1, c2-standard-4
- **Azure Virtual Machines**: B1s, B2s, D2s_v3, F2s_v2
- **Oracle Cloud Infrastructure**: VM.Standard.E2.1, VM.Standard.E2.2, VM.Standard.E2.4
- **Sakura Cloud**: 1core/1GB, 2core/2GB, 4core/8GB, 6core/12GB

### 4. 高度な設定

#### 通貨・表示設定
- **Exchange Rate**: JPY/USDカスタムレート設定
- **Display in JPY**: 日本円/USD表示のリアルタイム切り替え
- **Language**: 日本語/English UI完全対応

#### ネットワーク設定
- **Egress Data Transfer**: リクエストあたりKB単位設定
- **Internet Transfer Ratio**: 0%（プライベート）〜100%（フルインターネット）

### 5. 結果の見方

#### グラフ表示（マルチプロバイダー対応）

**サーバーレスコスト（実線）:**
- **青線**: AWS Lambdaコスト
- **緑線**: Google Cloud Functionsコスト

**VMコスト（破線）:**
- **オレンジ線**: AWS EC2コスト
- **緑破線**: Google Cloud Compute Engineコスト
- **青破線**: Azure Virtual Machinesコスト
- **紫破線**: Oracle Cloud Infrastructureコスト
- **灰破線**: Sakura Cloudコスト

**参考線:**
- **黄色線**: 秒間実行数の目安（1-1000req/s）
- **紫線**: ブレークイーブンポイント（損益分岐点）

#### Quick Results
- 設定した実行頻度でのリアルタイムコスト比較
- 全プロバイダー（サーバーレス+VM）の月額コスト一覧
- Egress費用を含む総合コスト表示

#### 詳細データテーブル
- 全プロバイダーの詳細コスト内訳（コンピュート・リクエスト・転送費用）
- フリーティア適用状況と節約額表示
- CSVエクスポート機能（全データポイント含む）

#### スマートブレークイーブン分析
- サーバーレスと各VMプロバイダーの損益分岐点計算
- 秒/分/時間単位での実行頻度表示
- Egress費用を含む総合コストでの最適化推奨

## 技術スペック・対応環境

### サーバー環境
- **Python**: 3.11+ （mise管理）
- **Framework**: Flask 2.3+ （Application Factoryパターン）
- **Database**: SQLite3 （開発）/ PostgreSQL （本番対応）
- **Testing**: pytest + coverage （88%カバレッジ）
- **Docker**: Multi-stage builds + production ready

### クライアント環境
- **ブラウザ**: Chrome, Firefox, Safari, Edge（最新版）
- **JavaScript**: ES6+ （Vanilla JS、フレームワーク非依存）
- **CSS**: Bootstrap 5 + カスタムCSS
- **Charts**: Chart.js 3.9+ （インタラクティブグラフ）
- **i18n**: 日本語/English 完全対応

### 開発ツール
- **OS**: macOS, Linux, Windows + WSL2
- **環境管理**: mise（Python + 依存関係管理）
- **コード品質**: Black, isort, flake8, mypy
- **ビルドシステム**: Makefile + Docker Compose

## 開発コマンド一覧

### 基本コマンド
```bash
# 環境セットアップと依存関係インストール
make setup          # 初回セットアップ（推奨）

# 日常開発
make dev             # 開発サーバー起動 (localhost:5001)
make test            # テスト実行 + カバレッジレポート
make lint            # コード品質チェック
make format          # コードフォーマット
make check           # コミット前の全チェック

# Docker関連
make docker-build    # Dockerイメージビルド
make docker-run      # Dockerコンテナ起動
make docker-test     # Docker環境でテスト実行

# ユーティリティ
make clean           # キャッシュクリア
make help            # 全コマンド一覧表示
```

### テスト実行コマンド
```bash
make test            # 全テスト + カバレッジレポート
make t               # 短縮形
make test-unit       # ユニットテストのみ
make test-integration # 結合テストのみ
make test-e2e        # E2Eテストのみ
```

## トラブルシューティング

### ポート競合エラー
```bash
# 別ポートで起動
PORT=8000 make dev
```

### 計算結果が表示されない
- ブラウザのキャッシュをクリア
- 開発者ツール（F12）でJavaScriptエラーを確認

### データが正しく表示されない
- ページをリフレッシュ
- フォームの必須項目がすべて入力されているか確認

## ドキュメンテーション・サポート

### ユーザー向けドキュメント
- **[ユーザーガイド](docs/USER_GUIDE.md)** - 詳細な使用方法・機能説明
- **[管理者ガイド](docs/ADMIN_GUIDE.md)** - システム管理・デプロイガイド

### 開発者向けドキュメント
- **[プロジェクト仕様](Design/Overview.md)** - 完全なプロジェクト仕様書
- **[開発ガイド](ref/development-guide.md)** - TDDワークフロー・セットアップ手順
- **[APIリファレンス](ref/api-endpoints-reference.md)** - 全REST APIエンドポイント一覧
- **[アーキテクチャ概要](ref/architecture-overview.md)** - システム設計・パターン
- **[セキュリティアーキテクチャ](ref/security-architecture.md)** - エンタープライズセキュリティ設計

### サポート
- **バグ報告**: GitHub Issues
- **機能要望**: GitHub Issues
- **コントリビューション**: Pull Requests歓迎

## ライセンス

Apache License 2.0

---

## プロジェクト情報

**ステータス**: ✅ 完成・メンテナンスフェーズ  
**最終更新**: 2025-07-25  
**ライセンス**: Apache License 2.0  
**開発手法**: Outside-In TDD + ryuzeeメソドロジー

### 関連リンク
- **[開発者情報](README-Development.md)** - 開発環境セットアップ詳細
- **[PBI管理](Design/PBI/)** - プロダクトバックログ管理
- **[技術リファレンス](ref/)** - 詳細技術ドキュメント集