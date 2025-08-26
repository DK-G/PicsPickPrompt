# PicsPickPrompt

入力画像からプロンプト用の JSON ファイルを生成するためのプロトタイプ CLI ユーティリティです。

このプロトタイプは以下の抽出モデルを用いて推論を実行します。

* **Florence-2** : キャプション生成
* **WD14** : アニメ向けタグ抽出
* **CLIP Interrogator** : スタイルとライティングのヒント
* **DeepDanbooru** (オプション) : 追加タグ抽出。Windowsでは `tensorflow-io` の問題により非推奨。必要な場合は `tensorflow-cpu==2.12.*` と `tensorflow-io-gcs-filesystem==0.31.0` を手動でインストールしてください。

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
  "negative_prompt": "low quality, worst quality",
  "style": "anime",
  "model_suggestion": "unspecified"
}
```
