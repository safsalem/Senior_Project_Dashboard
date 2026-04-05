from django.shortcuts import render, redirect
from ai_regression_insights.ai_model.train import train_model
import joblib
import pandas as pd
from pathlib import Path
import json


def ai_insights_view(request):
    # Compute project root so paths resolve correctly
    project_root = Path(__file__).resolve().parents[2]

    # Paths inside the package
    model_path = project_root / "ai_regression_insights" / "ai_model" / "trained_model.pkl"
    metrics_path = project_root / "ai_regression_insights" / "ai_model" / "metrics.json"

    metrics = {}

    # If this is a retrain request, run training and update metrics
    if request.method == 'POST' and request.POST.get('retrain'):
        try:
            metrics = train_model() or {}
            # redirect with flag so GET can show success without using messages middleware
            return redirect(request.path + '?retrained=success')
        except Exception:
            metrics = {}
            return redirect(request.path + '?retrained=failure')

    # On GET, try to read persisted metrics if available
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
        except Exception:
            metrics = {}

    # Try to load the trained model (optional)
    model = None
    if model_path.exists():
        try:
            model = joblib.load(model_path)
        except Exception:
            model = None

    # Load combined data for display (top-level data/combined_data.csv)
    data_file = project_root / "data" / "combined_data.csv"
    data = pd.DataFrame()
    if data_file.exists():
        data = pd.read_csv(data_file)

    # Convert a random sample of rows to an HTML table for embedding in the template
    data_html = ''
    try:
        # allow optional GET param to control sample size (e.g. ?sample=10)
        try:
            sample_size = int(request.GET.get('sample', 5))
        except Exception:
            sample_size = 5

        if not data.empty:
            n = min(max(1, sample_size), len(data))
            sample_df = data.sample(n=n)
            data_html = sample_df.to_html(border=0, classes='table', index=False)
        else:
            data_html = ''
    except Exception:
        data_html = ''

    retrained_flag = request.GET.get('retrained')
    results = {
        'metrics': metrics,              # evaluation metrics
        'data': data_html,               # HTML snippet
        'retrain_status': retrained_flag,  # 'success', 'failure', or None
    }

    return render(request, 'dashboard/ai_insights.html', results)