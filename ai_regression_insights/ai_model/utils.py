from datetime import datetime
import logging
import os

def setup_logging(log_file='ai_model.log'):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Logging is set up.")

def load_config(env_file='.env'):
    config = {}
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                key, value = line.strip().split('=')
                config[key] = value
    else:
        logging.warning(f"{env_file} not found. Using default configuration.")
    return config

def save_model(model, filename):
    import joblib
    joblib.dump(model, filename)
    logging.info(f"Model saved to {filename}")

def load_model(filename):
    import joblib
    model = joblib.load(filename)
    logging.info(f"Model loaded from {filename}")
    return model

def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")