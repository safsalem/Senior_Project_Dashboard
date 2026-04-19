# Smart Emissions Control System — Dashboard (Frontend MVP)

## Quick start
```bash
# 1) Create and activate a venv (recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# 2) Install dependencies
pip install django psycopg2-binary python-dotenv

# 3) Configure environment variables (choose one)

# Option A: local .env file (development)
# Create a .env file at project root:
# DB_HOST=senior-project-db.c0dmkqe4mx1g.us-east-1.rds.amazonaws.com
# DB_PORT=5432
# DB_NAME=senior_project
# DB_USER=postgres
# DB_PASSWORD=<your-rds-password>
# DB_SSLMODE=require

# Option B: shell environment variables (development)
# Windows PowerShell:
# $env:DB_HOST="senior-project-db.c0dmkqe4mx1g.us-east-1.rds.amazonaws.com"
# $env:DB_PORT="5432"
# $env:DB_NAME="senior_project"
# $env:DB_USER="postgres"
# $env:DB_PASSWORD="<your-rds-password>"
# $env:DB_SSLMODE="require"

# 4) Run
python manage.py runserver
```

Open: http://127.0.0.1:8000/

## Notes
- This MVP uses **Chart.js via CDN** and dummy data generated server-side.
- Dashboard and alerts now read live data from PostgreSQL (AWS RDS).
- Alerts API invokes `public.check_upload_delay()` before returning records.
- Frontend polls the API every 1 second for live updates.

## Elastic Beanstalk Secret Handling (Recommended)
- Use Elastic Beanstalk environment properties for DB settings, not committed files.
- Prefer AWS Secrets Manager for DB credentials and inject them into environment variables at deploy/startup.
- Keep `.env` for local development only.
- Rotate database credentials after initial setup if they were shared.


## Possible datasets:
- https://archive.ics.uci.edu/dataset/322/gas+sensor+array+under+dynamic+gas+mixtures

- https://archive.ics.uci.edu/dataset/487/gas+sensor+array+temperature+modulation

- https://archive.ics.uci.edu/dataset/270/gas+sensor+array+drift+dataset+at+different+concentrations

- https://archive.ics.uci.edu/dataset/360/air+quality

- https://archive.ics.uci.edu/dataset/551/gas+turbine+co+and+nox+emission+data+set

- https://www.kaggle.com/datasets/sjagkoo7/fuel-gas-emission