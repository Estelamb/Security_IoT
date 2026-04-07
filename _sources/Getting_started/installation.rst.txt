Installation
============

.. contents:: Table of Contents
   :depth: 2

Node Device
-----------

**Directory:** ``device/``

**Requirements:**

* ESP32 microcontroller.
* DHT22 temperature and humidity sensor.
* Computer or laptop with Arduino IDE and required libraries installed.

Setup Steps:

1. Connect the DHT22 sensor to the ESP32 microcontroller according to the following pin configuration:
   
   * VCC to 3.3V
   * GND to GND
   * Data to D15
   * 10kΩ pull-up resistor between VCC and Data

2. Open the Arduino IDE:
   
   * Install the DHT sensor library by Adafruit.
   * Modify the provided code to include the correct Wi-Fi credentials and MQTT broker details.

3. Upload the provided code to the ESP32 microcontroller to read data from the DHT22 sensor and publish it to the MQTT broker.


Edge Device
-----------

**Directory:** ``edge/``

**Requirements:**

* Raspberry Pi 5 with Raspbian OS installed and configured.

1. MQTT Broker Setup
~~~~~~~~~~~~~~~~~~~~

Update System
^^^^^^^^^^^^^

.. code-block:: bash

    sudo apt update
    sudo apt upgrade -y

Install Mosquitto
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo apt install mosquitto mosquitto-clients -y

Enable and Check Status
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo systemctl enable mosquitto
    sudo systemctl status mosquitto

Configuration
^^^^^^^^^^^^^

1. Open the configuration file:

   .. code-block:: bash

       sudo nano /etc/mosquitto/conf.d/local.conf

2. Add the following lines:

   .. code-block:: text

       listener 1883
       allow_anonymous true

3. Press Ctrl+X, then Y, and Enter to save.

Restart and Test
^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Restart to apply changes
    sudo systemctl restart mosquitto

    # Test (Open two terminals)
    # Terminal 1: Subscribe
    mosquitto_sub -h localhost -t "test/topic"
    # Terminal 2: Publish
    mosquitto_pub -h localhost -t "test/topic" -m "Hello World"

Stop and Disable Mosquitto
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo systemctl stop mosquitto
    sudo systemctl disable mosquitto


2. Virtual Environment Setup 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo apt update
    sudo apt install graphviz python3-venv -y
    python3 -m venv .venv_edge

Install Dependencies
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Activate Environment
    source .venv_edge/bin/activate

    # Install Libraries
    pip install -r requirements.txt


3. Run the Anomaly Detector UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure the MQTT broker is running and the virtual environment is activated before proceeding.

.. code-block:: bash

    # Make the launch script executable
    chmod +x launch_edge.sh

    # Run the Anomaly Detector
    ./launch_edge.sh


Cloud Node
----------

**Directory:** ``cloud/``

**Requirements:**

* GitHub account and project repository.

1. Create a GitHub Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Streamlit Cloud pulls your code directly from GitHub.

1. Go to GitHub.com and create a free account (if you don't have one).
2. Create a new repository (you can name it something like Security_IoT).
3. Upload your dashboard.py file to this new repository.

2. Create a requirements.txt File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When your app runs on your computer, it uses the libraries you installed via pip. When it runs in the cloud, the cloud server needs to know what to install.

1. In your GitHub repository, create a new file and name it requirements.txt.
2. Paste the following text exactly as it is into that file:

   .. code-block:: text

       streamlit
       paho-mqtt
       pandas
       streamlit-autorefresh

3. Save (commit) the file.

3. Deploy to Streamlit Cloud
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Go to share.streamlit.io and log in using your GitHub account.
2. Click the "New app" button.
3. Select your repository.
4. Set the "Main file path" to dashboard.py.
5. Click "Deploy".


Attacks Device
--------------

**Directory:** ``attacks/``

**Requirements:**

* Computer or laptop with Python environment and required libraries installed.

1. Virtual Environment Setup 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo apt update
    sudo apt install graphviz python3-venv -y
    python3 -m venv .venv_attacks

Install Dependencies
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Activate Environment (Linux/macOS)
    source .venv_attacks/bin/activate

    # Activate Environment (Windows PowerShell)
    .\.venv_attacks\Scripts\Activate.ps1 

    # Install Libraries
    pip install -r requirements.txt


2. Run the Attacks UI
~~~~~~~~~~~~~~~~~~~~~

Ensure the virtual environment is activated before proceeding.

.. code-block:: bash

    # Run the Attacks UI
    streamlit run ui_attacks.py