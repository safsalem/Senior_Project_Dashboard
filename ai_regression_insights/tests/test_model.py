from ai_model.train import train_model
from ai_model.evaluate import evaluate_model
import pandas as pd
import pytest

def test_train_model():
    # Load the combined dataset
    data = pd.read_csv('path/to/combined_data.csv')  # Update with the actual path
    X = data.drop('target_column', axis=1)  # Replace 'target_column' with the actual target variable
    y = data['target_column']

    # Train the model
    model = train_model(X, y)

    # Check if the model is trained
    assert model is not None

def test_evaluate_model():
    # Load the combined dataset
    data = pd.read_csv('path/to/combined_data.csv')  # Update with the actual path
    X = data.drop('target_column', axis=1)  # Replace 'target_column' with the actual target variable
    y = data['target_column']

    # Train the model
    model = train_model(X, y)

    # Evaluate the model
    metrics = evaluate_model(model, X, y)

    # Check if metrics are returned
    assert metrics is not None
    assert 'R_squared' in metrics
    assert 'MAE' in metrics
    assert 'MSE' in metrics
    assert metrics['R_squared'] >= 0  # R-squared should be non-negative
    assert metrics['MAE'] >= 0  # MAE should be non-negative
    assert metrics['MSE'] >= 0  # MSE should be non-negative