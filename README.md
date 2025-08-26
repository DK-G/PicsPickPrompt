# PicsPickPrompt

Prototype CLI utility to generate prompt JSON from an input image.

The current prototype runs real inference using the following
extraction models:

* **Florence-2** for caption generation
* **WD14** for anime-focused tagging
* **CLIP Interrogator** for style and lighting hints

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

On Windows use:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python -m img2prompt.cli path/to/image.jpg
```

On Windows PowerShell or Command Prompt the command is the same:

```powershell
python -m img2prompt.cli path\to\image.jpg
```

The command writes `path/to/image.jpg.prompt.json` containing the prompt data.

Example:

```bash
$ python -m img2prompt.cli examples/sample.jpg
```

The resulting `examples/sample.jpg.prompt.json` looks like:

```json
{
  "caption": "a girl smiling",
  "prompt": "1girl, smile, outdoor",
  "negative_prompt": "low quality, worst quality",
  "style": "anime",
  "model_suggestion": "unspecified"
}
```

## 使い方

以下のコマンドで、入力画像からプロンプトのJSONファイルを生成します。

```bash
python -m img2prompt.cli path/to/image.jpg
```

実行すると `path/to/image.jpg.prompt.json` が作成され、画像から抽出したプロンプト情報が保存されます。
