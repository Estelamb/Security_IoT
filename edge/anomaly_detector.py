import paho.mqtt.client as mqtt
import json
import numpy as np
from sklearn.ensemble import IsolationForest
import time

# --- CONFIGURATION ---
BROKER = "localhost"
TOPIC = "device_1/telemetry"

# Security and AI tracking
data_history = []
model = IsolationForest(contamination=0.1)
trained = False
last_seq = -1
last_msg_time = 0

# Thresholds
FLOOD_THRESHOLD = 0.5 

def on_message(client, userdata, msg):
    global data_history, trained, model, last_seq, last_msg_time
    
    current_time = time.time()
    time_diff = current_time - last_msg_time
    last_msg_time = current_time

    try:
        payload = json.loads(msg.payload.decode())
        temp = payload["temperature"]
        hum = payload["humidity"]
        current_seq = payload.get("seq", -1)

        # --- REBOOT & SEQUENCE LOGIC ---
        if current_seq != -1:
            # If we receive 0, the device likely restarted. We reset last_seq.
            if current_seq == 0 and last_seq > 0:
                print("ℹ️ Device reboot detected. Resetting sequence tracking.")
                last_seq = 0
            
            # Replay Attack check: only alert if it's not a reboot (current_seq > 0)
            elif current_seq <= last_seq and current_seq != 0:
                print(f"🚨 ALERT [Replay Attack]: Outdated sequence! Received {current_seq}, Expected > {last_seq}")
            else:
                last_seq = current_seq
                print(f"✅ Seq: {current_seq}")

        # --- DOS / FLOODING DETECTION ---
        if time_diff < FLOOD_THRESHOLD and last_msg_time != 0:
            print(f"🚨 ALERT [DoS/Flooding]: High frequency detected! Interval: {time_diff:.2f}s")

        # --- AI-BASED DETECTION ---
        current_reading = [temp, hum]
        data_history.append(current_reading)
        
        if len(data_history) > 20:  
            X = np.array(data_history)
            if not trained or len(data_history) % 10 == 0:
                model.fit(X)
                trained = True
            
            prediction = model.predict([current_reading])
            if prediction[0] == -1:
                print(f"🚨 ALERT [Data Injection]: Unusual pattern! T={temp}°C, H={hum}%")
            else:
                print(f"✅ Normal: T={temp}°C, H={hum}% (Seq: {current_seq})")
                
    except Exception as e:
        print(f"Error processing message: {e}")

# --- MQTT SETUP ---
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, 1883)
client.subscribe(TOPIC)

print(f"Monitoring topic '{TOPIC}'...")
client.loop_forever()