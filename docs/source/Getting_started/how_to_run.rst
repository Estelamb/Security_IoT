How to Run
==========

Before running the project, ensure that you have completed the installation steps outlined in the Installation guide.

Node Device
-----------

**Directory:** ``device/``

1. Ensure that the ESP32 microcontroller is properly connected to the DHT22 sensor and that the code (``device/device.ino``) has been uploaded successfully.
2. Power on the ESP32 microcontroller and monitor the serial output in the Arduino IDE to confirm that it is reading data from the DHT22 sensor and publishing it to the MQTT broker.


Edge Device
-----------

**Directory:** ``edge/``

1. Ensure that the Raspberry Pi 5 is powered on and connected to the same network as the ESP32 microcontroller.
2. Open a terminal on the Raspberry Pi, navigate to the edge directory, and run the launch script:

   .. code-block:: bash

       cd edge
       ./launch_edge.sh


Cloud Node
----------

**Directory:** ``cloud/``

1. Ensure that the cloud node is properly set up and configured according to the installation instructions.
2. Access the dashboard via the web interface: `Cloud Dashboard <https://anomaly-detection-iot-gc.streamlit.app>`_


Attacks Device
--------------

**Directory:** ``attacks/``

1. Ensure that the attack device is properly set up and configured according to the installation instructions.
2. Activate the virtual environment and launch the attack interface:

   .. code-block:: bash

       # Activate Environment (Linux/macOS)
       source .venv_attacks/bin/activate

       # Activate Environment (Windows PowerShell)
       .\.venv_attacks\Scripts\Activate.ps1 

       # Run the application
       streamlit run ui_attacks.py