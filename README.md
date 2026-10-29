# Course Starting Point

Capstone Project, NOVA IMS. Week 1.

This already works. You do not have to create files or paste code.
Follow the setup below and you will end up with an AI web app running on your
own laptop.

## Setup

**1. Install uv** (once, on your machine)

Windows, in PowerShell:
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

macOS or Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

uv handles Python, the virtual environment and the packages. It replaces `pip`,
`venv` and `pyenv`. You do not need to install Python first.

**2. Install the dependencies**

```bash
uv sync
```

**3. Create your key**

Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and create a key.
Copy `.env.example` to `.env` and paste the key into the `GOOGLE_API_KEY` line.

`.env` is in `.gitignore`. Never put a key inside a `.py` file or a notebook:
that is the most common way keys leak onto GitHub.

**4. Check everything is in place**

```bash
uv run python check_setup.py
```

Each FAIL line tells you which piece is missing and what to do next.
Work through them in order and run it again until everything says OK.

## Running

```bash
uv run python hello_ai.py          # the simplest possible API call
uv run streamlit run app.py        # the web app
```

## Files

| File | What it does |
|---|---|
| `config.py` | model, temperature, key. Everything you tune lives here |
| `hello_ai.py` | one API call, nothing around it |
| `app.py` | Streamlit chat interface |
| `check_setup.py` | environment diagnostic |
| `.env` | your key. Never reaches GitHub |

## Notebooks

You do not need to install Jupyter. Install the **Jupyter** extension in VS Code
and open the class notebooks directly in the editor. When it asks for a kernel,
pick the `.venv` in this folder.

## About the technical choices

In class we use Google Gemini, Streamlit and, later on, Langfuse.
These are recommendations and what we teach, not project requirements.

What the project requires is an LLM, an interface, tracing and clean
architecture. Which provider or tool you use for each of those pieces is your
call, and the margin is wide: other LLM providers, other databases, other
frontends, other tracing tools. We only ask that you justify the decision and
agree it with the instructor beforehand.

Learn from what we teach. Do not feel bound by it.
