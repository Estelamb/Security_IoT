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
DEFAULT_TOPIC = "device_1/telemetry"

# --- HELPER FUNCTIONS ---
def publish_message(broker, topic, payload, qos=1):
    """
    Handles the MQTT connection and publishing of a single malicious payload.
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

def main():
    '''Main function to render the Streamlit dashboard UI.'''
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
    st.subheader("Select Attack")
    attack_tab = st.tabs(["💉 Data Injection", "🧠 Markov Process", "🌊 Flooding (DoS)", "♻️ Replay Attack"])

    # 1. DATA INJECTION ATTACK
    with attack_tab[0]:
        st.markdown("### Data Injection")

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
            "⚠️ **Collateral Detections (Side Effects):**\n"
            "* **Markov Tampering:** Likely **YES**. Depending on the last registered physical state of the sensor before you launch this attack, the extreme jump to State 8 will likely trigger a Markov Tampering alert for an impossible transition.\n"
            "* **Flooding (DoS):** **SOMETIMES**. Although this attack only sends one packet, if it arrives at the broker less than 0.5 seconds after a legitimate sensor reading, it will trip the Flooding threshold.\n"
            "* **Replay Attack:** **NO**. The payload hardcodes the sequence to `0`. The detector's logic specifically catches a `0` sequence to reset the tracker (`last_seq = 0`) rather than flagging it as an older sequence."
        )
        
    # 2. MARKOV PROCESS TAMPERING
    with attack_tab[1]:
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
            markov_tgt_hum = st.number_input("Target Humidity", value=85.0)
            markov_tgt_state = st.number_input("Target State", value=8, max_value=8)

        if st.button("🧠 Execute Impossible Jump", use_container_width=True):
            init_payload = {"temperature": markov_init_temp, "humidity": markov_init_hum, "seq": 100, "state": markov_init_state}
            tgt_payload = {"temperature": markov_tgt_temp, "humidity": markov_tgt_hum, "seq": 101, "state": markov_tgt_state}

            publish_message(broker_ip, mqtt_topic, init_payload)
            st.info(f"Set initial state: {markov_init_state}. Waiting 1 second...")
            time.sleep(1)

            if publish_message(broker_ip, mqtt_topic, tgt_payload):
                st.success(f"Injected impossible transition: State {markov_init_state} -> {markov_tgt_state}")

        st.info(
            "**How it works:** The attacker tries to spoof data that looks normal to threshold limits, but violates the "
            "laws of physics or logical state transitions defined by our Process Mining matrix.\n\n"
            "**Real-world Example:** An attacker forces a sensor state to jump instantly from 'Cold/Dry' to 'Hot/Humid'. "
            "While both states are valid on their own, physics dictates a room must pass through intermediate states "
            "(like warming up to 'Normal') first. The Markov model catches this impossible teleportation.\n\n"
            "⚠️ **Collateral Detections (Side Effects):**\n"
            "Executing this attack can potentially trigger **all 4 alarms** across its execution:\n"
            "* **Markov Tampering:** **YES**. Triggers on the second payload due to the impossible state jump (e.g., State 0 to 8).\n"
            "* **Data Injection:** **YES**. The default target payload sends 80% humidity, purposely exceeding the detector's hardcoded 70% limit.\n"
            "* **Replay Attack:** **YES**. Because the sequence numbers are hardcoded (`100` and `101`), running this attack after the legitimate sensor passes sequence 101 (or running the attack twice), forces the sequence backward.\n"
            "* **Flooding (DoS):** **SOMETIMES**. While there is a 1-second pause *between* the attack's two payloads, if you launch the attack less than 0.5 seconds after a legitimate telemetry message arrives at the broker, the first payload will trigger the Flood alarm."
        )
        
    # 3. FLOODING ATTACK
    with attack_tab[2]:
        st.markdown("### Flooding (Denial of Service)")

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

                    progress = int(((i + 1) / flood_count) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Sent {i + 1}/{flood_count} messages...")

                client.disconnect()
                st.success("✅ Flood complete. Check Cloud Dashboard/RPi logs for DoS alerts.")
            except Exception as e:
                st.error(f"Error during flood: {e}")

        st.info(
            "**How it works:** The attacker overwhelms the MQTT broker or edge node by sending a massive burst "
            "of messages in a fraction of a second, violating the expected transmission rate (`FLOOD_THRESHOLD`).\n\n"
            "**Real-world Example:** A botnet targets a central server, maxing out CPU and preventing legitimate sensor data from arriving.\n\n"
            "⚠️ **Collateral Detections (Side Effects):**\n"
            "* **Replay Attack:** **SUPPRESSED**. The detector is deliberately coded (`if not alarms['flood']`) to ignore sequence order during a flood to prevent cascading false positives from out-of-order network packets.\n"
            "* **Data Injection / Markov:** **NO**. The flood payload uses perfectly normal, hardcoded safe values (`Temp: 25.0`, `Hum: 50.0`, `State: 4`) so it will easily pass the AI and Process Mining checks."
        )
        
    # 4. REPLAY ATTACK
    with attack_tab[3]:
        st.markdown("### Replay Attack")

        col1, col2 = st.columns(2)
        with col1:
            current_seq = st.number_input("Current Valid Sequence", value=50, step=1)
        with col2:
            replay_seq = st.number_input("Captured Old Sequence", value=5, step=1)

        if st.button("♻️ Inject Replay", use_container_width=True):
            valid_payload = {"temperature": 24.5, "humidity": 50.0, "seq": current_seq, "state": 4}
            replay_payload = {"temperature": 24.5, "humidity": 50.0, "seq": replay_seq, "state": 4}

            publish_message(broker_ip, mqtt_topic, valid_payload)
            st.info(f"Sent valid packet (seq: {current_seq}). Waiting 1 second...")
            time.sleep(1)

            if publish_message(broker_ip, mqtt_topic, replay_payload):
                st.success(f"Injected Replay Attack (seq: {replay_seq})")

        st.info(
            "**How it works:** The attacker intercepts a legitimate, valid payload sent by the sensor. Later, they re-transmit "
            "(replay) that exact same payload to the broker to trick the system.\n\n"
            "**Real-world Example:** A hacker records a 'temperature is normal' message (Sequence #10). Later, they physically "
            "set the room on fire. While the sensor tries to send high-temperature warnings (Sequence #50), the hacker "
            "floods the network with the old Sequence #10 message to hide the fire from the operators.\n\n"
            "⚠️ **Collateral Detections (Side Effects):**\n"
            "* **Flooding (DoS):** **SOMETIMES**. Even though the script pauses for 1 second between its own messages, if you launch the attack less than 0.5 seconds after a legitimate background sensor message arrives, the detector will flag the attack's first packet as a Flood.\n"
            "* **Data Injection / Markov:** **NO**. The attack deliberately uses completely normal temperature (24.5), humidity (50.0), and state (4) to pass the AI and Markov bounds undetected."
        )



if __name__ == "__main__":
    main()