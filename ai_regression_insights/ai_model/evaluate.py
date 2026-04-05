from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
import joblib

def evaluate_model(model_path, X_test, y_test):
    model = joblib.load(model_path)
    predictions = model.predict(X_test)

    mse = mean_squared_error(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    metrics = {
        'Mean Squared Error': mse,
        'Mean Absolute Error': mae,
        'R-squared': r2
    }

    return metrics

def print_evaluation_metrics(metrics):
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")