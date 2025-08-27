# PicsPickPrompt

入力画像からプロンプト用の JSON ファイルを生成するためのプロトタイプ CLI ユーティリティです。

このプロトタイプは以下の抽出モデルを用いて推論を実行します。

* **Florence-2** : キャプション生成
* **WD14** : アニメ向けタグ抽出。特に Windows 環境ではこのモデルを優先して利用してください。
* **CLIP Interrogator** : スタイルとライティングのヒント
* **DeepDanbooru** (バックアップ) : 追加タグ抽出。`tensorflow-io` などの依存が必要なため Windows では非推奨です。本リポジトリでは `tensorflow-io` を自動でインストールしないため、利用する場合は `tensorflow-cpu==2.12.*` と `tensorflow-io-gcs-filesystem==0.31.0` を手動でインストールしてください。

## セットアップ

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

Windows の場合:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 使い方

```bash
python -m img2prompt.cli path/to/image.jpg
```

Windows の PowerShell やコマンドプロンプトでも同じコマンドを使用します:

```powershell
python -m img2prompt.cli path\to\image.jpg
```

実行すると `path/to/image.jpg.prompt.json` が生成され、抽出したプロンプトデータが保存されます。

### 実行例

```bash
$ python -m img2prompt.cli examples/sample.jpg
```

生成される `examples/sample.jpg.prompt.json` の内容例:

```json
{
  "caption": "a girl smiling",
  "prompt": "1girl, smile, outdoor",
  "negative_prompt": "(low quality:1.2), (blurry:1.2), (jpeg artifacts:1.1), (duplicate:1.1), (bad anatomy:1.1), (extra fingers:1.2), (nsfw:1.3), (monochrome:1.1), (lineart:1.1)",
  "style": "anime",
  "model_suggestion": "unspecified"
}
```
