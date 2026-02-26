import paho.mqtt.client as mqtt
import json

BROKER = "localhost"
TOPIC = "device_1/telemetry"

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, 1883)

print("🚀 Starting Aggressive Flooding Attack...")

for i in range(100):
    # Enviamos datos con secuencia rápida para disparar la alerta de FLOODING
    flood_data = {
        "temperature": 25.0, 
        "humidity": 50.0, 
        "seq": i,
        "state": 4  # Estado Normal/Normal
    }
    client.publish(TOPIC, json.dumps(flood_data))
    
print("Flood complete. Check RPi for DoS alerts.")
client.disconnect()