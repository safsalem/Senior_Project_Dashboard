# Smart Emissions Control System — Dashboard (Frontend MVP)

## Quick start
```bash
# 1) Create and activate a venv (recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# 2) Install Django
pip install django

# 3) Run
python manage.py runserver
```

Open: http://127.0.0.1:8000/

## Notes
- This MVP uses **Chart.js via CDN** and dummy data generated server-side.
- Replace dummy data with real sensor/API data later (e.g., AWS API / MQTT / REST).


## Possible datasets:
- https://archive.ics.uci.edu/dataset/322/gas+sensor+array+under+dynamic+gas+mixtures

- https://archive.ics.uci.edu/dataset/487/gas+sensor+array+temperature+modulation

- https://archive.ics.uci.edu/dataset/270/gas+sensor+array+drift+dataset+at+different+concentrations

- https://archive.ics.uci.edu/dataset/360/air+quality

- https://archive.ics.uci.edu/dataset/551/gas+turbine+co+and+nox+emission+data+set

- https://www.kaggle.com/datasets/sjagkoo7/fuel-gas-emission