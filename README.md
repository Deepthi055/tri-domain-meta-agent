# TriDomain Meta-Agent

A FastAPI-based multi-domain AI assistant that supports Career, Health, and Finance guidance. The project includes both a standard meta-agent pipeline and a LangChain-powered comparison endpoint.

## Features

- FastAPI server with routes for auth, user profiles, memory, chat, reports, and domain queries.
- Domain-specific agents for career, health, and finance.
- LangChain-powered agents via `/query-langchain` for comparison testing.
- RAG retrieval support using a FAISS index and sentence-transformers.
- Local SQLite database for user authentication and persistence.

## Setup

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
```

2. Install the optional sentence-transformers dependency used by RAG:

```powershell
.venv\Scripts\python -m pip install sentence-transformers
```

3. Create or update `.env` with your `HF_TOKEN` and any other secrets:

```text
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=hf_...
```

4. Build the FAISS index for RAG retrieval:

```powershell
.venv\Scripts\python rag\embedder.py
```

## Running the app

Start the FastAPI server using the workspace virtual environment:

```powershell
.venv\Scripts\python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- `http://127.0.0.1:8000/api-status` — health check
- `http://127.0.0.1:8000/domains` — available domains
- `http://127.0.0.1:8000/docs` — Swagger UI

## Authentication

### Register

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/register -Body '{"name":"Test User","email":"test@example.com","password":"secret"}' -ContentType 'application/json'
```

### Login

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/login -Body @{username='test@example.com'; password='secret'} -ContentType 'application/x-www-form-urlencoded'
```

The login response returns `access_token` used for authenticated requests.

## Query Endpoints

### Standard meta-agent

```powershell
$token = (Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/login -Body @{username='test@example.com'; password='secret'} -ContentType 'application/x-www-form-urlencoded').access_token
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/query -Headers @{Authorization = "Bearer $token"} -Body '{"name":"Test User","age":30,"query":"I need finance advice","domain":"finance","monthly_income":50000,"monthly_expenses":35000,"expenses":{"total":35000}}' -ContentType 'application/json'
```

### LangChain-powered meta-agent

```powershell
$token = (Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/login -Body @{username='test@example.com'; password='secret'} -ContentType 'application/x-www-form-urlencoded').access_token
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/query-langchain -Headers @{Authorization = "Bearer $token"} -Body '{"name":"Test User","age":30,"query":"I need finance advice","domain":"finance","monthly_income":50000,"monthly_expenses":35000,"expenses":{"total":35000}}' -ContentType 'application/json'
```

## Notes

- Use `.venv\Scripts\python` to ensure the project virtual environment is used.
- `LangChain` endpoints are powered by `langchain_groq`, `langchain_core`, and `langgraph`.
- If you see deprecation warnings for `create_react_agent`, the code still works but should be updated to `from langchain.agents import create_agent` in the future.

## Troubleshooting

### HF_TOKEN not working
- Ensure `.env` contains a valid Hugging Face token:
  ```text
  HF_TOKEN=hf_...
  ```
- If using PowerShell for testing, set it in the session too:
  ```powershell
  $env:HF_TOKEN = "hf_..."
  ```
- The token is required for authenticated Hugging Face downloads and RAG retrieval.

### `pydantic[email]` required
- If you see an import error for `email_validator`, install it with:
  ```powershell
  .venv\Scripts\python -m pip install "pydantic[email]"
  ```
- This is needed because Pydantic validates email fields used by auth schemas.

### `FAISS index not found`
- Build the FAISS index before using RAG functionality:
  ```powershell
  .venv\Scripts\python rag\embedder.py
  ```
- If you still see the error, make sure `rag\tridomain_index.faiss` and `rag\tridomain_meta.pkl` exist.

## Tests

Run the test suite:

```powershell
.venv\Scripts\python -m pytest -q
```

## Cleanup

Stop the server with CTRL+C in the terminal running uvicorn.
