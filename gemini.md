# Gemini CLI Agent Guide for PicsPickPrompt Project

このドキュメントは、Gemini CLI エージェントが PicsPickPrompt プロジェクトを理解し、効率的に作業を進めるためのガイドです。

## 1. プロジェクト概要

PicsPickPrompt は、入力画像からプロンプト用の JSON ファイルを生成するためのプロトタイプ CLI ユーティリティです。
以下の抽出モデルを用いて推論を実行します。

*   **Florence-2**: キャプション生成
*   **WD14**: アニメ向けタグ抽出 (Windows 環境では優先)
*   **CLIP Interrogator**: スタイルとライティングのヒント
*   **DeepDanbooru**: 追加タグ抽出 (Windows では `tensorflow-cpu` と `tensorflow-io-gcs-filesystem` の手動インストールが必要)

生成される JSON ファイルには、キャプション、プロンプト、ネガティブプロンプト、スタイル、モデルの提案が含まれます。

## 2. 技術スタック

主要な技術スタックは Python であり、以下の主要なライブラリを使用しています。

*   `accelerate`
*   `clip-interrogator`
*   `einops`
*   `huggingface-hub`
*   `Keras`
*   `numpy`
*   `onnxruntime`
*   `Pillow`
*   `torch`
*   `transformers`
*   `typer` (CLI フレームワーク)

完全な依存関係は `requirements.txt` を参照してください。

## 3. ディレクトリ構造

プロジェクトの主要なディレクトリとファイルの役割は以下の通りです。

*   `.venv/`: Python 仮想環境
*   `cache/`: モデルのキャッシュディレクトリ
*   `examples/`: サンプルの画像と生成される JSON ファイル
*   `img2prompt/`: メインのアプリケーションコード
    *   `cli.py`: CLI のエントリーポイント
    *   `assemble/`: プロンプトのアセンブルロジック
    *   `eval/`: 評価関連のコード
    *   `export/`: 出力関連のコード
    *   `extract/`: 各モデルからの特徴抽出ロジック
    *   `options/`: オプション設定
    *   `utils/`: ユーティリティ関数
*   `tests/`: ユニットテストコード
*   `CHANGELOG.md`: プロジェクトの変更履歴
*   `README.md`: プロジェクトの概要と基本的な使用方法
*   `RoadMap.md`: プロジェクトのロードマップと今後の計画
*   `requirements.txt`: Python の依存関係リスト

## 4. 開発セットアップ

プロジェクトをセットアップするには、以下の手順を実行します。

```bash
# Linux/macOS
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Windows PowerShell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 5. 実行方法

画像からプロンプトを生成するには、以下のコマンドを使用します。

```bash
# Linux/macOS/Windows PowerShell/Command Prompt
python -m img2prompt.cli path/to/image.jpg
```

実行後、`path/to/image.jpg.prompt.json` が生成されます。

## 6. 開発者向けメモ

### 6.1. DeepDanbooru の利用に関する注意点 (Windows)

Windows 環境で DeepDanbooru モデルを利用する場合、`tensorflow-io` などの依存関係が自動でインストールされません。利用する場合は、以下のコマンドで手動でインストールしてください。

```bash
pip install tensorflow-cpu==2.12.* tensorflow-io-gcs-filesystem==0.31.0
```

### 6.2. テストの実行

プロジェクトには `tests/` ディレクトリにユニットテストが含まれています。テストの実行には `pytest` が使用されている可能性が高いです。`pytest` がインストールされていない場合は、`pip install pytest` でインストールしてください。

```bash
pytest
```

### 6.3. バージョン管理ルール

プロジェクト内の Python スクリプトおよび MQL4 スクリプトには、以下のバージョン管理ルールが適用されます。

*   各スクリプトの冒頭にコメント形式で `Version: X.Y.Z, Date: YYYY-MM-DD, Description: (変更点)` を記述します。
*   `X.Y.Z` はセマンティックバージョニングの簡易版に従い更新します。
    *   初期バージョンは `1.0.0` です。
    *   後方互換性のない変更: メジャーバージョン (X) をインクリメント
    *   新機能の追加: マイナーバージョン (Y) をインクリメント
    *   バグ修正: パッチバージョン (Z) をインクリメント
*   現在、`analyze_feature_importance.py` は `Version: 1.0.1`、その他のファイルは `Version: 1.0.0` となっています。

### 6.4. Git 操作

*   ファイルを更新したら Git 上にプッシュします。
*   ユーザーは 100MB を超えるファイルを Git にプッシュしないことを希望しています。
*   Git コミット時には、メッセージを直接指定するのではなく、一時的なテキストファイルにメッセージを書き込み、そのファイルを使用してコミットすることを推奨します。

### 6.5. Changelog の更新

ファイルを更新したら `CHANGELOG.md` に概要を書き加えます。

### 6.6. ロードマップ

プロジェクトのロードマップは `RoadMap.md` に記載されており、今後の開発の方向性を示しています。

### 6.7. GPU の利用

今後の実装では、GPU が利用可能な場合は優先して GPU を活用します。

### 6.8. サーバー起動コマンド

`npx` などのサーバーを起動するコマンドは、外部の PowerShell で実行します。

### 6.9. フリーズする可能性のあるコマンド

ユーザーは、私がフリーズする可能性のあるコマンドを実行することを許可しており、フリーズした場合は手動で停止します。

### 6.10. エラーの再発防止とテスト

ユーザーは、複雑なエラーの再発防止のため、定期的にテストを実行することを推奨しています。
