import paho.mqtt.client as mqtt
import json
import numpy as np
from sklearn.ensemble import IsolationForest
import time
import pandas as pd
import pm4py
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter

# --- CONFIGURATION ---
BROKER = "localhost"
TOPIC = "device_1/telemetry"
FLOOD_THRESHOLD = 0.5
LOG_FILE = "iot_event_log.csv" # Archivo para Process Mining

# --- MARKOV MODEL SETUP (9 States) ---
transition_matrix = np.eye(9) * 0.8 + 0.025
transition_matrix[0][8] = 0.0 

# --- STATE TRACKING, AI & PROCESS MINING ---
data_history = []
event_records = [] # Lista para almacenar eventos para PM
model = IsolationForest(contamination=0.01)
trained = False
last_seq = -1
prev_state = -1
last_msg_time = time.time()

def export_process_graph():
    """Genera un mapa del proceso actual basado en los logs acumulados."""
    if len(event_records) < 10: return
    
    df = pd.DataFrame(event_records)
    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    
    # Creamos un Directly-Follows Graph (DFG) - Técnica clásica de Process Mining
    dfg, start_activities, end_activities = pm4py.discover_dfg(df, 
        case_id_key='case_id', activity_key='activity', timestamp_key='timestamp')
    
    # Guardamos la imagen para mostrarla en el video
    pm4py.save_vis_dfg(dfg, start_activities, end_activities, "process_map.png")
    print("📈 Process Mining: Updated process_map.png based on event logs.")

def on_message(client, userdata, msg):
    global prev_state, last_seq, last_msg_time, data_history, trained, model, event_records
    
    arrival_time = time.time()
    time_diff = arrival_time - last_msg_time
    
    try:
        payload = json.loads(msg.payload.decode())
        temp = payload.get("temperature", 0)
        hum = payload.get("humidity", 0)
        current_seq = payload.get("seq", -1)
        current_state = payload.get("state", -1)

        # Registro del evento para Process Mining
        # Un 'log' requiere: ID de caso, Actividad (Estado) y Timestamp
        event_records.append({
            "case_id": "device_1", 
            "activity": f"State_{current_state}", 
            "timestamp": pd.to_datetime(arrival_time, unit='s'),
            "temp": temp,
            "hum": hum
        })

        # A. DOS / FLOODING DETECTION
        if time_diff < FLOOD_THRESHOLD:
            print(f"🚨 ALERT [DoS/Flooding]: Interval: {time_diff:.4f}s")
        last_msg_time = arrival_time

        # B. SEQUENCE LOGIC (Replay Attack)
        if current_seq != -1:
            if current_seq == 0 and last_seq > 0:
                last_seq = 0
            elif current_seq <= last_seq and current_seq != 0:
                print(f"🚨 ALERT [Replay Attack]: Seq {current_seq} <= {last_seq}")
            else:
                last_seq = current_seq

        # C. MARKOV & PROCESS LOGIC
        if prev_state != -1 and current_state != -1:
            probability = transition_matrix[prev_state][current_state]
            if probability == 0:
                print(f"🚨 ALERT [Process Mining]: Illegal jump from {prev_state} to {current_state}!")
                export_process_graph() # Exportamos el mapa al detectar el fallo

        prev_state = current_state

        # D. AI DETECTION (Isolation Forest)
        current_reading = [temp, hum]
        data_history.append(current_reading)
        
        if len(data_history) > 50:
            X = np.array(data_history)
            if not trained or len(data_history) % 20 == 0:
                model.fit(X)
                trained = True
            
            score = model.decision_function([current_reading])
            if score[0] < -0.15:
                print(f"🚨 ALERT [Data Injection]: Unusual pattern! T={temp}, H={hum}")
            else:
                print(f"✅ Normal: T={temp}, H={hum} (Seq: {current_seq})")
        else:
            print(f"⚙️ Collecting baseline... ({len(data_history)}/50)")
                
    except Exception as e:
        print(f"❌ Error: {e}")

# --- MQTT EXECUTION ---
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(BROKER, 1883)
client.subscribe(TOPIC)
client.loop_forever()