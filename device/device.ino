/**
 * @file device.ino
 * @brief ESP32 connecting to RPi5 Mosquitto Broker.
 */

#include "DHT.h"
#include <WiFi.h>
#include <PubSubClient.h> // Standard MQTT library
#include <ArduinoJson.h>

// --- CONFIGURATION ---
#define PERIOD 10000
//const char* ssid = "A56 de Estela";
//const char* password = "4hk2fbthruumfqf";
const char* ssid = "CASABAR";
const char* password = "Ju.Es.200105.260701";

// REPLACE THIS with your Raspberry Pi 5 IP address
const char* mqtt_server = "192.168.0.216"; 
const char* mqtt_topic  = "device_1/telemetry";
const char* clientID    = "device_1";

// --- DHT ---
#define DHTPIN 15 
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// --- WIFI and MQTT ---
WiFiClient espClient;
PubSubClient client(espClient);

/**
 * @brief Reconnects the MQTT client to the broker.
 */
void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("[MQTT] - Attempting connection to ");
    Serial.println(mqtt_server);

    // Attempt to connect (using clientID, no username/pass for now)
    if (client.connect(clientID)) {
      Serial.println("[MQTT] - Connected");
    } else {
      Serial.print("[MQTT] - Failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

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

void loop() {
  // 1. Connection Checks
  if (WiFi.status() != WL_CONNECTED) {
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

  // 3. Create JSON Payload
  StaticJsonDocument<200> data; // Reduced size for simple telemetry
  data["temperature"] = isnan(t) ? 0 : t;
  data["humidity"] = isnan(h) ? 0 : h;

  char buffer[256];
  serializeJson(data, buffer);

  // 4. Publish to specific topic
  Serial.print("[TELEMETRY] - Publishing to ");
  Serial.print(mqtt_topic);
  Serial.print(": ");
  Serial.println(buffer);
    
  client.publish(mqtt_topic, buffer);

  delay(PERIOD);
}