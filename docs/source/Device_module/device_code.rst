ESP32 + DHT22 Device
====================

Overview
--------
The ``device.ino`` script runs on an ESP32 microcontroller. It acts as the primary physical node for the IoT Security Testbed. Its main responsibilities are reading physical environment data, translating that data into discrete logical states for Process Mining, and transmitting the telemetry to the local Raspberry Pi 5 Mosquitto broker.

Hardware & Dependencies
-----------------------
* **Microcontroller:** ESP32
* **Sensor:** DHT22 (Temperature and Humidity) connected to GPIO 15.
* **Libraries:**

  * ``DHT.h``: For reading physical sensor data.
  * ``WiFi.h``: For network connectivity.
  * ``PubSubClient.h``: For MQTT communication.
  * ``ArduinoJson.h``: For serializing the data into JSON payloads.

State Calculation (Markov Matrix)
---------------------------------
To enable the Anomaly Detector's Markov and Process Mining algorithms, the raw temperature and humidity floats are mapped into a 9-state matrix. 

The script categorizes physical readings into discrete bins:

* **Temperature Bins:**

  * ``0``: Cold (< 20°C)
  * ``1``: Normal (20°C - 30°C)
  * ``2``: Hot (> 30°C)

* **Humidity Bins:**

  * ``0``: Dry (< 30%)
  * ``1``: Normal (30% - 60%)
  * ``2``: Humid (> 60%)

The final logical state is calculated using the formula: ``(T_bin * 3) + H_bin``, resulting in an integer ranging from 0 to 8 (e.g., State 4 represents Normal/Normal).

Payload Structure
-----------------
Every 5 seconds (defined by ``PERIOD = 5000``), the ESP32 constructs a JSON payload. It includes an incrementing sequence number (``seq``), which is strictly monitored by the SOC to detect Replay Attacks.

.. code-block:: json

    {
      "temperature": 24.5,
      "humidity": 45.2,
      "seq": 105,
      "state": 4
    }

Core Functions
--------------

.. cpp:function:: void setup()

    Initializes the serial monitor, boots the DHT sensor, and establishes the initial WiFi and MQTT network configurations.

.. cpp:function:: void reconnectMQTT()

    A blocking loop that attempts to reconnect to the Mosquitto broker if the connection drops, retrying every 5 seconds.

.. cpp:function:: void loop()

    The main execution cycle. It ensures network stability, polls the DHT22 sensor, computes the 9-state matrix value, packages the JSON, and publishes it to the ``device_1/telemetry`` topic.