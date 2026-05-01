import json
import csv
from pathlib import Path
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render

TIME_RANGE_TO_MINUTES = {"1h": 60, "5h": 300, "10h": 600, "24h": 1440}
TIME_RANGE_TO_HOURS = {"1h": 1, "5h": 5, "10h": 10, "24h": 24}


def _serialize_reading_timestamp(ts):
    if ts is None:
        return ""
    return ts.strftime("%H:%M:%S")


def _serialize_alert_timestamp(ts):
    if ts is None:
        return ""
    return ts.strftime("%Y-%m-%d %H:%M:%S UTC")


def _fetch_timeseries(minutes):
    labels = []
    nox = []
    co = []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT reading_time, nox, co
            FROM public.sensor_readings
            WHERE reading_time >= NOW() - (%s * INTERVAL '1 minute')
            ORDER BY reading_time ASC
            """,
            [minutes],
        )
        for reading_time, nox_value, co_value in cursor.fetchall():
            labels.append(_serialize_reading_timestamp(reading_time))
            nox.append(float(nox_value))
            co.append(float(co_value))

    return labels, nox, co


def _fetch_latest_reading():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT reading_time, temperature, nox, co
            FROM public.sensor_readings
            ORDER BY reading_time DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()

    if not row:
        return {
            "reading_time": None,
            "temperature": 0.0,
            "nox": 0.0,
            "co": 0.0,
        }

    reading_time, temperature, nox_value, co_value = row
    return {
        "reading_time": reading_time,
        "temperature": float(temperature),
        "nox": float(nox_value),
        "co": float(co_value),
    }


def _invoke_upload_delay_check():
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.check_upload_delay();")


def _fetch_alerts(hours):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, alert_time, alert_type, alert_value, status
            FROM public.alerts
            WHERE alert_time >= NOW() - (%s * INTERVAL '1 hour')
            ORDER BY alert_time DESC
            """,
            [hours],
        )
        rows = cursor.fetchall()

    alerts = []
    for row in rows:
        (alert_id, alert_time, alert_type, alert_value, status) = row
        alerts.append(
            {
                "id": str(alert_id) if alert_id else None,
                "time": _serialize_alert_timestamp(alert_time),
                # ISO timestamp for reliable client-side sorting/pagination
                "ts": alert_time.isoformat() if alert_time else "",
                "type": alert_type or "",
                "value": alert_value or "",
                "status": status or "New",
            }
        )
    return alerts


def _update_alert_status(alert_id, new_status):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE public.alerts
            SET status = %s
            WHERE id = %s
            """,
            [new_status, alert_id],
        )
    return True

def dashboard_view(request):
    try:
        labels, nox, co = _fetch_timeseries(TIME_RANGE_TO_MINUTES["1h"])
        latest = _fetch_latest_reading()
        updated_at = _serialize_alert_timestamp(latest["reading_time"])
    except DatabaseError:
        labels, nox, co = [], [], []
        latest = {"temperature": 0.0, "nox": 0.0, "co": 0.0, "reading_time": None}
        updated_at = ""

    context = {
        "labels_json": json.dumps(labels),
        "nox_json": json.dumps(nox),
        "co_json": json.dumps(co),
        "current_nox": latest["nox"],
        "current_co": latest["co"],
        "temp_c": latest["temperature"],
        "updated_at": updated_at,
    }
    return render(request, "dashboard/dashboard.html", context)

def alerts_view(request):
    rng = request.GET.get("range", "1h")
    hours = TIME_RANGE_TO_HOURS.get(rng, 1)

    try:
        # Do NOT invoke the DB-side upload delay check here to avoid blocking page load.
        # The API endpoint can optionally run the check when requested (see alerts_api).
        alerts = _fetch_alerts(hours)
    except DatabaseError:
        alerts = []

    return render(request, "dashboard/alerts.html", {"alerts": alerts, "range": rng})

def insights_view(request):
    from django.shortcuts import redirect
    return redirect('/insights/')

def timeseries_api(request):
    rng = request.GET.get("range", "1h")
    minutes = TIME_RANGE_TO_MINUTES.get(rng, 60)

    try:
        labels, nox, co = _fetch_timeseries(minutes)
        latest = _fetch_latest_reading()
        payload = {
            "labels": labels,
            "nox": nox,
            "co": co,
            "current_nox": latest["nox"],
            "current_co": latest["co"],
            "temp_c": latest["temperature"],
            "updated_at": _serialize_alert_timestamp(latest["reading_time"]),
        }
    except DatabaseError as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    return JsonResponse(payload)

def alerts_api(request):
    rng = request.GET.get("range", "1h")
    hours = TIME_RANGE_TO_HOURS.get(rng, 1)
    # Optional query params:
    #   check=1   -> invoke DB-side upload delay check (expensive)
    #   only_new=1 -> return only alerts with status 'New'
    do_check = str(request.GET.get("check", "0")).lower() in ("1", "true", "yes")
    only_new = str(request.GET.get("only_new", "0")).lower() in ("1", "true", "yes")

    try:
        if do_check:
            _invoke_upload_delay_check()
        alerts = _fetch_alerts(hours)
    except DatabaseError as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    if only_new:
        alerts = [a for a in alerts if a.get("status") == 'New']

    return JsonResponse({"alerts": alerts, "range": rng})


def acknowledge_alert_api(request):
    # Accept POST JSON or GET param for quick tests
    alert_id = request.GET.get("id")
    if not alert_id and request.body:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            alert_id = alert_id or payload.get("id")
        except Exception:
            alert_id = alert_id

    if not alert_id:
        return JsonResponse({"error": "missing id"}, status=400)

    try:
        _update_alert_status(alert_id, "Acknowledged")
    except DatabaseError as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    return JsonResponse({"ok": True, "id": alert_id, "status": "Acknowledged"})


def resolve_alert_api(request):
    alert_id = request.GET.get("id")
    if not alert_id and request.body:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            alert_id = alert_id or payload.get("id")
        except Exception:
            alert_id = alert_id

    if not alert_id:
        return JsonResponse({"error": "missing id"}, status=400)

    try:
        _update_alert_status(alert_id, "Resolved")
    except DatabaseError as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    return JsonResponse({"ok": True, "id": alert_id, "status": "Resolved"})


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
