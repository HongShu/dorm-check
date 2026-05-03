# dorm-check

A lightweight dormitory check management system for schools. Dorm supervisors submit nightly check records via WeChat mini-program, anomalies are auto-detected by rules, and Claude LLM generates a concise daily report for administrators.

## Features

- **Dorm Supervisor (Mini-program)**: View assigned building, submit nightly check records with one tap
- **Auto Anomaly Detection**: Rules-based detection (present but should be absent / absent but should be present)
- **LLM-powered Report**: Claude Haiku generates a natural language summary for administrators
- **Admin Dashboard**: View all buildings progress, anomaly details, export records

## Tech Stack

- **Backend**: Python 3.10+ / FastAPI / SQLAlchemy 2.0 / SQLite
- **Frontend**: WeChat Mini-program (native framework)
- **LLM**: Anthropic Claude API (claude-haiku-4-5)

## Project Structure

```
dorm-check/
├── backend/              # FastAPI backend
│   ├── main.py
│   ├── models/           # SQLAlchemy models
│   ├── routers/          # API routes
│   ├── services/         # Business logic
│   └── schemas/          # Pydantic schemas
├── miniprogram/          # WeChat mini-program
└── docs/                 # Requirements document
```

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m scripts.init_db
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Mini-program

Open `miniprogram/` directory in WeChat Developer Tools and configure the backend URL in `utils/config.js`.

## License

MIT
