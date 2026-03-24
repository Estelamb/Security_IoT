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

# EMQX Broker Configuration (Cloud Dashboard)
DASHBOARD_BROKER = "broker.emqx.io"
DASHBOARD_TOPIC = "ad_iot/group_c/device_1/dashboard"

cloud_dashboard_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
cloud_dashboard_client.connect(DASHBOARD_BROKER, 1883)
cloud_dashboard_client.loop_start()

FLOOD_THRESHOLD = 0.5 
NORMAL_TEMP_RANGE = (15, 35)
NORMAL_HUM_RANGE = (30, 70)

STATE_NAMES = {
    0: "Cold_Dry",
    1: "Cold_Normal",
    2: "Cold_Humid",
    3: "Normal_Dry",
    4: "Normal_Normal",
    5: "Normal_Humid",
    6: "Hot_Dry",
    7: "Hot_Normal",
    8: "Hot_Humid"
}

# --- 2. MARKOV MODEL SETUP (9 States) ---
# 1. Base initialization (small probability for the rest)
transition_matrix = np.eye(9) * 0.8 + 0.025

# 2. DEFINE IMPOSSIBLE JUMPS (Extreme to Extreme)

# --- Temperature Jumps (Cold <-> Hot) ---
# Cannot jump directly from Cold (0,1,2) to Hot (6,7,8)
for c in [0, 1, 2]:
    for h in [6, 7, 8]:
        transition_matrix[c][h] = 0.0 # Cold to Hot
        transition_matrix[h][c] = 0.0 # Hot to Cold

# --- Humidity Jumps (Dry <-> Humid) ---
# Cannot jump directly from Dry (0,3,6) to Humid (2,5,8)
for d in [0, 3, 6]:
    for hu in [2, 5, 8]:
        transition_matrix[d][hu] = 0.0 # Dry to Humid
        transition_matrix[hu][d] = 0.0 # Humid to Dry
        
# --- 3. AI INITIALIZATION (Isolation Forest) ---
def generate_reference_model():
    print("⚙️ Generating professional reference model...")
    t_samples = np.random.uniform(NORMAL_TEMP_RANGE[0], NORMAL_TEMP_RANGE[1], 200)
    h_samples = np.random.uniform(NORMAL_HUM_RANGE[0], NORMAL_HUM_RANGE[1], 200)
    X_ref = np.column_stack((t_samples, h_samples))
    ref_model = IsolationForest(contamination=0.01)
    ref_model.fit(X_ref)
    return ref_model

model = generate_reference_model()

# --- 4. STATE TRACKING & PROCESS MINING ---
event_records = []
last_seq = -1
prev_state = -1
last_msg_time = time.time()

def export_process_graph():
    if len(event_records) < 10: return
    try:
        df = pd.DataFrame(event_records)
        df = dataframe_utils.convert_timestamp_columns_in_df(df)
        dfg, start_activities, end_activities = pm4py.discover_dfg(df, 
            case_id_key='case_id', activity_key='activity', timestamp_key='timestamp')
        pm4py.save_vis_dfg(dfg, start_activities, end_activities, "process_map.png")
        print("📈 Process Mining: Updated process_map.png")
    except Exception as e:
        print(f"❌ Process Mining Error: {e}")

# --- 5. CORE LOGIC (Anomaly Detection) ---
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
        state_label = STATE_NAMES.get(current_state, f"State_{current_state}")

        # Initial Alarm flags
        alarms = {"flood": False, "replay": False, "markov": False, "di": False}

        # Process Mining Logging
        event_records.append({
            "case_id": "device_1", 
            "activity": state_label, 
            "timestamp": pd.to_datetime(arrival_time, unit='s')
        })
        # --- A. DOS DETECTION (FLOODING) ---
        if time_diff < FLOOD_THRESHOLD:
            print(f"🚨 ALERT [DoS/Flooding]")
            alarms["flood"] = True
        last_msg_time = arrival_time

        # --- B. REPLAY ATTACK DETECTION ---
        # Check Replay only if there's NO flooding to avoid false positives
        if not alarms["flood"] and current_seq != -1:
            if current_seq == 0:
                last_seq = 0
            elif current_seq <= last_seq:
                print(f"🚨 ALERT [Replay Attack] Seq: {current_seq} (Last: {last_seq})")
                alarms["replay"] = True
            else:
                last_seq = current_seq
        elif alarms["flood"]:
            # Update max seen during flood to avoid blocking
            last_seq = max(last_seq, current_seq)

        # C. MARKOV ANALYSIS
        if prev_state != -1 and current_state != -1:
            if transition_matrix[prev_state][current_state] == 0:
                print(f"🚨 ALERT [Markov Impossible Jump]")
                alarms["markov"] = True
                export_process_graph()
        prev_state = current_state

        # D. IMMEDIATE AI DETECTION
        current_reading = np.array([[temp, hum]])
        score = model.decision_function(current_reading)
        
        # Anomaly threshold: < 0.0
        ai_anomaly = score[0] < 0.0 

        # Golden Rule: Out of physical bounds is an anomaly
        out_of_bounds = (temp < NORMAL_TEMP_RANGE[0] or temp > NORMAL_TEMP_RANGE[1] or 
                         hum < NORMAL_HUM_RANGE[0] or hum > NORMAL_HUM_RANGE[1])

        if ai_anomaly or out_of_bounds:
            print(f"🚨 ALERT [Data Injection/Out of Range] Score: {score[0]:.4f}")
            alarms["di"] = True

        # --- SEND TO CLOUD DASHBOARD ---
        is_anomalous = any(alarms.values())
        db_payload = {
            "temperature": temp,
            "humidity": hum,
            "sequence": current_seq,
            "state": current_state,
            "alarm_flood": alarms["flood"],
            "alarm_replay": alarms["replay"],
            "alarm_markov": alarms["markov"],
            "alarm_di": alarms["di"],
            "system_status": "Anomalous" if is_anomalous else "Normal"
        }
        
        cloud_dashboard_client.publish(DASHBOARD_TOPIC, json.dumps(db_payload), qos=0)
        
        if not is_anomalous:
            print(f"✅ Normal: T={temp}, H={hum} sent to the dashboard")
                
    except Exception as e:
        print(f"❌ Error processing message: {e}")

# --- 6. LOCAL SUBSCRIBER ---
local_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
local_client.on_message = on_message
local_client.connect(LOCAL_BROKER, 1883)
local_client.subscribe(LOCAL_TOPIC)

print("🎧 Listening for local device telemetry...")
local_client.loop_forever()