# Create Virtual Environment
sudo apt update
sudo apt install python3-venv -y
python3 -m venv .venv_edge

# Activate Environment
source .venv_edge/bin/activate
pip install -r requirements.txt

-----------------------------------

# Libraries
pip install paho-mqtt scikit-learn numpy pandas pm4py streamlit
pip freeze > requirements.txt