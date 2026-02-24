import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import render

def _make_series(minutes=60, base=250, swing=140, seed=7):
    # Deterministic pseudo-random series (no external deps)
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

    # "Now" is based on the newest alert timestamp so the demo always shows results.
    # Later, replace with datetime.utcnow().
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

    # Dummy ambient temperature for UI (replace with real sensor later)
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
    # Server-render initial 1h alerts (so the page loads without JS too)
    rng = request.GET.get("range", "1h")
    alerts = _filter_alerts_by_range(_dummy_alerts(), rng)
    return render(request, "dashboard/alerts.html", {"alerts": alerts, "range": rng})

def insights_view(request):
    return render(request, "dashboard/insights.html")

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
