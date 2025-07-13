# Design Overview

## プロジェクトの目的

このプログラムは、AWS Lambdaのコストと、バーチャルマシン（AWS EC2、さくらのクラウド、Google Cloud Compute Engine）で同様のことを行う場合のコストを比較します。
コストを比較し、グラフを作成します。そして break even point を明らかにします。

## 機能

- localhostで動作するWebページを入出力のインタフェースとして持ちます。
  - 次の画像のような入出力が最初の基本です
  - ![cost-input-and-result](cost-input-and-result.png) 
- コストを比較し、グラフを作成します。そして break even point を明らかにします。
  - CSV形式でデータを出力する機能も持ちます。

## 考慮する事項

1. Lambdaの費用を計算する。Lambdaは動作時だけに費用が発生する。
2. Virtual Machine (VM) の費用を計算する。このVMはlambdaと異なり、アクセスがなくても起動しているだけで費用が発生する。
3. Internetへのegress feeの計算をする。1リクエストあたりのインターネットegress転送量も、Webから入力するパラメータとする。

- Lambdaの動作パラメータ
  - メモリサイズ (128MB, 512MB, 1024MB, 2048MB)
  - プロセスの動作時間 (1秒、10秒、30秒、60秒)
  - Number of executions (月間 100万回、秒間1回、秒間10回、秒間100回)
  - 1リクエストあたりのインターネットegress転送量(10KB, 100KB, 1MB)

- インターネットに転送する割合を100%, 50%, 10%, 0%, およびカスタマイズした割合 を入力できるようにしてください。例えば、完全に閉域でのみ使用するならば0%です。

- グラフのX軸は、Number of executionsです。
  - per month および、per secondを表示します。
- グラフのY軸は、コスト（費用）です。ドルおよび円表示をします。換算レートも設定可能です。

- 比較対象とするVMは、東京リージョンにおけるAWS EC2、さくらのクラウド、およびGoogle Cloud Compute Engineとする。

- AWSとGoogleの月100GBまでの転送量は無料


### Egress Rates
- AWS (Lambda/EC2): 0.114 USD/GB
- Google Cloud: 0.12 USD/GB
- Sakura Cloud: 0 JPY/GB (egress free)

## 実装

### 技術スタック
- **バックエンド**: Python
- **フロントエンド**: localhostで動作するWebインターフェース
- **ビジュアライゼーション**: グラフ生成ライブラリ（未定）
- **データエクスポート**: CSV機能

### 実装予定の主要機能

1. AWS Lambdaコスト計算:
   - メモリ設定: 128MB, 512MB, 1024MB, 2048MB
   - 実行時間: 1秒、10秒、30秒、60秒
   - 実行頻度: 月間100万回、秒間1回、秒間10回、秒間100回

2. バーチャルマシンコスト計算:
   - AWS EC2（東京リージョン）
   - さくらのクラウド
   - Google Cloud Compute Engine（東京リージョン、asia-northeast1）

3. インタラクティブなコスト比較インターフェース:
   - LambdaとVMパラメータの入力フィールド
   - リアルタイムコスト計算
   - グラフ表示（X軸: 実行回数、Y軸: USD/JPYコスト）
   - 設定可能な為替レート
   - CSVエクスポート機能

### コア計算ロジック

- **Lambdaコスト**: 実行回数 × 実行時間 × メモリ × AWS料金
- **VMコスト**: 使用量に関係なく固定の月額費用
- **ブレークイーブンポイント**: LambdaコストとVMコストが等しくなる点

デフォルトの為替レート: 150 JPY/USD

## 関連ドキュメント

- [QA.md](QA.md) - 設計に関する詳細な質問と回答
