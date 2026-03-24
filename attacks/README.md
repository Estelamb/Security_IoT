# Create Virtual Environment
sudo apt update
sudo apt install python3-venv -y
python3 -m venv .venv_attacks

# Activate Environment
source .venv_attacks/bin/activate
.\.venv\Scripts\Activate.ps1 (Windows PowerShell)

pip install -r requirements.txt

# Run UI
streamlit run ui_attacks.py