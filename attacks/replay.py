import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("localhost", 1883)

# Simulating an old packet with an old sequence ID (e.g., seq: 5)
replay_packet = {
    "temperature": 22.0,
    "humidity": 45.0,
    "seq": 5 
}

print("Sending Replay Attack...")
client.publish("device_1/telemetry", json.dumps(replay_packet))
client.disconnect()