"""
This Streamlit application acts as the Security Operations Center (SOC) monitor.
It subscribes to a public cloud MQTT broker (EMQX) to receive real-time telemetry and
anomaly alerts from the edge node, displaying them in an interactive web interface.
"""

import streamlit as st
import paho.mqtt.client as mqtt
import json
import threading
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import queue
import pytz

# --- PAGE CONFIG ---
st.set_page_config(page_title="IoT Security SOC", page_icon="🛡️", layout="wide")

# Refresh the page every 1 second
st_autorefresh(interval=1000, key="data_refresh")

# Local Timezone Setup (Crucial for Streamlit Cloud deployment)
LOCAL_TZ = pytz.timezone("Europe/Madrid")

# --- THREAD-SAFE COMMUNICATION ---
@st.cache_resource
def get_message_queue():
    """
    Creates a thread-safe queue to pass messages from the background MQTT thread
    to the main Streamlit UI thread.
    
    :return: A synchronized queue instance.
    :rtype: queue.Queue
    """
    return queue.Queue()

msg_queue = get_message_queue()

# --- INITIALIZE SESSION STATE ---
if 'current_data' not in st.session_state:
    st.session_state.current_data = {
        "temperature": 0.0, "humidity": 0.0, "sequence": 0, "state": 0,
        "alarm_flood": False, "alarm_replay": False, "alarm_markov": False, "alarm_di": False,
        "system_status": "Waiting for data..."
    }

if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Temperature', 'Humidity'])

if 'alarms_log' not in st.session_state:
    st.session_state.alarms_log = []

# --- BACKGROUND MQTT CLIENT ---
def on_message(client, userdata, msg):
    """
    MQTT callback function triggered when a new message arrives from the cloud broker.
    
    It decodes the JSON payload and safely places it into the processing queue 
    so the Streamlit main thread can update the UI without race conditions.

    :param client: The MQTT client instance for this callback.
    :type client: paho.mqtt.client.Client
    :param userdata: The private user data as set in Client() or user_data_set().
    :type userdata: Any
    :param msg: An instance of MQTTMessage containing the topic, qos, and payload.
    :type msg: paho.mqtt.client.MQTTMessage
    """
    try:
        payload = json.loads(msg.payload.decode())
        get_message_queue().put(payload)
    except Exception as e:
        print(f"Error decoding message: {e}")

@st.cache_resource
def start_mqtt_subscriber():
    """
    Initializes and starts a background daemon thread that continuously listens
    to the public EMQX MQTT broker for incoming telemetry and alert data.
    
    :return: The configured MQTT client instance.
    :rtype: paho.mqtt.client.Client
    """
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    
    # Connect to the public cloud broker
    client.connect("broker.emqx.io", 1883)
    client.subscribe("ad_iot/group_c/device_1/dashboard") 
    
    thread = threading.Thread(target=client.loop_forever, daemon=True)
    thread.start()
    return client

start_mqtt_subscriber()

# --- PROCESS QUEUE (Main Streamlit Thread) ---
# Pull all new messages from the queue and update the UI memory safely
while not msg_queue.empty():
    payload = msg_queue.get()
    
    # 1. Update current metrics
    st.session_state.current_data = payload
    
    # 2. Append to historical chart data (Using local timezone)
    new_row = pd.DataFrame([{
        'Time': datetime.now(LOCAL_TZ), 
        'Temperature': payload.get('temperature', 0), 
        'Humidity': payload.get('humidity', 0)
    }])

    if st.session_state.history.empty:
        st.session_state.history = new_row
    else:
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
        
    if len(st.session_state.history) > 60:
        st.session_state.history = st.session_state.history.tail(60)

    # 3. Process Alarms for the Table
    alarms_map = {
        "alarm_flood": "Flooding (DoS)",
        "alarm_replay": "Replay Attack",
        "alarm_markov": "Markov Tampering",
        "alarm_di": "Data Injection"
    }
    
    for key, alarm_name in alarms_map.items():
        if payload.get(key):
            st.session_state.alarms_log.insert(0, {
                "Timestamp": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S"),
                "Type": alarm_name,
                "Severity": "MAJOR",
                "Originator": "device_1",
                "Status": "ACTIVE"
            })
    
    st.session_state.alarms_log = st.session_state.alarms_log[:50]

def main():
    '''
    Main function to render the Streamlit dashboard UI. It displays real-time telemetry,
    system status, historical charts, and an alarms log based on the data received from the MQTT subscriber.
    '''
    # --- UI LAYOUT ---
    st.title("🛡️ IoT Security: Anomaly Detection Monitor")
    data = st.session_state.current_data

    # 1. System Status Banner
    if data["system_status"] == "Anomalous":
        st.error(f"⚠️ SYSTEM STATUS: {data['system_status'].upper()} ⚠️")
    elif data["system_status"] == "Normal":
        st.success(f"✅ SYSTEM STATUS: {data['system_status'].upper()}")
    else:
        st.warning(f"⏳ {data['system_status']}")

    st.divider()

    left_col, right_col = st.columns([2, 1])

    with left_col:
        # 2. Quick Alarm Indicators
        st.subheader("🎯 Threat Status")

        active_threats = False

        if data.get("alarm_flood"):
            st.error("🚨 Flooding (DoS)")
            active_threats = True
        if data.get("alarm_replay"):
            st.error("🚨 Replay Attack")
            active_threats = True
        if data.get("alarm_markov"):
            st.error("🚨 Markov Tampering")
            active_threats = True
        if data.get("alarm_di"):
            st.error("🚨 Data Injection")
            active_threats = True

        # Show a single clean message if nothing is happening
        if not active_threats:
            st.success("✅ Secure (No active alarms)")

        # 3. Historical Data Chart
        st.subheader("📈 Historical Data")
        if not st.session_state.history.empty:
            chart_data = st.session_state.history.set_index('Time')
            st.line_chart(chart_data[['Temperature', 'Humidity']], color=["#F32121", "#55C3FF"])
        else:
            st.info("Waiting for telemetry data to build charts...")

        # 4. Alarms Table
        st.subheader("🚨 Alarms Log")
        if st.session_state.alarms_log:
            alarms_df = pd.DataFrame(st.session_state.alarms_log)
            st.dataframe(alarms_df, use_container_width=True, hide_index=True)
            if st.button("Clear Alarms Log"):
                st.session_state.alarms_log = []
        else:
            st.success("No alarms detected in the current session.")

    with right_col:
        # 5. Horizontal Value Cards
        st.subheader("📡 Live Telemetry")

        with st.container(border=True):
            st.metric(label="Temperature", value=f"{data['temperature']:.2f} °C")
        with st.container(border=True):
            st.metric(label="Humidity", value=f"{data['humidity']:.2f} %")
        with st.container(border=True):
            st.metric(label="Sequence Number", value=data['sequence'])

        # English labels with full words
        state_labels = [
            "Cold/Dry", "Cold/Normal", "Cold/Humid", 
            "Normal/Dry", "Normal/Normal", "Normal/Humid", 
            "Hot/Dry", "Hot/Normal", "Hot/Humid"
        ]

        # Format: temp_str Temperature / hum_str Humidity / state State
        if 0 <= data['state'] <= 8:
            temp_str, hum_str = state_labels[data['state']].split("/")
            formatted_state = f"**{temp_str} Temperature**\n\n**{hum_str} Humidity**\n\n**State {data['state']}**"
        else:
            formatted_state = f"**Unknown state {data['state']}**"

        # Using Markdown inside a container to mimic the metric card look
        with st.container(border=True):
            st.caption("Markov State") 
            st.markdown(formatted_state)

if __name__ == "__main__":
    main()