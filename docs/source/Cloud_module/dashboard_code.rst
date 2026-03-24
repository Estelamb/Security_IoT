Anomaly Detection Dashboard
===========================


Overview
--------
This Streamlit application acts as the primary Security Operations Center (SOC) monitor for the IoT testbed. It subscribes to a public cloud MQTT broker (EMQX) to receive real-time telemetry and anomaly alerts from the edge node, displaying them in a live, interactive web interface.

To prevent UI freezing and race conditions, the dashboard utilizes a multithreaded architecture. A background daemon thread handles the MQTT network traffic, safely passing decoded JSON payloads to the main Streamlit rendering thread via a synchronized message queue.

Global Configuration & State
----------------------------

.. py:data:: LOCAL_TZ
   :type: pytz.tzinfo.BaseTzInfo

   Local timezone configuration (``"Europe/Madrid"``) to ensure accurate UI timestamps, especially critical when the Streamlit application is deployed on UTC cloud servers.

.. py:data:: msg_queue
   :type: queue.Queue

   A global, thread-safe queue used to safely transfer decoded MQTT payloads from the background network thread to the Streamlit session state.

Core Functions
--------------

.. py:function:: get_message_queue()

   Creates and caches a thread-safe queue to pass messages between the background MQTT thread and the main Streamlit UI thread.

   :return: A synchronized queue instance.
   :rtype: queue.Queue

.. py:function:: start_mqtt_subscriber()

   Initializes and starts a background daemon thread that continuously listens to the public EMQX MQTT broker (``broker.emqx.io``) on the topic ``ad_iot/group_c/device_1/dashboard`` for incoming telemetry and alert data.

   :return: The configured MQTT client instance.
   :rtype: paho.mqtt.client.Client

.. py:function:: on_message(client, userdata, msg)

   MQTT callback function triggered when a new message arrives from the cloud broker. It decodes the JSON payload and safely places it into the processing queue.

   :param client: The MQTT client instance for this callback.
   :param userdata: The private user data as set in Client() or user_data_set().
   :param msg: An instance of MQTTMessage containing the topic, qos, and payload bytes.

.. py:function:: main()

   Main execution function to render the Streamlit dashboard UI. It continuously pulls from the ``msg_queue`` and dynamically updates the following interface components:
   
   * **System Status Banner:** A high-level indicator of the current network safety.
   * **Threat Status:** Red/Green indicators for active Flooding, Replay, Markov, or Data Injection attacks.
   * **Historical Data Chart:** A rolling 60-second line chart of temperature and humidity.
   * **Alarms Log:** A chronological dataframe of triggered security events.
   * **Live Telemetry:** Metric cards displaying real-time physical readings and Markov states.
