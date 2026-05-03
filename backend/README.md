# TestForge AI Backend

FastAPI backend for TestForge AI. It accepts requirement text, generates structured QA assets through a provider abstraction, stores results in SQLite, and exports Markdown.

## Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/api/generate` | Generate and persist QA output |
| `GET` | `/api/generations` | List saved outputs |
| `GET` | `/api/generations/{id}` | Fetch one output |
| `GET` | `/api/generations/{id}/export` | Export Markdown |
| `POST` | `/api/documents` | Index supporting text for RAG |
| `GET` | `/api/documents` | List indexed documents |
| `POST` | `/api/evals/run` | Run mock-provider eval fixtures |

## Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.

## Tests

```bash
pytest
```

Current backend tests cover generation success, validation errors, history, history ordering, 404s, Markdown export, mock determinism, provider fallback, document indexing, RAG retrieval, guardrails, and eval scoring.

## Provider Selection

Mock generation is the default and requires no key:

```env
AI_PROVIDER=mock
PROMPT_VERSION=qa_generation_v1
RAG_RETRIEVAL_TOP_K=3
```

OpenAI is optional:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

If `AI_PROVIDER=openai` is set but `OPENAI_API_KEY` is missing, the app falls back to the mock provider.
