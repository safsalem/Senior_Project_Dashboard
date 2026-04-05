# AI Regression Insights Project

This project aims to build an AI regression model using combined CSV data related to NOX emissions and temperature. The model will be trained to predict NOX levels based on temperature-related features. The results will be visualized and integrated into a dashboard for insights.

## Project Structure

- **ai_model/**: Contains the core functionality for data handling, preprocessing, feature engineering, model training, inference, and evaluation.
  - `__init__.py`: Initializes the ai_model package.
  - `data.py`: Loads and combines CSV data into a single DataFrame.
  - `preprocess.py`: Handles data cleaning and preprocessing.
  - `features.py`: Defines feature selection and engineering functions.
  - `train.py`: Contains logic for training the regression model.
  - `infer.py`: Provides functions for making predictions with the trained model.
  - `evaluate.py`: Evaluates model performance and calculates metrics.
  - `utils.py`: Contains utility functions used across modules.

- **notebooks/**: Contains Jupyter notebooks for analysis and training.
  - `correlation.ipynb`: Computes correlation matrices for NOX and temperature.
  - `training.ipynb`: Used for training the regression model.

- **dashboard_integration/**: Integrates the AI insights into the dashboard.
  - `views.py`: Contains view functions for rendering the AI insights page.
  - `urls.py`: Defines URL patterns for dashboard integration.
  - `templates/dashboard/ai_insights.html`: Displays visualizations and results.

- **tests/**: Contains unit tests for the project.
  - `test_data.py`: Tests for data loading and preprocessing functions.
  - `test_model.py`: Tests for model training and evaluation functions.

- **scripts/**: Contains scripts for automation.
  - `run_training.sh`: Automates the training process.

- **requirements.txt**: Lists dependencies required for the project.

- **.env.example**: Provides an example of environment variables needed for the project.

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd ai_regression_insights
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables by copying `.env.example` to `.env` and modifying as necessary.

5. Run the training script to train the regression model:
   ```
   bash scripts/run_training.sh
   ```

## Usage

After training the model, you can access the AI insights through the dashboard. The insights page will display visualizations and metrics related to the regression model's performance.

## Overview

This project combines data analysis, machine learning, and web development to provide insights into NOX emissions based on temperature data. The modular structure allows for easy updates and maintenance of the codebase.