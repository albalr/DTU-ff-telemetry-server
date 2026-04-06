import time
import random
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

load_dotenv('../config/.env')

BROKER = os.getenv("HIVEMQ_HOST")
PORT = int(os.getenv("HIVEMQ_PORT"))
USER = os.getenv("HIVEMQ_USER")
PASSWORD = os.getenv("HIVEMQ_PASSWORD")

# ==========================
# MQTT Client Setup
# ==========================
client = mqtt.Client(client_id="telemetry_simulator", protocol=mqtt.MQTTv5)
client.username_pw_set(USER, PASSWORD)
client.tls_set()  # Use default TLS settings
client.connect(BROKER, PORT)
client.loop_start()
print("Simulator connected to HiveMQ Cloud!")


# ========================================
# ALL TELEMETRY TOPICS (same as last year)
# ========================================
topics = [
    # ----------- BATTERY 1
    "boat/telemetry/battery/1/voltage",
    "boat/telemetry/battery/1/current",
    "boat/telemetry/battery/1/temperature",
    "boat/telemetry/battery/1/soc",
    "boat/telemetry/battery/1/status",
    "boat/telemetry/battery/1/alarm",

    # ----------- BATTERY 2
    "boat/telemetry/battery/2/voltage",
    "boat/telemetry/battery/2/current",
    "boat/telemetry/battery/2/temperature",
    "boat/telemetry/battery/2/soc",
    "boat/telemetry/battery/2/status",
    "boat/telemetry/battery/2/alarm",

    # ----------- BATTERY 3
    "boat/telemetry/battery/3/voltage",
    "boat/telemetry/battery/3/current",
    "boat/telemetry/battery/3/temperature",
    "boat/telemetry/battery/3/soc",
    "boat/telemetry/battery/3/status",
    "boat/telemetry/battery/3/alarm",

    # ----------- BATTERY 4
    "boat/telemetry/battery/4/voltage",
    "boat/telemetry/battery/4/current",
    "boat/telemetry/battery/4/temperature",
    "boat/telemetry/battery/4/soc",
    "boat/telemetry/battery/4/status",
    "boat/telemetry/battery/4/alarm",

    # ----------- GPS
    "boat/telemetry/gps/latitude",
    "boat/telemetry/gps/longitude",
    "boat/telemetry/gps/altitude",
    "boat/telemetry/gps/status",
    "boat/telemetry/gps/Nsatellites",
    "boat/telemetry/gps/roll",
    "boat/telemetry/gps/pitch",
    "boat/telemetry/gps/heading",
    "boat/telemetry/gps/last_distance",
    "boat/telemetry/gps/speed",
    "boat/telemetry/gps/accel_x",
    "boat/telemetry/gps/accel_y",
    "boat/telemetry/gps/accel_z",
    "boat/telemetry/gps/angular_rate_x",
    "boat/telemetry/gps/angular_rate_y",
    "boat/telemetry/gps/angular_rate_z",

    # ----------- MOTOR
    "boat/telemetry/motor/speed",
    "boat/telemetry/motor/power",
    "boat/telemetry/motor/direction",
    "boat/telemetry/motor/current",

    # ----------- DHT + LV battery
    "boat/telemetry/dht/temp",
    "boat/telemetry/dht/hum",
    "boat/telemetry/lv_dht/temp",
    "boat/telemetry/lv_dht/hum",
    "boat/telemetry/lv_batt_v",
]


# =================================
# Realistic random value generator
# ==================================
def generate_value(topic):
    if "voltage" in topic:
        return round(random.uniform(50, 54), 2)
    if "current" in topic:
        return round(random.uniform(3, 10), 2)
    if "temperature" in topic:
        return round(random.uniform(25, 40), 1)
    if "soc" in topic:
        return random.randint(70, 100)
    if "status" in topic:
        return 1
    if "alarm" in topic:
        return 0
    if "gps/latitude" in topic:
        return 55.0 + random.uniform(-0.005, 0.005)
    if "gps/longitude" in topic:
        return 12.0 + random.uniform(-0.005, 0.005)
    if "gps/speed" in topic:
        return round(random.uniform(0, 6), 2)
    if "gps" in topic:
        return round(random.uniform(-1, 1), 3)
    if "motor/power" in topic:
        return random.randint(300, 2000)
    if "motor/speed" in topic:
        return random.randint(900, 1500)
    if "motor/direction" in topic:
        return random.choice(["Forward", "Neutral", "Reverse"])
    if "lv_batt_v" in topic:
        return round(random.uniform(11.5, 12.8), 2)
    if "dht/temp" in topic or "lv_dht/temp" in topic:
        return round(random.uniform(20, 35), 1)
    if "dht/hum" in topic or "lv_dht/hum" in topic:
        return round(random.uniform(30, 60), 1)

    return 0


# ===============================================
# Main loop, publishes all topics every 1 second
# ===============================================
while True:
    for topic in topics:
        value = generate_value(topic)
        client.publish(topic, str(value), qos=0)
        print(f"Published {topic}: {value}")

    time.sleep(1)