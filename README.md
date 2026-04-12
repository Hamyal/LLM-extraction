# Voyage charter Part II clause extractor

Python tool that reads **Part II** (legal clauses, pages 6–39 in the reference PDF) of a voyage charter party PDF, normalizes noisy text extraction, and uses an **LLM** to return numbered clauses as JSON (`id`, `title`, `text`). Strike-through / superseded language is excluded per the model instructions (plain PDF text does not always encode strikes; the model is instructed to ignore them).

## Requirements

- Python 3.10+
- An OpenAI API key **or** [Ollama](https://ollama.com/) with a chat model pulled locally

## Setup

```bash
cd charter-clause-extractor
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -e .
copy .env.example .env          # add OPENAI_API_KEY (never commit .env)
```

## Run

```bash
python main.py voyage-charter-example.pdf -o output/part2_clauses.json
# or
python -m charter_clauses voyage-charter-example.pdf -o output/part2_clauses.json
```

`output/part2_clauses.sample.json` contains **two** clauses sliced from the normalized PDF text (structure demo only). A full Part II extraction with strike-through handling and rider numbering is produced by the commands above once an API key or Ollama model is configured.

Options:

- `--first-page` / `--last-page` — default to Part II pages **6–39** for this sample PDF.
- `--page-markers` — inserts `--- Page N ---` markers; use with `OLLAMA_CHUNK=1` for chunked local runs.
- `--no-dedupe-by-id` — by default, clause rows with the same `id` (from overlapping chunks) are merged into one entry; disable for raw model output.

### Local LLM (Ollama)

```bash
set CHARTER_LLM_PROVIDER=ollama
set OLLAMA_MODEL=llama3.2
ollama pull llama3.2
python main.py voyage-charter-example.pdf -o output/part2_clauses.json
```

If context size is insufficient, use page markers and chunking:

```bash
set OLLAMA_CHUNK=1
python main.py --page-markers voyage-charter-example.pdf -o output/part2_clauses.json
```

## GitHub

This folder is ready to push as a new repository (no API keys in git):

```bash
git init
git add .
git commit -m "Add voyage charter Part II clause extractor"
# Create an empty repo on GitHub, then:
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

Invite reviewers via **GitHub → Settings → Collaborators** (or a private repo invite).

## Layout

- `charter_clauses/pdf_extract.py` — PyMuPDF Part II text + normalization
- `charter_clauses/llm_extract.py` — OpenAI structured output (`parse`) or Ollama JSON mode
- `charter_clauses/cli.py` — CLI

## License

MIT (adjust as needed).
