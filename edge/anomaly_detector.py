import paho.mqtt.client as mqtt
import json
import numpy as np
from sklearn.ensemble import IsolationForest
import time
import pandas as pd
import pm4py
from pm4py.objects.log.util import dataframe_utils

# --- 1. CONFIGURATION ---
LOCAL_BROKER = "localhost"
LOCAL_TOPIC = "device_1/telemetry"

# ThingsBoard Configuration (UPM Server)
TB_BROKER = "srv-iot.diatel.upm.es"
TB_PORT = 8883
TB_TOKEN = "BKt667UYnxs92JTOACkg"
TB_TOPIC = "v1/devices/me/telemetry"

FLOOD_THRESHOLD = 0.5 
NORMAL_TEMP_RANGE = (15, 35)
NORMAL_HUM_RANGE = (30, 70)

# --- 2. MARKOV MODEL SETUP (9 States) ---
transition_matrix = np.eye(9) * 0.8 + 0.025
transition_matrix[0][8] = 0.0 

# --- 3. PROFESSIONAL AI INITIALIZATION ---
def generate_reference_model():
    print("⚙️ Generating professional reference model...")
    t_samples = np.random.uniform(NORMAL_TEMP_RANGE[0], NORMAL_TEMP_RANGE[1], 200)
    h_samples = np.random.uniform(NORMAL_HUM_RANGE[0], NORMAL_HUM_RANGE[1], 200)
    X_ref = np.column_stack((t_samples, h_samples))
    ref_model = IsolationForest(contamination=0.01)
    ref_model.fit(X_ref)
    return ref_model

model = generate_reference_model()
trained = True

# --- 4. STATE TRACKING & PROCESS MINING ---
event_records = []
last_seq = -1
prev_state = -1
last_msg_time = time.time()

# --- 5. THINGSBOARD CLIENT SETUP ---
tb_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
tb_client.username_pw_set(TB_TOKEN)

def connect_tb():
    try:
        # OPCIÓN A: Usar puerto 1883 (más fiable si no tienes certificados)
        # tb_client.connect(TB_BROKER, 1883, 60) 
        
        # OPCIÓN B: Puerto 8883 con TLS activado (requerido para ese puerto)
        tb_client.tls_set_context(mqtt.ssl.create_default_context()) 
        tb_client.connect(TB_BROKER, TB_PORT, 60)
        
        tb_client.loop_start()
        print(f"🌐 Connected to ThingsBoard at {TB_BROKER}")
    except Exception as e:
        print(f"❌ TB Connection Error: {e}")

connect_tb()

def export_process_graph():
    if len(event_records) < 5: return
    df = pd.DataFrame(event_records)
    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    dfg, start_activities, end_activities = pm4py.discover_dfg(df, 
        case_id_key='case_id', activity_key='activity', timestamp_key='timestamp')
    pm4py.save_vis_dfg(dfg, start_activities, end_activities, "process_map.png")
    print("📈 Process Mining: Updated process_map.png")

def on_message(client, userdata, msg):
    global prev_state, last_seq, last_msg_time, model, event_records
    
    arrival_time = time.time()
    time_diff = arrival_time - last_msg_time
    
    try:
        payload = json.loads(msg.payload.decode())
        temp = payload.get("temperature", 0)
        hum = payload.get("humidity", 0)
        current_seq = payload.get("seq", -1)
        current_state = payload.get("state", -1)

        # Alarm flags
        alarm_dos = False
        alarm_replay = False
        alarm_markov = False
        alarm_ai = False

        # Registro para Process Mining 
        event_records.append({
            "case_id": "device_1", 
            "activity": f"State_{current_state}", 
            "timestamp": pd.to_datetime(arrival_time, unit='s')
        })

        # A. DOS DETECTION
        if time_diff < FLOOD_THRESHOLD:
            print(f"🚨 ALERT [DoS/Flooding]")
            alarm_dos = True
        last_msg_time = arrival_time

        # B. REPLAY ATTACK DETECTION
        if current_seq != -1:
            if current_seq == 0 and last_seq > 0:
                last_seq = 0 
            elif current_seq <= last_seq and current_seq != 0:
                print(f"🚨 ALERT [Replay Attack]")
                alarm_replay = True
            else:
                last_seq = current_seq

        # C. MARKOV & PROCESS LOGIC 
        if prev_state != -1 and current_state != -1:
            if transition_matrix[prev_state][current_state] == 0:
                print(f"🚨 ALERT [Markov Impossible Jump]")
                alarm_markov = True
                export_process_graph()
        prev_state = current_state

        # D. IMMEDIATE AI DETECTION
        current_reading = np.array([[temp, hum]])
        score = model.decision_function(current_reading)
        if score[0] < -0.10:
            print(f"🚨 ALERT [Data Injection]")
            alarm_ai = True

        # --- SEND TO THINGSBOARD ---
        tb_payload = {
            "temperature": temp,
            "humidity": hum,
            "sequence": current_seq,
            "state": current_state,
            "alarm_dos": alarm_dos,
            "alarm_replay": alarm_replay,
            "alarm_markov": alarm_markov,
            "alarm_ai": alarm_ai,
            "system_status": "Anomalous" if (alarm_dos or alarm_replay or alarm_markov or alarm_ai) else "Normal"
        }
        tb_client.publish(TB_TOPIC, json.dumps(tb_payload), qos=1)
        
        if not alarm_dos and not alarm_replay and not alarm_markov and not alarm_ai:
            print(f"✅ Normal: T={temp}, H={hum} sent to ThingsBoard.")
                
    except Exception as e:
        print(f"❌ Error: {e}")

# --- 6. LOCAL EXECUTION ---
local_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
local_client.on_message = on_message
local_client.connect(LOCAL_BROKER, 1883)
local_client.subscribe(LOCAL_TOPIC)

print(f"🚀 Anomaly Detector + ThingsBoard Bridge active.")
local_client.loop_forever()