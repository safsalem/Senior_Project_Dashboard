from sklearn.feature_selection import SelectKBest, f_regression
import pandas as pd

def select_features(X, y, k=10):
    """
    Select the top k features based on univariate statistical tests.
    
    Parameters:
    X (pd.DataFrame): The input features.
    y (pd.Series): The target variable.
    k (int): The number of top features to select.
    
    Returns:
    pd.DataFrame: The selected features.
    """
    selector = SelectKBest(score_func=f_regression, k=k)
    selector.fit(X, y)
    mask = selector.get_support()
    selected_features = X.loc[:, mask]
    return selected_features

def engineer_features(df):
    """
    Perform feature engineering on the DataFrame.
    
    Parameters:
    df (pd.DataFrame): The input DataFrame.
    
    Returns:
    pd.DataFrame: The DataFrame with engineered features.
    """
    # Example of feature engineering: creating interaction terms or polynomial features
    df['AT_squared'] = df['AT'] ** 2
    df['TIT_squared'] = df['TIT'] ** 2
    df['TAT_squared'] = df['TAT'] ** 2
    
    # Add more feature engineering steps as needed
    return df