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


def _trim_trailing_empty(row):
    cleaned = [(cell or "").strip() for cell in row]
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return cleaned


def _read_csv_table(file_path):
    rows = []
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            rows.append(_trim_trailing_empty(row))

    if not rows:
        return {"headers": [], "rows": []}

    headers = rows[0]
    body = rows[1:]
    return {"headers": headers, "rows": body}


def _find_column_index(headers, column_name):
    target = column_name.strip().lower()
    for index, header in enumerate(headers):
        if (header or "").strip().lower() == target:
            return index
    return -1


def _extract_flue_gas_metrics(composition_table, material_table):
    no_value = 0.0
    no2_value = 0.0
    co_value = 0.0
    o2_value = 0.0
    temperature_value = 0.0

    composition_headers = composition_table.get("headers", [])
    composition_rows = composition_table.get("rows", [])
    composition_flue_index = _find_column_index(composition_headers, "Flue Gas")

    if composition_flue_index >= 0:
        for row in composition_rows:
            if len(row) <= composition_flue_index:
                continue

            metric_name = (row[0] if row else "").strip()
            metric_value = _safe_float(row[composition_flue_index])

            if metric_name == "Comp Mole Frac (NO)":
                no_value = metric_value
            elif metric_name == "Comp Mole Frac (NO2)":
                no2_value = metric_value
            elif metric_name == "Comp Mole Frac (CO)":
                co_value = metric_value
            elif metric_name == "Comp Mole Frac (Oxygen)":
                o2_value = metric_value

    material_headers = material_table.get("headers", [])
    material_rows = material_table.get("rows", [])
    material_flue_index = _find_column_index(material_headers, "Flue Gas")

    if material_flue_index >= 0:
        for row in material_rows:
            if len(row) <= material_flue_index:
                continue
            metric_name = (row[0] if row else "").strip()
            if metric_name == "Temperature":
                temperature_value = _safe_float(row[material_flue_index])
                break

    nox_value = round(no_value + no2_value, 12)
    nox_ppm = round(nox_value * 1_000_000, 6)
    co_ppm = round(co_value * 1_000_000, 6)
    return {
        "temperature": round(temperature_value, 6),
        "nox": nox_value,
        "nox_ppm": nox_ppm,
        "co": round(co_value, 12),
        "co_ppm": co_ppm,
        "o2": round(o2_value, 12),
    }


def _load_simulation_dataset():
    root_dir = Path(__file__).resolve().parents[1]
    csv_dir = root_dir / "CasesAFR" / "csv"

    cases = {}
    lambda_points = []
    nox_points = []
    co_points = []
    o2_points = []
    temperature_points = []

    for composition_file in sorted(csv_dir.glob("Compositions_*.csv")):
        suffix = composition_file.stem.replace("Compositions_", "")
        try:
            lambda_value = float(suffix)
        except ValueError:
            continue

        lambda_key = f"{lambda_value:.1f}"
        material_file = csv_dir / f"Material_Streams_{suffix}.csv"

        composition_table = _read_csv_table(composition_file)
        material_table = _read_csv_table(material_file) if material_file.exists() else {"headers": [], "rows": []}

        metrics = _extract_flue_gas_metrics(composition_table, material_table)
        composition_rows = composition_table.get("rows", [])
        displayed_composition = {
            "headers": composition_table.get("headers", []),
            "rows": composition_rows[:-2] if len(composition_rows) > 2 else composition_rows,
        }

        cases[lambda_key] = {
            "metrics": metrics,
            "compositions": displayed_composition,
            "material_streams": material_table,
        }

        lambda_points.append(round(lambda_value, 3))
        nox_points.append(metrics["nox_ppm"])
        co_points.append(metrics["co_ppm"])
        o2_points.append(metrics["o2"])
        temperature_points.append(metrics["temperature"])

    return {
        "cases": cases,
        "series": {
            "lambdas": lambda_points,
            "nox": nox_points,
            "co": co_points,
            "o2": o2_points,
            "temperature": temperature_points,
        },
    }


def simulation_results_view(request):
    dataset = _load_simulation_dataset()
    selector_values = ["0.8", "0.9", "1.0", "1.1", "1.2", "all"]
    available = [value for value in selector_values if value != "all" and value in dataset.get("cases", {})]
    context = {
        "simulation_data_json": json.dumps(dataset),
        "selector_values": selector_values,
        "default_selection": available[0] if available else "0.8",
    }
    return render(request, "dashboard/simulation_results.html", context)
