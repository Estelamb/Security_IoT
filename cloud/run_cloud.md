# Cloud Node Setup & Execution Guide

This document combines the system preparation, and virtual environment setup for the cloud dashboard.

---

## 1. Virtual Environment Setup 

### Create Virtual Environment
```bash
sudo apt update
sudo apt install graphviz python3-venv -y
python3 -m venv .venv_cloud
```

### Install Dependencies
```bash
# Activate Environment
source .venv_cloud/bin/activate

# Install Libraries
pip install paho-mqtt scikit-learn numpy pandas pm4py streamlit streamlit-autorefresh

# Save Requirements
pip freeze > requirements.txt
```

## 2. Run the Cloud Dashboard

Ensure the virtual environment is activated before proceeding.
```bash
# Run the Cloud Dashboard
streamlit run dashboard.py
```