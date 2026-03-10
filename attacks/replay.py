import paho.mqtt.client as mqtt
import json
import time

# --- CONFIGURACIÓN ---
BROKER = "localhost"
TOPIC = "device_1/telemetry"

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

try:
    client.connect(BROKER, 1883)
    
    # 1. Enviamos un paquete legítimo con secuencia alta para "avanzar" el detector
    valid_packet = {
        "temperature": 24.5,
        "humidity": 50.0,
        "seq": 50,         # Secuencia actual
        "state": 4
    }
    print(f"📡 Sending valid packet (seq: {valid_packet['seq']})...")
    client.publish(TOPIC, json.dumps(valid_packet), qos=1)
    
    time.sleep(1) # Pausa para asegurar el procesamiento

    # 2. ATAQUE: Reenviamos un paquete capturado previamente con una secuencia menor
    # Esto activará la condición: current_seq <= last_seq
    replay_packet = {
        "temperature": 24.5,
        "humidity": 50.0,
        "seq": 10,         # Secuencia antigua (REPLAY)
        "state": 4
    }
    
    print(f"♻️ Injecting Replay Attack (seq: {replay_packet['seq']})...")
    client.publish(TOPIC, json.dumps(replay_packet), qos=1)
    
    print("✅ Check RPI5 logs for '🚨 ALERT [Replay Attack]'.")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    client.disconnect()