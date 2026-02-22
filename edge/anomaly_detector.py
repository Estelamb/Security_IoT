import paho.mqtt.client as mqtt
import json
import numpy as np
from sklearn.ensemble import IsolationForest
import time

# --- CONFIGURATION ---
BROKER = "localhost"
TOPIC = "device_1/telemetry"

# Data storage to "train" the AI on the fly
# Each entry will now be [temperature, humidity]
data_history = []
model = IsolationForest(contamination=0.1) # Assumes 10% anomalies
trained = False

def on_message(client, userdata, msg):
    global data_history, trained, model
    
    try:
        payload = json.loads(msg.payload.decode())
        temp = payload["temperature"]
        hum = payload["humidity"]
        
        # Current reading as a 2D vector
        current_reading = [temp, hum]
        
        # 1. RULE-BASED DETECTION (Basic Security)
        # Check for physically impossible humidity (DHT22 range is 0-100%)
        if hum < 0 or hum > 100:
            print(f"SECURITY ALERT: Out-of-range humidity detected ({hum}%)")

        # 2. AI-BASED DETECTION (Multivariate Isolation Forest)
        data_history.append(current_reading)
        
        # Wait for 20 readings to build initial behavior profile
        if len(data_history) > 20:  
            X = np.array(data_history)
            
            # Retrain model periodically to adapt to environmental shifts
            if not trained or len(data_history) % 10 == 0:
                model.fit(X)
                trained = True
            
            # Predict if the [temp, hum] combination is an anomaly
            prediction = model.predict([current_reading])
            
            if prediction[0] == -1:
                print(f"ANOMALY DETECTED! Reading: T={temp}°C, H={hum}%")
                # This fulfills the "identify unusual patterns" requirement 
            else:
                print(f"Normal behavior: T={temp}°C, H={hum}%")
                
    except Exception as e:
        print(f"Error processing message: {e}")

# --- MQTT SETUP ---
client = mqtt.Client()
client.on_message = on_message

print(f"Connecting to broker: {BROKER}...")
client.connect(BROKER, 1883)
client.subscribe(TOPIC)

print(f"Monitoring topic '{TOPIC}' for IoT anomalies...")
client.loop_forever()