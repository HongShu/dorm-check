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

### Backend (Development)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m scripts.init_db
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then visit http://localhost:8000/docs for API docs.

### Mini-program

Open `miniprogram/` directory in WeChat Developer Tools and configure the backend URL in `utils/config.js`.

---

## Deployment (Ubuntu Server)

### 1. Install system dependencies

```bash
sudo apt update
sudo apt install python3.12-venv nginx
```

### 2. Clone & setup

```bash
git clone https://github.com/HongShu/dorm-check.git
cd dorm-check
sudo bash deploy.sh
```

### 3. Configure environment

Edit `backend/.env` and fill in:

```
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=your-secret-key
```

Then restart the service:

```bash
sudo systemctl restart dorm-check
```

### 4. Manage service

```bash
sudo systemctl status dorm-check   # 查看状态
sudo systemctl restart dorm-check  # 重启
sudo journalctl -u dorm-check -f   # 查看日志
```

### 5. Setup Nginx (optional, for HTTP)

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/dorm-check
# Edit /etc/nginx/sites-available/dorm-check, replace /path/to/dorm-check with actual path
sudo ln -s /etc/nginx/sites-available/dorm-check /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Enable HTTPS with Certbot (optional)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 7. Update mini-program config

In `miniprogram/utils/config.js`, set `baseUrl` to your server domain.

## License

MIT
