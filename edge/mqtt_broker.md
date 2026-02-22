# Update System
sudo apt update
sudo apt upgrade -y

# Install Mosquitto
sudo apt install mosquitto mosquitto-clients -y

# Enable and Check Status
sudo systemctl enable mosquitto
sudo systemctl status mosquitto

# Configuration
sudo nano /etc/mosquitto/conf.d/local.conf

'''
listener 1883
allow_anonymous true
'''

Ctrl+X

# Restart Mosquitto
sudo systemctl restart mosquitto

# Test
mosquitto_sub -h localhost -t "test/topic"
mosquitto_pub -h localhost -t "test/topic" -m "Hello World"

-----------------------------------------

# Restart Mosquitto
sudo systemctl restart mosquitto

# Turn It Off
sudo systemctl stop mosquitto
sudo systemctl disable mosquitto