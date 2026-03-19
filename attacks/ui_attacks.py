import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="IoT Attack Control Center", page_icon="👾", layout="wide")

DEFAULT_BROKER = "localhost"
DEFAULT_TOPIC = "device_1/telemetry"

# --- HELPER FUNCTIONS ---
def publish_message(broker, topic, payload, qos=1):
    """Handles the MQTT connection and publishing."""
    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.connect(broker, 1883)
        client.publish(topic, json.dumps(payload), qos=qos)
        client.disconnect()
        return True
    except Exception as e:
        st.error(f"MQTT Connection Error: {e}")
        return False

# --- UI LAYOUT ---
st.title("👾 IoT Security: Attack Control Center")
st.markdown("Group C - Anomalies Detection Testbed")

# Sidebar for MQTT Config
with st.sidebar:
    st.header("⚙️ Broker Settings")
    broker_ip = st.text_input("Broker IP", DEFAULT_BROKER)
    mqtt_topic = st.text_input("Topic", DEFAULT_TOPIC)
    st.info("Ensure the edge node (RPi5) is running the anomaly detector and listening to this broker.")

# Main content: Attack selection
st.subheader("Select Attack Vector")
attack_tab = st.tabs(["💉 Data Injection", "🌊 Flooding (DoS)", "🧠 Markov Process", "♻️ Replay Attack"])

# 1. DATA INJECTION ATTACK
with attack_tab[0]:
    st.markdown("Inject extreme or impossible physical values to trigger AI Anomaly bounds.")
    col1, col2, col3 = st.columns(3)
    with col1:
        di_temp = st.number_input("Spoofed Temperature (°C)", value=150.0, step=1.0)
    with col2:
        di_hum = st.number_input("Spoofed Humidity (%)", value=5.0, step=1.0)
    with col3:
        di_state = st.number_input("Spoofed State (0-8)", value=8, step=1, min_value=0, max_value=8)
    
    if st.button("🚀 Launch Data Injection", use_container_width=True):
        payload = {"temperature": di_temp, "humidity": di_hum, "seq": 0, "state": di_state}
        if publish_message(broker_ip, mqtt_topic, payload):
            st.success(f"Sent malicious payload: {payload}")

# 2. FLOODING ATTACK
with attack_tab[1]:
    st.markdown("Send a massive burst of seemingly normal traffic to overwhelm the threshold.")
    col1, col2 = st.columns(2)
    with col1:
        flood_count = st.number_input("Number of Messages", value=100, step=10)
    with col2:
        flood_delay = st.number_input("Delay Between Messages (s)", value=0.1, step=0.05)
    
    if st.button("🌊 Launch Flooding Attack", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        try:
            client.connect(broker_ip, 1883)
            for i in range(flood_count):
                payload = {"temperature": 25.0, "humidity": 50.0, "seq": i, "state": 4}
                client.publish(mqtt_topic, json.dumps(payload), qos=0)
                time.sleep(flood_delay)
                
                # Update UI
                progress = int(((i + 1) / flood_count) * 100)
                progress_bar.progress(progress)
                status_text.text(f"Sent {i + 1}/{flood_count} messages...")
                
            client.disconnect()
            st.success("✅ Flood complete. Check ThingsBoard/RPi logs for DoS alerts.")
        except Exception as e:
            st.error(f"Error during flood: {e}")

# 3. MARKOV PROCESS TAMPERING
with attack_tab[2]:
    st.markdown("Force an impossible state transition (e.g., instant jump from Cold/Dry to Hot/Humid).")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Initial State Setup")
        markov_init_temp = st.number_input("Initial Temp", value=18.0)
        markov_init_hum = st.number_input("Initial Humidity", value=35.0)
        markov_init_state = st.number_input("Initial State", value=0, max_value=8)
    with col2:
        st.write("Impossible Jump Target")
        markov_tgt_temp = st.number_input("Target Temp", value=35.0)
        markov_tgt_hum = st.number_input("Target Humidity", value=80.0)
        markov_tgt_state = st.number_input("Target State", value=8, max_value=8)

    if st.button("🧠 Execute Impossible Jump", use_container_width=True):
        init_payload = {"temperature": markov_init_temp, "humidity": markov_init_hum, "seq": 100, "state": markov_init_state}
        tgt_payload = {"temperature": markov_tgt_temp, "humidity": markov_tgt_hum, "seq": 101, "state": markov_tgt_state}
        
        publish_message(broker_ip, mqtt_topic, init_payload)
        st.info(f"Set initial state: {markov_init_state}. Waiting 1 second...")
        time.sleep(1)
        
        if publish_message(broker_ip, mqtt_topic, tgt_payload):
            st.success(f"Injected impossible transition: State {markov_init_state} -> {markov_tgt_state}")

# 4. REPLAY ATTACK
with attack_tab[3]:
    st.markdown("Send an older sequence number to trigger replay detection.")
    col1, col2 = st.columns(2)
    with col1:
        current_seq = st.number_input("Current Valid Sequence", value=50, step=1)
    with col2:
        replay_seq = st.number_input("Captured Old Sequence", value=10, step=1)
        
    if st.button("♻️ Inject Replay", use_container_width=True):
        valid_payload = {"temperature": 24.5, "humidity": 50.0, "seq": current_seq, "state": 4}
        replay_payload = {"temperature": 24.5, "humidity": 50.0, "seq": replay_seq, "state": 4}
        
        publish_message(broker_ip, mqtt_topic, valid_payload)
        st.info(f"Sent valid packet (seq: {current_seq}). Waiting 1 second...")
        time.sleep(1)
        
        if publish_message(broker_ip, mqtt_topic, replay_payload):
            st.success(f"Injected Replay Attack (seq: {replay_seq})")