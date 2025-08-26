# PicsPickPrompt

Prototype CLI utility to generate prompt JSON from an input image.

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python -m img2prompt.cli path/to/image.jpg
```

The command writes `path/to/image.jpg.prompt.json` containing the prompt data.

## 使い方

以下のコマンドで、入力画像からプロンプトのJSONファイルを生成します。

```bash
python -m img2prompt.cli path/to/image.jpg
```

実行すると `path/to/image.jpg.prompt.json` が作成され、画像から抽出したプロンプト情報が保存されます。
