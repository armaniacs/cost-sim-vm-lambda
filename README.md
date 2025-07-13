# AWS Lambda vs VM Cost Simulator

AWS LambdaとVirtual Machine（AWS EC2、Sakura Cloud、Google Cloud Compute Engine）のコスト比較シミュレーター

## 概要

このアプリケーションは、AWS Lambdaの実行頻度に応じたコストと、Virtual Machineの固定コストを比較し、ブレークイーブンポイント（損益分岐点）を視覚化するWebツールです。

## 機能

- **インタラクティブなコスト比較グラフ** - Chart.jsによる対数軸での表示
- **実行頻度参考線** - 秒間1〜1000リクエストの黄色い参考線
- **ブレークイーブンポイント表示** - LambdaとVMのコストが交差する点を紫線で表示
- **複数のVMプロバイダー対応** - AWS EC2、Sakura Cloud、Google Cloud Compute Engineの比較
- **通貨変換** - USD/JPY自動変換対応
- **CSV出力** - 計算結果をCSVファイルで出力
- **リアルタイム計算** - 設定変更時の即座な再計算

## 使い方

### 1. アプリケーション起動

```bash
make dev
```

ブラウザで http://localhost:5001 にアクセス

### 2. Lambda設定

- **Memory Size**: 128MB〜2048MBから選択
- **Execution Time**: 1秒〜60秒から選択
- **Execution Frequency**: 月間実行回数を選択
- **Include AWS Free Tier**: AWSフリーティアの適用有無

### 3. VM比較設定

- **AWS EC2**: t3.micro〜c5.xlargeから選択
- **Sakura Cloud**: 1core/1GB〜6core/12GBから選択

### 4. 通貨設定

- **Exchange Rate**: JPY/USDレート設定
- **Display in JPY**: 日本円表示の切り替え

### 5. 結果の見方

#### グラフ表示
- **青線**: AWS Lambdaコスト
- **緑線**: AWS EC2コスト（破線）
- **オレンジ線**: Sakura Cloudコスト（破線）
- **黄色参考線**: 秒間実行数の目安
- **紫線**: ブレークイーブンポイント

#### Quick Results
- 設定した実行頻度でのコスト比較
- 各プロバイダーの月額コスト表示

#### データテーブル
- 詳細なコスト計算結果
- CSV出力機能

#### ブレークイーブン分析
- LambdaとVMのコストが同じになる実行頻度
- 秒間リクエスト数での表示

## 対応環境

- **Python**: 3.11以上
- **ブラウザ**: Chrome、Firefox、Safari、Edge
- **OS**: macOS、Linux、Windows

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

## サポート

- **バグ報告**: GitHubのIssues
- **機能要望**: GitHubのIssues
- **ドキュメント**: [Design/Overview.md](Design/Overview.md)

## ライセンス

MIT License

---

**開発者向け情報**: [README-Development.md](README-Development.md)