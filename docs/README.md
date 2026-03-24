# 🛡️ AD-IoT: Anomalies Detection in IoT Project

Welcome to the **AD-IoT (Anomalies Detection in IoT)** project repository. This project is a comprehensive edge-to-cloud security testbed designed to simulate, monitor, and detect cyber threats in real-time within an IoT environment. 

It utilizes Machine Learning (Isolation Forest) and Process Mining (Markov Models) at the edge to secure MQTT-based sensor networks.

## 🏗️ System Architecture & Repository Structure

The repository is divided into dedicated modules representing the different layers of an IoT ecosystem:

* 📁 **`/device` (Physical Layer):** Contains the C++ `device.ino` code for the ESP32 microcontroller. It reads physical data from a DHT22 sensor, calculates physical state bins, and publishes telemetry to a local MQTT broker.
* 📁 **`/edge` (Edge Computing Layer):** Contains the core `anomaly_detector.py` script running on a Raspberry Pi 5. It acts as the gateway, analyzing incoming telemetry in real-time to detect anomalies before forwarding the sanitized status to the cloud.
* 📁 **`/cloud` (Application Layer):** Contains the `dashboard.py` Streamlit application. It acts as a public Security Operations Center (SOC), subscribing to a cloud EMQX broker to display live telemetry and active threat alerts.
* 📁 **`/attacks` (Simulation Layer):** Contains the `app.py` Streamlit application, serving as an interactive Attack Control Center to launch simulated cyberattacks against the edge node.
* 📁 **`/docs`:** Contains the Sphinx and reStructuredText (`.rst`) source files for the official project documentation.
* 📁 **`/.github/workflows`:** Contains CI/CD pipelines for automating tasks (e.g., building documentation).

## 👾 Supported Threat Vectors

The testbed is capable of simulating and successfully detecting four distinct types of cyberattacks:

1. **🌊 Flooding (Denial of Service):** Overwhelming the MQTT broker with high-frequency messages to exhaust processing limits.
2. **♻️ Replay Attacks:** Intercepting valid telemetry and re-transmitting old sequence numbers to mask physical events.
3. **🧠 Markov Process Tampering:** Spoofing logically impossible physical state transitions (e.g., teleporting a room from "Cold/Dry" to "Hot/Humid" instantly).
4. **💉 Data Injection:** Evading physical threshold rules by injecting maliciously crafted sensor readings to trick the AI Anomaly Detection model.

## 🚀 Getting Started

To run the complete architecture locally or in the cloud, you will need to start the components in the following order:

1. **Flash the Edge Sensor:** Flash the `/device/device.ino` code to an ESP32 connected to a DHT22 sensor.
2. **Start the Edge Node:** On your Raspberry Pi 5, navigate to the `/edge` folder, install the requirements, and run the Anomaly Detector:
   ```bash
   pip install -r requirements.txt
   python anomaly_detector.py
   ```
3. **Access the Cloud Dashboard:** Access through the next link: [Cloud Dashboard](https://anomaly-detection-iot-gc.streamlit.app)
4. **Launch the Attack Center:** Navigate to the `/attacks` folder and launch the control center to begin testing:
   ```bash
   streamlit run app.py
   ```
## 📚 Documentation
Comprehensive documentation covering the codebases, mathematical models, and deployment guides can be generated using Sphinx. Access through the next link: [Project Documentation](https://estelamb.github.io/Security_IoT/)

---

## 👥 Group C
Yingying Gao

Nouha Madiouni

Estela Mora Barba

Security for IoT Applications, MIoT - 2026
