import paho.mqtt.client as mqtt
import json
import time

# Configuration
BROKER = "localhost"
TOPIC = "device_1/telemetry"

client = mqtt.Client()
client.connect(BROKER, 1883)

print("Starting Data Injection Attack...")

# Sending a physically impossible value (e.g., 150°C)
# This will be caught by your Isolation Forest model
fake_data = {
    "temperature": 150.0,
    "humidity": 5.0
}

client.publish(TOPIC, json.dumps(fake_data))
print(f"Sent malicious payload: {fake_data}")
client.disconnect()