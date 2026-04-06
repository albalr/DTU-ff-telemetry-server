# 🚢 Float Forward Telemetry Server  
### DTU Boat Telemetry Pipeline

A modern telemetry backend for the Float Forward (DTU) boat.  
This system replaces last year's Raspberry Pi with a more reliable, cloud-integrated stack:

- **HiveMQ Cloud** – secure MQTT broker  
- **Python MQTT Bridge** – receives telemetry & writes to InfluxDB  
- **InfluxDB** – time-series storage  
- **Grafana** – real-time dashboards  
- **Cloudflare Tunnel** – remote access  
- **ESP32 Simulator** – realistic telemetry generator for development  

Designed to run on the **DTU mini-PC telemetry server**.

---

# ⚡ System Architecture

```
ESP32 / Simulator
        │
        ▼
   HiveMQ Cloud
 (MQTT over TLS)
        │
        ▼
   MQTT Bridge
  (Python script)
        │
        ▼
    InfluxDB
        │
        ▼
      Grafana
        │
        ▼
 Cloudflare Tunnel
```

---

# 📂 Project Structure

```
ff_server/
│
├── src/
│   ├── mqtt_bridge.py          # Main telemetry pipeline
│   ├── esp32_simulator.py      # Telemetry generator (test)
│   └── __init__.py
│
├── config/
│   └── .env                    # Environment variables (not in Git)
│
├── tools/
│   └── cloudflared.deb         # Optional Cloudflare installer
│
├── old_scripts/                # Previous Raspberry Pi code
│
├── docker-compose.yml          # InfluxDB + Grafana
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 🚀 Running the Telemetry Pipeline

## 1️⃣ Activate Python Virtual Environment

```bash
source ff-env/bin/activate
```

## 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 3️⃣ Run the MQTT Bridge  
(HiveMQ → InfluxDB)

```bash
python src/mqtt_subscriber_basic_test.py
```

Expected output:

```
Connected OK!
Subscribed to boat/telemetry/#
Received gps/speed = 4.3
--- Wrote 1 telemetry row to InfluxDB ---
```

The bridge:

- Subscribes to **all telemetry topics**  
- Parses MQTT payloads  
- Stores processed data in InfluxDB (1 Hz)

---

## 4️⃣ Run the ESP32 Simulator  
(Generates realistic boat telemetry)

```bash
python src/esp32_simulator_basic.py
```

Example output:

```
Published boat/telemetry/gps/speed: 3.87
Published boat/telemetry/battery/1/voltage: 52.4
```

Perfect for development without boat hardware.

---