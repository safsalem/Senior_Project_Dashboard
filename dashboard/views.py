import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from django.http import JsonResponse
from django.shortcuts import render

def _make_series(minutes=60, base=250, swing=140, seed=7):
    # Deterministic pseudo-random series
    x = []
    y = []
    t0 = datetime.utcnow() - timedelta(minutes=minutes)
    for i in range(minutes + 1):
        ts = t0 + timedelta(minutes=i)
        val = base + (swing * (0.6 * (i / max(1, minutes)) - 0.3))
        val += ((i * 37 + seed * 101) % 23) - 11  # small ripple
        val = max(0, round(val, 1))
        x.append(ts.strftime("%H:%M"))
        y.append(val)
    return x, y

def _dummy_alerts():
    # Newest first
    return [
        {"time": "2026-02-19 10:42", "type": "CO High", "value": "312 ppm", "status": "Acknowledged"},
        {"time": "2026-02-19 10:15", "type": "NOx Spike", "value": "410 ppm", "status": "New"},
        {"time": "2026-02-19 09:58", "type": "CO High", "value": "305 ppm", "status": "Resolved"},
        {"time": "2026-02-19 09:31", "type": "NOx Spike", "value": "395 ppm", "status": "Resolved"},
        {"time": "2026-02-19 09:05", "type": "System Notice", "value": "Upload delay", "status": "Acknowledged"},
        {"time": "2026-02-19 08:40", "type": "CO High", "value": "301 ppm", "status": "Resolved"},
        {"time": "2026-02-19 07:55", "type": "NOx Spike", "value": "372 ppm", "status": "Resolved"},
        {"time": "2026-02-18 23:10", "type": "System Notice", "value": "Maintenance window", "status": "Resolved"},
    ]

def _filter_alerts_by_range(alerts, rng):
    # Query param: range=1h|5h|10h|24h (fallback 1h)
    mapping = {"1h": 1, "5h": 5, "10h": 10, "24h": 24}
    hours = mapping.get(rng, 1)

    # "Now" is based on the newest alert timestamp.
    newest = max(datetime.strptime(a["time"], "%Y-%m-%d %H:%M") for a in alerts)
    cutoff = newest - timedelta(hours=hours)

    out = []
    for a in alerts:
        t = datetime.strptime(a["time"], "%Y-%m-%d %H:%M")
        if t >= cutoff:
            out.append(a)
    return out

def dashboard_view(request):
    labels, nox = _make_series(minutes=60, base=280, swing=180, seed=7)
    _, co = _make_series(minutes=60, base=80, swing=70, seed=3)

    # Current readings (latest point)
    current_nox = nox[-1] if nox else 0
    current_co = co[-1] if co else 0

    # Dummy ambient temperature for UI
    temp_c = round(27.0 + (((len(labels) * 13) % 7) - 3) * 0.6, 1)

    context = {
        "labels_json": json.dumps(labels),
        "nox_json": json.dumps(nox),
        "co_json": json.dumps(co),
        "current_nox": current_nox,
        "current_co": current_co,
        "temp_c": temp_c,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }
    return render(request, "dashboard/dashboard.html", context)

def alerts_view(request):
    # Server-render initial 1h alerts
    rng = request.GET.get("range", "1h")
    alerts = _filter_alerts_by_range(_dummy_alerts(), rng)
    return render(request, "dashboard/alerts.html", {"alerts": alerts, "range": rng})

def insights_view(request):
    from django.shortcuts import redirect
    return redirect('/insights/')

def timeseries_api(request):
    rng = request.GET.get("range", "1h")
    mapping = {"1h": 60, "5h": 300, "10h": 600, "24h": 1440}
    minutes = mapping.get(rng, 60)

    labels, nox = _make_series(minutes=minutes, base=280, swing=180, seed=7)
    _, co = _make_series(minutes=minutes, base=80, swing=70, seed=3)
    return JsonResponse({"labels": labels, "nox": nox, "co": co})

def alerts_api(request):
    rng = request.GET.get("range", "1h")
    alerts = _filter_alerts_by_range(_dummy_alerts(), rng)
    return JsonResponse({"alerts": alerts, "range": rng})


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _extract_component_fractions(file_path):
    co_fraction = 0.0
    no_fraction = 0.0
    no2_fraction = 0.0

    with open(file_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if len(row) < 4:
                continue

            metric_name = (row[0] or "").strip()
            combustion_gas_value = _safe_float(row[2])

            if metric_name == "Comp Mole Frac (CO)":
                co_fraction = combustion_gas_value
            elif metric_name == "Comp Mole Frac (NO)":
                no_fraction = combustion_gas_value
            elif metric_name == "Comp Mole Frac (NO2)":
                no2_fraction = combustion_gas_value

    # Convert mole fractions to ppm for easier comparison on charts.
    co_ppm = round(co_fraction * 1_000_000, 3)
    nox_ppm = round((no_fraction + no2_fraction) * 1_000_000, 3)
    return {"co_ppm": co_ppm, "nox_ppm": nox_ppm}


def _load_simulation_series():
    root_dir = Path(__file__).resolve().parents[1]
    csv_dir = root_dir / "CasesAFR" / "csv"

    lambda_points = []
    nox_points = []
    co_points = []

    for composition_file in sorted(csv_dir.glob("Compositions_*.csv")):
        suffix = composition_file.stem.replace("Compositions_", "")
        try:
            lambda_value = float(suffix)
        except ValueError:
            continue

        extracted = _extract_component_fractions(composition_file)
        lambda_points.append(round(lambda_value, 3))
        nox_points.append(extracted["nox_ppm"])
        co_points.append(extracted["co_ppm"])

    return {
        "lambdas": lambda_points,
        "nox": nox_points,
        "co": co_points,
    }


def simulation_results_view(request):
    series = _load_simulation_series()
    selector_values = ["0.8", "0.9", "1.0", "1.1", "1.2", "all"]
    context = {
        "simulation_series_json": json.dumps(series),
        "selector_values": selector_values,
        "default_selection": "0.8",
    }
    return render(request, "dashboard/simulation_results.html", context)
