import paho.mqtt.client as mqtt
import json

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", 1883)

# Salto imposible: de estado 0 (Cold/Dry) a estado 8 (Hot/Humid) 
# saltándose toda la lógica de transición física
markov_attack = {
    "temperature": 35.0,
    "humidity": 80.0,
    "seq": 500,
    "state": 8 
}

print("🧠 Sending Impossible State Transition (Markov Attack)...")
client.publish("device_1/telemetry", json.dumps(markov_attack))
client.disconnect()