/**
 * @file device.ino
 * @brief ESP32 connecting to RPi5 Mosquitto Broker.
 * * Reads temperature and humidity from a DHT22 sensor, calculates a Markov state
 * based on physical ranges, and publishes the telemetry via MQTT as a JSON payload.
 */

#include "DHT.h"
#include <WiFi.h>
#include <PubSubClient.h> // Standard MQTT library
#include <ArduinoJson.h>

// --- CONFIGURATION ---
/** @brief Telemetry publishing period in milliseconds. */
#define PERIOD 5000

// REPLACE THIS with your WiFi Configuration
//const char* ssid = "A56 de Estela";
//const char* password = "4hk2fbthruumfqf";
const char* ssid = "CASABAR";
const char* password = "Ju.Es.200105.260701";

// REPLACE THIS with your Raspberry Pi 5 IP address
//const char* mqtt_server = "10.91.8.64"; 
const char* mqtt_server = "192.168.0.216"; 
const char* mqtt_topic  = "device_1/telemetry";
const char* clientID    = "device_1";

// --- DHT SENSOR SETUP ---
/** @brief GPIO pin connected to the DHT22 data pin. */
#define DHTPIN 15 
/** @brief Type of DHT sensor used. */
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// --- WIFI AND MQTT CLIENTS ---
WiFiClient espClient;
PubSubClient client(espClient);

/** @brief Tracks the number of messages sent for replay attack detection. */
unsigned long msg_count = 0; 

/**
 * @brief Reconnects the MQTT client to the broker if the connection drops.
 */
void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("[MQTT] - Attempting connection to ");
    Serial.println(mqtt_server);

    // Attempt to connect (using clientID, no username/pass for now)
    if (client.connect(clientID)) {
      Serial.println("[MQTT] - Connected!");
    } else {
      Serial.print("[MQTT] - Failed, rc=");
      Serial.print(client.state());
      Serial.println(" - Trying again in 5 seconds");
      delay(5000);
    }
  }
}

/**
 * @brief Initializes serial communication, the DHT sensor, WiFi, and MQTT settings.
 */
void setup() {
  Serial.begin(115200);
  dht.begin();

  // WiFi Setup
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { 
    delay(500); 
    Serial.print(".");
  }
  Serial.println(" Connected!");

  // MQTT Server Setup (Port 1883 for local Mosquitto)
  client.setServer(mqtt_server, 1883);
}

/**
 * @brief Main execution loop. Handles connectivity, reads sensor data, 
 * calculates the physical state, and publishes the payload.
 */
void loop() {
  // 1. Connection Checks
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] - Reconnecting...");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) { delay(500); }
  }

  if (!client.connected()) {
    reconnectMQTT(); 
  }
  client.loop(); 

  // 2. DHT22 Sensor Read
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  // Temperature Bins (Example: <20 Cold, 20-30 Normal, >30 Hot)
  int t_bin = (t < 20) ? 0 : (t <= 30 ? 1 : 2);
  
  // Humidity Bins (Example: <30 Dry, 30-60 Normal, >60 Humid)
  int h_bin = (h < 30) ? 0 : (h <= 60 ? 1 : 2);

  // Mapping to 9 states (0 to 8)
  // Formula: (T_bin * 3) + H_bin
  int current_state = t_bin * 3 + h_bin;        

  // 3. Create JSON Payload
  StaticJsonDocument<200> data; // Reduced size for simple telemetry
  data["temperature"] = isnan(t) ? 0 : t;
  data["humidity"] = isnan(h) ? 0 : h;
  data["seq"] = msg_count;
  data["state"] = current_state;

  char buffer[256];
  serializeJson(data, buffer);

  // 4. Publish to specific topic
  Serial.print("[TELEMETRY] - Publishing to ");
  Serial.print(mqtt_topic);
  Serial.print(": ");
  Serial.println(buffer);
    
  client.publish(mqtt_topic, buffer);

  msg_count++;
  delay(PERIOD);
}