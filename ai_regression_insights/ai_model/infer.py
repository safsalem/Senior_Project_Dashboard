from sklearn.externals import joblib
import pandas as pd
from ai_model.data import load_data
from ai_model.preprocess import preprocess_data

def load_model(model_path):
    """Load the trained regression model from the specified path."""
    model = joblib.load(model_path)
    return model

def make_predictions(model, data):
    """Make predictions using the trained model on the provided data."""
    predictions = model.predict(data)
    return predictions

def infer(model_path, csv_path):
    """Load data, preprocess it, and make predictions using the trained model."""
    # Load the trained model
    model = load_model(model_path)
    
    # Load and preprocess the data
    data = load_data(csv_path)
    processed_data = preprocess_data(data)
    
    # Make predictions
    predictions = make_predictions(model, processed_data)
    
    return predictions

if __name__ == "__main__":
    model_path = "path/to/your/trained_model.pkl"  # Update with your model path
    csv_path = "path/to/your/new_data.csv"  # Update with your new data path
    predictions = infer(model_path, csv_path)
    print(predictions)