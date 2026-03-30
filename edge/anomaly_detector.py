"""
This module listens to local MQTT telemetry from IoT devices, analyzes the data stream
in real-time for cyber threats (Flooding, Replay, Data Injection, and Markov Tampering),
and forwards the processed security status to a cloud-based dashboard broker.

It utilizes an Isolation Forest model for AI-based anomaly detection and pm4py for
Process Mining to track logical state transitions.
"""

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
"""str: The hostname or IP of the local Mosquitto broker running on the Raspberry Pi 5."""

LOCAL_TOPIC = "device_1/telemetry"
"""str: The local MQTT topic where the ESP32 edge node publishes its sensor data."""

DASHBOARD_BROKER = "broker.emqx.io"
"""str: The public cloud MQTT broker used to forward processed data to the Streamlit UI."""

DASHBOARD_TOPIC = "ad_iot/group_c/device_1/dashboard"
"""str: The cloud MQTT topic the Streamlit dashboard subscribes to."""

MAX_SEQ_JUMP = 10
"""int: Maximum allowed gap between sequence numbers to prevent sequence spoofing."""

cloud_dashboard_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
cloud_dashboard_client.connect(DASHBOARD_BROKER, 1883)
cloud_dashboard_client.loop_start()

FLOOD_THRESHOLD = 0.5 
"""float: Minimum allowed time (in seconds) between incoming messages to avoid triggering a DoS alert."""

NORMAL_TEMP_RANGE = (15, 35)
"""tuple of int: The physical safe bounds for temperature in degrees Celsius."""

NORMAL_HUM_RANGE = (30, 70)
"""tuple of int: The physical safe bounds for relative humidity percentages."""

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
"""dict: Maps the calculated 0-8 integer state to a human-readable string for Process Mining logs."""

# --- 2. MARKOV MODEL SETUP (9 States) ---

transition_matrix = np.eye(9) * 0.8 + 0.025
"""numpy.ndarray: A 9x9 transition matrix representing the probability of moving from one physical state to another."""

# DEFINE IMPOSSIBLE JUMPS (Extreme to Extreme)

# Cannot jump directly from Cold (0,1,2) to Hot (6,7,8)
for c in [0, 1, 2]:
    for h in [6, 7, 8]:
        transition_matrix[c][h] = 0.0 # Cold to Hot
        transition_matrix[h][c] = 0.0 # Hot to Cold

# Cannot jump directly from Dry (0,3,6) to Humid (2,5,8)
for d in [0, 3, 6]:
    for hu in [2, 5, 8]:
        transition_matrix[d][hu] = 0.0 # Dry to Humid
        transition_matrix[hu][d] = 0.0 # Humid to Dry
        
# --- 3. AI INITIALIZATION (Isolation Forest) ---

def generate_reference_model():
    """
    Generates and trains the baseline AI anomaly detection model.

    Creates synthetic reference data representing normal operating conditions based on
    the predefined physical boundaries (NORMAL_TEMP_RANGE and NORMAL_HUM_RANGE).
    It then fits an Isolation Forest model to establish the anomaly decision boundaries.

    :return: A trained Machine Learning model for anomaly scoring.
    :rtype: sklearn.ensemble.IsolationForest
    """
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
"""list of dict: Stores a history of state transitions for PM4Py Process Mining."""

last_seq = -1
"""int: Tracks the last seen sequence number to detect Replay Attacks."""

prev_state = -1
"""int: Tracks the previously recorded physical state (0-8) to validate Markov transitions."""

last_msg_time = time.time()
"""float: Unix timestamp of the last received message to calculate transmission speed (Flooding)."""

last_rejected_seq = -1
"""int: Tracks the last blocked sequence to identify if the real device is trying to recover."""

desync_counter = 0
"""int: Counts consecutive logically incrementing sequences that were blocked."""

