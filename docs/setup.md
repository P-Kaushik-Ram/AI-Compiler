# Setup

## Backend

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
# Backend
pytest

# Frontend
cd frontend
npm run test
```
