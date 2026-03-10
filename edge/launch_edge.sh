#!/bin/bash

# Navegar al directorio del proyecto
cd "$(dirname "$0")"

echo "📂 Current directory: $(pwd)"

# 1. GESTIÓN DEL BROKER MQTT (Mosquitto)
echo "🌐 Starting MQTT Broker (Mosquitto)..."
# Iniciamos el servicio
sudo systemctl start mosquitto

# Verificación rápida de que el broker está corriendo
if systemctl is-active --quiet mosquitto; then
    echo "✅ Mosquitto Broker is UP on port 1883."
else
    echo "❌ Error: Mosquitto failed to start."
    exit 1
fi

# 2. ACTIVAR ENTORNO VIRTUAL
if [ -d ".venv_edge" ]; then
    echo "🐍 Activating virtual environment .venv_edge..."
    source .venv_edge/bin/activate
else
    echo "❌ Error: .venv_edge not found. Ensure you created it for Topic 9." [cite: 47]
    sudo systemctl stop mosquitto
    exit 1
fi

# 3. EJECUTAR DETECTOR DE ANOMALÍAS
echo "🚀 Starting Anomaly Detector..."
echo "💡 Press Ctrl+C to stop the detector and the broker."

# Ejecutamos el detector
# Usamos un bloque 'trap' para asegurar que el broker se apague incluso si forzamos la salida
trap 'echo -e "\n🛑 Stopping system..."; sudo systemctl stop mosquitto; deactivate; echo "👋 Done."; exit' SIGINT

python3 anomaly_detector.py

# 4. LIMPIEZA FINAL (Si el script termina normalmente)
echo "🛑 Stopping MQTT Broker..."
sudo systemctl stop mosquitto
deactivate
echo "✅ System closed correctly."