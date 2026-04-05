from matplotlib.path import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler


def train_model():
    # Load and preprocess the data
    combined_file = "data/combined_data.csv"
    df = pd.read_csv(combined_file)

    # Preprocess the data
    df = df.dropna()

    # Separate target before scaling
    target_col = "NOX"
    y = df[target_col]

    # Scale numeric feature columns only (exclude target)
    numeric_cols = [c for c in df.select_dtypes(include=['float64', 'int']).columns if c != target_col]
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    # Define features and target variable
    X = df.drop(columns=[target_col])

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize and train the regression model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Make predictions
    y_pred = model.predict(X_test)

    # Evaluate the model (errors are now in original NOX units)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Baseline (predicting training mean)
    baseline_pred = [y_train.mean()] * len(y_test)
    baseline_mse = mean_squared_error(y_test, baseline_pred)

    print(f'Baseline MSE (train mean): {baseline_mse:.4f}')
    print(f'Mean Squared Error: {mse:.4f}')
    print(f'Mean Absolute Error: {mae:.4f}')
    print(f'R-squared: {r2:.4f}')

    # Save the trained model and scaler
    joblib.dump(model, 'trained_model.pkl')
    joblib.dump(scaler, 'scaler.pkl')

if __name__ == "__main__":
    train_model()