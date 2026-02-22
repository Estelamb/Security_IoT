import paho.mqtt.client as mqtt
import json
import numpy as np
from sklearn.ensemble import IsolationForest
import time

# --- CONFIGURATION ---
BROKER = "localhost"
TOPIC = "device_1/telemetry"

# Security tracking
data_history = []
model = IsolationForest(contamination=0.01) # Reducido al 1% para evitar falsos positivos
trained = False
last_seq = -1
last_msg_time = time.time() # Inicializar con el tiempo actual

# Thresholds
FLOOD_THRESHOLD = 0.5 

def on_message(client, userdata, msg):
    global data_history, trained, model, last_seq, last_msg_time
    
    # Capturar el tiempo inmediatamente al recibir el mensaje
    arrival_time = time.time()
    time_diff = arrival_time - last_msg_time
    
    try:
        payload = json.loads(msg.payload.decode())
        temp = payload["temperature"]
        hum = payload["humidity"]
        current_seq = payload.get("seq", -1)

        # 1. DOS / FLOODING DETECTION (Prioridad alta)
        if time_diff < FLOOD_THRESHOLD:
            print(f"🚨 ALERT [DoS/Flooding]: Interval: {time_diff:.4f}s")
        
        # Actualizar el tiempo para la siguiente comparación
        last_msg_time = arrival_time

        # 2. SEQUENCE LOGIC (Replay Attack)
        if current_seq != -1:
            if current_seq == 0 and last_seq > 0:
                print("ℹ️ Device reboot detected.")
                last_seq = 0
            elif current_seq <= last_seq and current_seq != 0:
                print(f"🚨 ALERT [Replay Attack]: Seq {current_seq} <= {last_seq}")
            else:
                last_seq = current_seq

        # 3. AI DETECTION (Isolation Forest)
        current_reading = [temp, hum]
        data_history.append(current_reading)
        
        # Aumentamos a 50 lecturas para tener una base estadística real
        if len(data_history) > 50:  
            X = np.array(data_history)
            if not trained or len(data_history) % 20 == 0:
                model.fit(X)
                trained = True
            
            # Solo evaluar si el modelo está bien entrenado
            score = model.decision_function([current_reading])
            if score[0] < -0.15: # Usamos un umbral de confianza manual además del modelo
                print(f"🚨 ALERT [Data Injection]: Unusual pattern! T={temp}, H={hum}")
            else:
                print(f"✅ Normal: T={temp}, H={hum} (Seq: {current_seq})")
        else:
            print(f"⚙️ Collecting baseline data... ({len(data_history)}/50)")
                
    except Exception as e:
        print(f"Error: {e}")

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, 1883)
client.subscribe(TOPIC)
client.loop_forever()