# Edge Node Setup & Execution Guide

This document combines the system preparation, MQTT broker configuration, and virtual environment setup for the Anomaly Detector.

---

## 1. MQTT Broker Setup

### Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### Install Mosquitto
```bash
sudo apt install mosquitto mosquitto-clients -y
```

### Enable and Check Status
```bash
sudo systemctl enable mosquitto
sudo systemctl status mosquitto
```

### Configuration
1. Open the configuration file:
```bash
sudo nano /etc/mosquitto/conf.d/local.conf
```

2. Add the following lines:
```plaintext
listener 1883
allow_anonymous true
```

3. Press Ctrl+X, then Y, and Enter to save.

### Restart and Test
```bash
# Restart to apply changes
sudo systemctl restart mosquitto

# Test (Open two terminals)
# Terminal 1: Subscribe
mosquitto_sub -h localhost -t "test/topic"
# Terminal 2: Publish
mosquitto_pub -h localhost -t "test/topic" -m "Hello World"
```

### Stop and Disable Mosquitto
```bash
sudo systemctl stop mosquitto
sudo systemctl disable mosquitto
```

## 2. Virtual Environment Setup 

### Create Virtual Environment
```bash
sudo apt update
sudo apt install graphviz python3-venv -y
python3 -m venv .venv_edge
```

### Install Dependencies
```bash
# Activate Environment
source .venv_edge/bin/activate

# Install Libraries
pip install -r requirements.txt
```

## 3. Run the Anomaly Detector UI

Ensure the MQTT broker is running and the virtual environment is activated before proceeding.
```bash
# Make the launch script executable
chmod +x launch_edge.sh

# Run the Anomaly Detector
./launch_edge.sh
```