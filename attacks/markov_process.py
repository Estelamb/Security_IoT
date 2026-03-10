import paho.mqtt.client as mqtt
import json
import time

# --- CONFIGURACIÓN ---
BROKER = "localhost"
TOPIC = "device_1/telemetry"

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

try:
    client.connect(BROKER, 1883)
    print("🧠 Starting Markov Process Tampering...")

    # 1. Establecemos un estado inicial "Frío/Seco" (Estado 0)
    setup_packet = {
        "temperature": 18.0,
        "humidity": 35.0,
        "seq": 100,
        "state": 0 
    }
    print(f"📡 Setting initial state: {setup_packet['state']}")
    client.publish(TOPIC, json.dumps(setup_packet), qos=1)
    
    time.sleep(1) # Pausa para que el detector registre el prev_state

    # 2. ATAQUE: Salto forzado al Estado 8 (Hot/Humid)
    # Físicamente, la temperatura no sube de 18°C a 35°C instantáneamente.
    markov_attack = {
        "temperature": 35.0,
        "humidity": 80.0,
        "seq": 101,
        "state": 8 
    }
    
    print(f"🧠 Injecting impossible transition: {setup_packet['state']} -> {markov_attack['state']}")
    client.publish(TOPIC, json.dumps(markov_attack), qos=1)
    
    print("✅ Check RPI5 logs for '🚨 ALERT [Markov Impossible Jump]'.")
    print("📈 This should also trigger: export_process_graph()")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    client.disconnect()