def export_process_graph():
    """
    Exports the current Process Mining data as a visual graph.

    Converts the stored ``event_records`` into a pandas DataFrame, processes it
    with the pm4py library, and saves a Directly-Follows Graph (DFG) as a PNG image 
    (``process_map.png``). Requires at least 10 logged events to trigger generation.

    :raises Exception: Catches and logs any errors during graph generation to prevent edge node crashes.
    """
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
    """
    MQTT callback function executed upon receiving a new telemetry message.
    Includes State Protection and Auto-Recovery to prevent permanent lockouts.
    """
    global prev_state, last_seq, last_msg_time, model, event_records
    global last_rejected_seq, desync_counter
    
    arrival_time = time.time()
    time_diff = arrival_time - last_msg_time
    
    try:
        payload = json.loads(msg.payload.decode())
        temp = payload.get("temperature", 0)
        hum = payload.get("humidity", 0)
        current_seq = payload.get("seq", -1)
        current_state = payload.get("state", -1)
        state_label = STATE_NAMES.get(current_state, f"State_{current_state}")

        alarms = {"flood": False, "replay": False, "markov": False, "di": False}
        
        # --- A. DOS DETECTION (FLOODING) ---
        if time_diff < FLOOD_THRESHOLD:
            print(f"🚨 ALERT [DoS/Flooding]")
            alarms["flood"] = True

        # --- C. MARKOV ANALYSIS ---
        if prev_state != -1 and current_state != -1:
            if transition_matrix[prev_state][current_state] == 0:
                print(f"🚨 ALERT [Markov Impossible Jump]")
                alarms["markov"] = True
                export_process_graph()

        # --- D. IMMEDIATE AI DETECTION ---
        current_reading = np.array([[temp, hum]])
        score = model.decision_function(current_reading)
        
        ai_anomaly = score[0] < 0.0 
        out_of_bounds = (temp < NORMAL_TEMP_RANGE[0] or temp > NORMAL_TEMP_RANGE[1] or 
                         hum < NORMAL_HUM_RANGE[0] or hum > NORMAL_HUM_RANGE[1])

        if ai_anomaly or out_of_bounds:
            print(f"🚨 ALERT [Data Injection/Out of Range] Score: {score[0]:.4f}")
            alarms["di"] = True

        # --- B. SEQUENCE & REPLAY ATTACK DETECTION (Moved to the end) ---
        if current_seq != -1:
            # SHIELD: Only allow sequence tracking if the payload passed all other physical/speed checks
            if alarms["flood"] or alarms["markov"] or alarms["di"]:
                pass # Prevent attacker from hijacking sequence memory
            else:
                # 1. Track if the ESP32 is consistently trying to send valid, incrementing sequences
                if current_seq == last_rejected_seq + 1 and last_rejected_seq != -1:
                    desync_counter += 1
                else:
                    desync_counter = 0

                # 2. Self-Healing: 3 valid sequences in a row means our baseline is poisoned. Resync.
                if desync_counter >= 3:
                    print("🔄 [Auto-Recovery] Baseline corrupted. Resynchronizing sequence tracker!")
                    last_seq = current_seq - 1
                    desync_counter = 0

                # 3. Standard Replay & Spoofing Checks
                if current_seq <= last_seq and current_seq != 0:
                    print(f"🚨 ALERT [Replay Attack] Seq: {current_seq} (Last: {last_seq})")
                    alarms["replay"] = True
                    last_rejected_seq = current_seq
                    
                elif last_seq != -1 and current_seq > (last_seq + MAX_SEQ_JUMP):
                    print(f"🚨 ALERT [Sequence Spoofing] Unreal jump from {last_seq} to {current_seq}")
                    alarms["replay"] = True
                    last_rejected_seq = current_seq
                    
                else:
                    # Sequence is normal, clear the tracking memory
                    last_rejected_seq = -1

        is_anomalous = any(alarms.values())

        # --- STATE & MEMORY PROTECTION ---
        if not is_anomalous:
            last_seq = current_seq
            prev_state = current_state
            
            event_records.append({
                "case_id": "device_1", 
                "activity": state_label, 
                "timestamp": pd.to_datetime(arrival_time, unit='s')
            })
            print(f"✅ Normal: T={temp}, H={hum}, Seq={current_seq} sent to dashboard.")
        else:
            print(f"🛡️ State Protected: Dropping malicious payload from memory.")

        last_msg_time = arrival_time

        # --- SEND TO CLOUD DASHBOARD ---
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
                
    except Exception as e:
        print(f"❌ Error processing message: {e}")

# --- 6. LOCAL SUBSCRIBER ---
if __name__ == "__main__":
    local_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    local_client.on_message = on_message
    local_client.connect(LOCAL_BROKER, 1883)
    local_client.subscribe(LOCAL_TOPIC)

    print("🎧 Listening for local device telemetry...")
    local_client.loop_forever()