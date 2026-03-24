
Edge Node Anomaly Detector
==========================

Overview
--------
The ``anomaly_detector.py`` script acts as the primary security gateway for the IoT testbed. Running on the edge node (Raspberry Pi 5), it subscribes to the local MQTT broker to receive raw physical telemetry from the ESP32 sensors. 

It evaluates every incoming message in real-time against four distinct security models before packaging the data with a security status flag and forwarding it to the public Cloud SOC Dashboard.

Supported Threat Detections
---------------------------
The anomaly detector is equipped to identify four specific cyberattack vectors:

* **Flooding (Denial of Service):** Monitors the time delta between incoming messages. If messages arrive faster than the defined threshold, the system flags a DoS attack.
* **Replay Attacks:** Tracks the sequential ID of incoming payloads. If a received sequence number is less than or equal to the previously recorded sequence, it indicates an attacker is re-transmitting old network packets.
* **Markov Process Tampering:** Utilizes a 9x9 probability matrix to map the laws of physics. It calculates if a physical state transition is possible (e.g., a sensor cannot jump instantly from Cold/Dry to Hot/Humid).
* **Data Injection (AI Evasion):** Utilizes an Isolation Forest Machine Learning algorithm trained on a synthetic baseline of normal operations to catch spoofed data that evades basic threshold limits.

Global Configuration & Constants
--------------------------------

.. py:data:: LOCAL_BROKER
   :type: str

   The hostname or IP of the local Mosquitto broker running on the Raspberry Pi 5 (default: ``"localhost"``).

.. py:data:: LOCAL_TOPIC
   :type: str

   The local MQTT topic where the ESP32 edge node publishes its sensor data (default: ``"device_1/telemetry"``).

.. py:data:: DASHBOARD_BROKER
   :type: str

   The public cloud MQTT broker used to forward processed data to the Streamlit UI (default: ``"broker.emqx.io"``).

.. py:data:: FLOOD_THRESHOLD
   :type: float

   Minimum allowed time in seconds between incoming messages to avoid triggering a DoS alert (default: ``0.5``).

.. py:data:: NORMAL_TEMP_RANGE
   :type: tuple

   The physical safe bounds for temperature in degrees Celsius (default: ``(15, 35)``).

.. py:data:: NORMAL_HUM_RANGE
   :type: tuple

   The physical safe bounds for relative humidity percentages (default: ``(30, 70)``).

.. py:data:: STATE_NAMES
   :type: dict

   Maps the calculated 0-8 integer state to a human-readable string (e.g., ``4: "Normal_Normal"``) for Process Mining logs.

.. py:data:: transition_matrix
   :type: numpy.ndarray

   A 9x9 transition matrix representing the probability of moving from one physical state to another. Hardcoded rules set impossible jumps (like Cold to Hot) to ``0.0``.

Core Functions
--------------

.. py:function:: generate_reference_model()

   Generates and trains the baseline AI anomaly detection model.
   
   Creates synthetic reference data representing normal operating conditions based on the predefined physical boundaries. It then fits an Isolation Forest model to establish the anomaly decision boundaries.

   :return: A trained Machine Learning model for anomaly scoring.
   :rtype: sklearn.ensemble.IsolationForest

.. py:function:: export_process_graph()

   Exports the current Process Mining data as a visual graph.

   Converts the stored event records into a pandas DataFrame, processes it with the ``pm4py`` library, and saves a Directly-Follows Graph (DFG) as a PNG image (``process_map.png``). Requires at least 10 logged events to trigger generation.

.. py:function:: on_message(client, userdata, msg)

   MQTT callback function executed upon receiving a new telemetry message.

   Parses the incoming JSON payload and evaluates it against the four independent threat vectors. It updates the global state trackers (sequence, previous state, and message time) and publishes a comprehensive security state payload to the cloud broker.

   :param client: The MQTT client instance for this callback.
   :param userdata: The private user data as set in Client() or user_data_set().
   :param msg: An instance of MQTTMessage containing the topic, qos, and payload bytes.