# boatrace-ai

競艇（ボートレース）のレース結果をもとに、機械学習で着順や期待値を予測するためのAI予測システムです。

## プロジェクト概要

このプロジェクトでは、以下の流れで予測基盤を構築します。

- レースデータの収集・整形
- データベースへの保存と管理
- 特徴量の生成
- 予測モデルの学習・推論
- 賭け戦略の評価
- 結果の出力と可視化

## ディレクトリ構成

- `src/collector/` : データ収集
- `src/database/` : DB管理
- `src/features/` : 特徴量生成
- `src/model/` : 予測モデル
- `src/betting/` : 賭け戦略
- `src/output/` : 結果出力
- `data/raw/` : 生データ
- `data/processed/` : 前処理済みデータ
- `data/features/` : 特徴量データ
- `models/` : 学習済みモデル
- `notebooks/` : 分析ノートブック
- `tests/` : テストコード
- `scripts/` : 実行スクリプト
