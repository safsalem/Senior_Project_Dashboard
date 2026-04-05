#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Run the training script
python -m ai_model.train

# Deactivate the virtual environment
deactivate