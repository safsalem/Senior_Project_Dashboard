from django.shortcuts import render
from ai_regression_insights.ai_model.train import train_model
import joblib
import pandas as pd
from pathlib import Path

def ai_insights_view(request):
    # Train the model (train_model now loads data internally and saves the trained model)
    train_model()

    # Compute project root so paths resolve correctly
    project_root = Path(__file__).resolve().parents[2]

    # Try to load the trained model (optional)
    model_path = project_root / "ai_regression_insights" / "ai_model" / "trained_model.pkl"
    model = None
    if model_path.exists():
        model = joblib.load(model_path)

    # Load combined data for display (top-level data/combined_data.csv)
    data_file = project_root / "data" / "combined_data.csv"
    data = pd.DataFrame()
    if data_file.exists():
        data = pd.read_csv(data_file)

    results = {
        'metrics': {},              # evaluation metrics can be added if available
        'data': data.head(),        # Display first few rows of the combined data
    }

    return render(request, 'dashboard/ai_insights.html', results)