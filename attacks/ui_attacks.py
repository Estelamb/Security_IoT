"""
This Streamlit application provides an interactive user interface to simulate various
cyberattacks against an IoT edge node running an anomaly detection system.

The supported attack vectors include:
1. **Data Injection:** Sending spoofed/impossible physical values.
2. **Flooding (DoS):** Overwhelming the broker with high-frequency messages.
3. **Markov Process Tampering:** Injecting logically impossible state transitions.
4. **Replay Attacks:** Re-transmitting old, captured telemetry sequences.
"""

import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="IoT Attack Control Center", page_icon="👾", layout="wide")

DEFAULT_BROKER = "localhost"
"""str: The default local IP address of the MQTT broker where the simulated attacks will be sent."""

DEFAULT_TOPIC = "device_1/telemetry"
"""str: The default MQTT topic that the target edge node is listening to for telemetry data."""

# --- HELPER FUNCTIONS ---
def publish_message(broker, topic, payload, qos=1):
    """
    Handles the MQTT connection and publishing of a single malicious payload.

    This function instantiates a temporary MQTT client, connects to the target broker,
    publishes the JSON-encoded payload, and immediately disconnects to simulate a
    stateless injection.

    :param broker: The IP address or hostname of the target MQTT broker.
    :type broker: str
    :param topic: The MQTT topic to publish the malicious message to.
    :type topic: str
    :param payload: The data dictionary to send (will be serialized to JSON).
    :type payload: dict
    :param qos: Quality of Service level for the MQTT message (default is 1 to guarantee delivery).
    :type qos: int
    :return: True if the message was successfully published, False if a connection error occurred.
    :rtype: bool
    """
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
    st.markdown("### Data Injection (AI Evasion)")
    
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
    
    st.info(
        "**How it works:** The attacker sends physically impossible or maliciously crafted data to trick the AI model "
        "(Isolation Forest) or trigger out-of-bounds physical rules.\n\n"
        "**Real-world Example:** A hacker injects a fake temperature reading of 150°C into an industrial control system. "
        "This triggers an automatic emergency shutdown of the machinery, causing a massive denial of service and financial loss.\n\n"
        "⚠️ **Side Effects:** Depending on the last registered physical state of the sensor before you launch this attack, "
        "the extreme jump to State 8 will likely also trigger a **Markov Tampering** alert."
    )

# 2. FLOODING ATTACK
with attack_tab[1]:
    st.markdown("### Flooding (Denial of Service)")
    
    col1, col2 = st.columns(2)
    with col1:
        flood_count = st.number_input("Number of Messages", value=100, step=10)
    with col2:
        flood_delay = st.number_input("Delay Between Messages (s)", value=0.1, step=0.05)
    
    if st.button("🌊 Launch Flooding Attack", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # We handle flooding connection manually to avoid connecting/disconnecting 100 times
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        try:
            client.connect(broker_ip, 1883)
            for i in range(flood_count):
                payload = {"temperature": 25.0, "humidity": 50.0, "seq": i, "state": 4}
                client.publish(mqtt_topic, json.dumps(payload), qos=0)
                time.sleep(flood_delay)
                
                # Update UI Progress
                progress = int(((i + 1) / flood_count) * 100)
                progress_bar.progress(progress)
                status_text.text(f"Sent {i + 1}/{flood_count} messages...")
                
            client.disconnect()
            st.success("✅ Flood complete. Check Cloud Dashboard/RPi logs for DoS alerts.")
        except Exception as e:
            st.error(f"Error during flood: {e}")

    st.info(
        "**How it works:** The attacker overwhelms the MQTT broker or the edge node (RPi5) by sending a massive burst "
        "of messages in a fraction of a second, violating the expected transmission rate (FLOOD_THRESHOLD).\n\n"
        "**Real-world Example:** A botnet of compromised IoT cameras targets a central server, sending thousands of "
        "MQTT packets per second. The server's CPU maxes out trying to process them, preventing legitimate sensor data "
        "from getting through.\n\n"
        "⚠️ **Side Effects:** None. The anomaly detector is deliberately programmed to suppress Sequence (Replay) checks "
        "while a flood is occurring to prevent false positive chain reactions from out-of-order network packets."
    )
    
# 3. MARKOV PROCESS TAMPERING
with attack_tab[2]:
    st.markdown("### Markov Process Tampering")
    
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
        
        # Send initial baseline state
        publish_message(broker_ip, mqtt_topic, init_payload)
        st.info(f"Set initial state: {markov_init_state}. Waiting 1 second...")
        
        # Pause to allow the edge node to register the `prev_state`
        time.sleep(1)
        
        # Send the impossible transition
        if publish_message(broker_ip, mqtt_topic, tgt_payload):
            st.success(f"Injected impossible transition: State {markov_init_state} -> {markov_tgt_state}")

    st.info(
        "**How it works:** The attacker tries to spoof data that looks normal to threshold limits, but violates the "
        "laws of physics or logical state transitions defined by our Process Mining matrix.\n\n"
        "**Real-world Example:** An attacker forces a sensor state to jump instantly from 'Cold/Dry' to 'Hot/Humid'. "
        "While both states are valid on their own, physics dictates a room must pass through intermediate states "
        "(like warming up to 'Normal') first. The Markov model catches this impossible teleportation.\n\n"
        "⚠️ **Side Effects:** Because the target state (Hot/Humid) payload forces a humidity of 80%, it intentionally "
        "exceeds the hardcoded physical limit of 70%. Therefore, this attack will simultaneously trigger a **Data Injection (Out of Bounds)** alert."
    )
    
# 4. REPLAY ATTACK
with attack_tab[3]:
    st.markdown("### Replay Attack")

    col1, col2 = st.columns(2)
    with col1:
        current_seq = st.number_input("Current Valid Sequence", value=50, step=1)
    with col2:
        replay_seq = st.number_input("Captured Old Sequence", value=10, step=1)
        
    if st.button("♻️ Inject Replay", use_container_width=True):
        valid_payload = {"temperature": 24.5, "humidity": 50.0, "seq": current_seq, "state": 4}
        replay_payload = {"temperature": 24.5, "humidity": 50.0, "seq": replay_seq, "state": 4}
        
        # Send the valid sequence to advance the edge node's memory
        publish_message(broker_ip, mqtt_topic, valid_payload)
        st.info(f"Sent valid packet (seq: {current_seq}). Waiting 1 second...")
        
        # Pause to allow edge node processing
        time.sleep(1)
        
        # Inject the older, captured sequence
        if publish_message(broker_ip, mqtt_topic, replay_payload):
            st.success(f"Injected Replay Attack (seq: {replay_seq})")
    
    st.info(
        "**How it works:** The attacker intercepts a legitimate, valid payload sent by the sensor. Later, they re-transmit "
        "(replay) that exact same payload to the broker to trick the system.\n\n"
        "**Real-world Example:** A hacker records a 'temperature is normal' message (Sequence #10). Later, they physically "
        "set the room on fire. While the sensor tries to send high-temperature warnings (Sequence #50), the hacker "
        "floods the network with the old Sequence #10 message to hide the fire from the operators.\n\n"
        "⚠️ **Side Effects:** None. The attack deliberately uses completely normal temperature, humidity, and state transitions "
        "to ensure it exclusively trips the Sequence logic without triggering AI or Markov bounds."
    )