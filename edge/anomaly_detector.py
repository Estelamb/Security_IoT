import paho.mqtt.client as mqtt
import json
import numpy as np
from sklearn.ensemble import IsolationForest
import time
import pandas as pd
import pm4py
from pm4py.objects.log.util import dataframe_utils
import ssl

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
# 1. Inicialización base (probabilidad pequeña para el resto)
transition_matrix = np.eye(9) * 0.8 + 0.025

# 2. DEFINIR SALTOS IMPOSIBLES (Extremo a Extremo)

# --- Saltos de Temperatura (Cold <-> Hot) ---
# No se puede pasar de Cold (0,1,2) a Hot (6,7,8) directamente
for c in [0, 1, 2]:
    for h in [6, 7, 8]:
        transition_matrix[c][h] = 0.0 # Cold a Hot
        transition_matrix[h][c] = 0.0 # Hot a Cold

# --- Saltos de Humedad (Dry <-> Humid) ---
# No se puede pasar de Dry (0,3,6) a Humid (2,5,8) directamente
for d in [0, 3, 6]:
    for hu in [2, 5, 8]:
        transition_matrix[d][hu] = 0.0 # Dry a Humid
        transition_matrix[hu][d] = 0.0 # Humid a Dry
        
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

# --- 5. THINGSBOARD CLIENT SETUP ---
tb_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
tb_client.username_pw_set(TB_TOKEN)

def on_tb_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"🌐 Connected to ThingsBoard at {TB_BROKER}")
    else:
        print(f"❌ TB Connection Failed with code {rc}")

tb_client.on_connect = on_tb_connect

# Configuración TLS robusta para el puerto 8883
try:
    context = ssl.create_default_context()
    # Si el servidor de la UPM usa un certificado autofirmado, podríais necesitar:
    # context.check_hostname = False
    # context.verify_mode = ssl.CERT_NONE
    tb_client.tls_set_context(context)
    tb_client.connect(TB_BROKER, TB_PORT, 60)
    tb_client.loop_start()
except Exception as e:
    print(f"⚠️ TLS/Connection Error: {e}. Check if port 8883 is open.")

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

# --- 6. CORE LOGIC (Anomaly Detection) ---
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

        # Alarm flags iniciales
        alarms = {"flood": False, "replay": False, "markov": False, "di": False}

        # Registro para Process Mining
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
        # Solo comprobamos Replay si NO hay Flooding activo para evitar falsos positivos por desorden
        if not alarms["flood"] and current_seq != -1:
            if current_seq == 0:
                last_seq = 0
            elif current_seq <= last_seq:
                print(f"🚨 ALERT [Replay Attack] Seq: {current_seq} (Last: {last_seq})")
                alarms["replay"] = True
            else:
                last_seq = current_seq
        elif alarms["flood"]:
            # Durante un flood, simplemente actualizamos el máximo visto para no quedarnos bloqueados
            last_seq = max(last_seq, current_seq)

        # C. MARKOV ANALYSIS
        if prev_state != -1 and current_state != -1:
            if transition_matrix[prev_state][current_state] == 0:
                print(f"🚨 ALERT [Markov Impossible Jump]")
                alarms["markov"] = True
                export_process_graph()
        prev_state = current_state

        # D. IMMEDIATE AI DETECTION (Ajustado)
        current_reading = np.array([[temp, hum]])
        score = model.decision_function(current_reading)
        
        # Umbral más sensible: si el score es menor que 0.0, es una anomalía
        ai_anomaly = score[0] < 0.0 

        # REGLA DE ORO: Si está fuera de los rangos físicos, es Anomaly Detection sí o sí
        # Esto apoya vuestro objetivo de detectar fallos técnicos 
        out_of_bounds = (temp < NORMAL_TEMP_RANGE[0] or temp > NORMAL_TEMP_RANGE[1] or 
                         hum < NORMAL_HUM_RANGE[0] or hum > NORMAL_HUM_RANGE[1])

        if ai_anomaly or out_of_bounds:
            print(f"🚨 ALERT [Data Injection/Out of Range] Score: {score[0]:.4f}")
            alarms["di"] = True

        # --- ENVÍO A THINGSBOARD ---
        is_anomalous = any(alarms.values())
        tb_payload = {
            "temperature": temp,
            "humidity": hum,
            "sequence": current_seq,
            "state": current_state,
            "alarm_flood": alarms["flood"],
            "alarm_replay": alarms["replay"],
            "alarm_markov": alarms["markov"],
            "alarm_di": alarms["di"],
            "status": "Anomalous" if is_anomalous else "Normal"
        }
        tb_client.publish(TB_TOPIC, json.dumps(tb_payload), qos=1)
        
        if not is_anomalous:
            print(f"✅ Normal: T={temp}, H={hum} sent to ThingsBoard.")
                
    except Exception as e:
        print(f"❌ Error processing message: {e}")

# --- 7. LOCAL SUBSCRIBER ---
local_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
local_client.on_message = on_message
local_client.connect(LOCAL_BROKER, 1883)
local_client.subscribe(LOCAL_TOPIC)

print(f"🚀 Anomaly Detector + ThingsBoard Bridge active.")
local_client.loop_forever()