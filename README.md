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
