# AI Team Orchestrator

Multi-agent **LangGraph** workflow: researcher → engineer → verifier → methodology writer, with optional **RAG** over a local paper corpus and an Ollama fallback.

> Author: Gleb Voronkov · Apache-2.0

## Features
- LangGraph state machine for multi-step coding / research tasks
- Chroma + `all-MiniLM-L6-v2` retrieval
- DeepSeek via OpenRouter with **local Ollama** fallback (`qwen2.5-coder`)
- Prompt IP anonymization helper
- FastAPI simple UI + optional Telegram bot

## Quickstart
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install openai langgraph chromadb sentence-transformers fastapi uvicorn python-dotenv requests pypdf
copy .env.example .env
# edit .env with your key OR rely on local Ollama
python run_team.py
# or: python web_app.py
```

Put open abstracts / your own public papers into `papers/` and run `ingest_knowledge.py`.

## Safety
- **Never commit** real `.env` files or proprietary PDFs.
- Telegram bot is optional; disable if unused.

## License
Apache-2.0 · `mybook3@mail.ru` · `@Gleb_Voronkov`