# LLM Playground Projects

A personal playground for **LLM engineering experiments** — notebooks + small Python scripts around:
- LLM APIs (OpenAI / Anthropic / Gemini)
- RAG + vector stores (ChromaDB)
- LangChain utilities
- Gradio demos / quick UIs
- Data + evaluation workflows (datasets, sklearn, pandas, plotly, etc.)

Repo: https://github.com/eliacharfe/llm-projects

---

## What’s inside

High-level structure (as of today):

    .
    ├── scripts/           # runnable scripts & small experiments
    ├── setup/             # setup helpers (env / tooling)
    ├── prices.db          # local sqlite db used by some experiments
    ├── pyproject.toml     # project deps (Python >= 3.11)
    ├── requirements.txt   # pip-friendly deps list
    ├── environment.yml    # conda environment definition
    ├── uv.lock            # uv lockfile (if you use uv)
    └── README.md

---

## Requirements

- Python 3.11+ (see `.python-version` + `pyproject.toml`)
- One of:
  - uv (recommended)
  - pip
  - conda

---

## Quickstart (recommended: uv)

    # 1) create & activate venv (uv manages it for you)
    uv venv
    source .venv/bin/activate  # macOS/Linux
    .venv\Scripts\activate     # Windows (PowerShell)

    # 2) install deps (uses pyproject.toml / uv.lock if present)
    uv pip install -r requirements.txt
    # or:
    uv sync

Run something:

    python -m scripts.<your_script_module>

---

## Quickstart (pip)

    python -m venv .venv
    source .venv/bin/activate  # macOS/Linux
    .venv\Scripts\activate     # Windows (PowerShell)

    pip install -r requirements.txt

---

## Quickstart (conda)

    conda env create -f environment.yml
    conda activate llms

---

## Environment variables (API keys)

Create a `.env` in the repo root:

    OPENAI_API_KEY=...
    ANTHROPIC_API_KEY=...
    GOOGLE_API_KEY=...
    GEMINI_API_KEY=...

Then load it in Python:

    from dotenv import load_dotenv
    load_dotenv()

---

## Notebooks

    pip install ipykernel
    python -m ipykernel install --user --name llm-projects --display-name "llm-projects"
    jupyter lab

---

## Gradio demos

    python app.py
    # or:
    python -m scripts.<something_gradio>

---

## Tips

- If you’re doing RAG experiments, keep large artifacts out of git:
  - vector stores / embeddings caches
  - downloaded datasets
- Prefer reproducible installs:
  - uv + uv.lock
  - or conda env for OS-level consistency

---

## License

MIT — see LICENSE.
