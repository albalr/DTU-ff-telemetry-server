import time
import random
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import json

load_dotenv('../config/.env')

#BROKER = os.getenv("HIVEMQ_HOST")
#PORT = int(os.getenv("HIVEMQ_PORT"))
#USER = os.getenv("HIVEMQ_USER")
#PASSWORD = os.getenv("HIVEMQ_PASSWORD")
BROKER = "fbe643f0aede453b8a874f9eef1b696b.s1.eu.hivemq.cloud"  #cluster Id / URL
PORT = 8883 #TLS port
USER = "ffServer"
PASSWORD = "BoatServer25"
TOPIC = "boat/telemetry/frame"


# ==========================
# MQTT Client Setup
# ==========================
client = mqtt.Client(client_id="telemetry_simulator", protocol=mqtt.MQTTv5)
client.max_inflight_messages_set(100)
client.username_pw_set(USER, PASSWORD)
client.tls_set()  # Use default TLS settings
client.connect(BROKER, PORT)
client.loop_start()
print("Simulator connected to HiveMQ Cloud!")


# ========================================
# ALL TELEMETRY TOPICS (same as last year)
# ========================================
'''topics = [
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
'''
#send a frame with all the topics in the 
#payload, this reduces the overhead of having arounf 50 topics
#and hopefully lets us use qos1

def generate_frame():
    frame = {
        "battery": {},
        "gps": {},
        "motor": {},
        "environment": {}
    }

    # Batteries
    for i in range(1, 5):
        frame["battery"][str(i)] = {
            "voltage": round(random.uniform(50, 54), 2),
            "current": round(random.uniform(3, 10), 2),
            "temperature": round(random.uniform(25, 40), 1),
            "soc": random.randint(70, 100),
            "status": 1,
            "alarm": 0
        }

    # GPS
    frame["gps"] = {
        "latitude": 55.0 + random.uniform(-0.005, 0.005),
        "longitude": 12.0 + random.uniform(-0.005, 0.005),
        "altitude": round(random.uniform(0, 5), 2),
        "status": 1,
        "Nsatellites": random.randint(8, 15),
        "roll": round(random.uniform(-1, 1), 3),
        "pitch": round(random.uniform(-1, 1), 3),
        "heading": round(random.uniform(0, 360), 2),
        "last_distance": round(random.uniform(0, 5), 2),
        "speed": round(random.uniform(0, 6), 2),
        "accel_x": round(random.uniform(-1, 1), 3),
        "accel_y": round(random.uniform(-1, 1), 3),
        "accel_z": round(random.uniform(-1, 1), 3),
        "angular_rate_x": round(random.uniform(-1, 1), 3),
        "angular_rate_y": round(random.uniform(-1, 1), 3),
        "angular_rate_z": round(random.uniform(-1, 1), 3)
    }

    # Motor
    frame["motor"] = {
        "speed": random.randint(900, 1500),
        "power": random.randint(300, 2000),
        "direction": random.choice(["Forward", "Neutral", "Reverse"]),
        "current": round(random.uniform(5, 20), 2)
    }

    # DHT + LV battery
    frame["DHT + LV battery"] = {
        "dht_temp": round(random.uniform(20, 35), 1),
        "dht_hum": round(random.uniform(30, 60), 1),
        "lv_dht_temp": round(random.uniform(20, 35), 1),
        "lv_dht_hum": round(random.uniform(30, 60), 1),
        "lv_batt_v": round(random.uniform(11.5, 12.8), 2)
    }

    return frame


# =================================
# Realistic random value generator
# ==================================
#not used anyomore
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

publishRate = 1
while True:
    telemetryFrame = generate_frame()
    payload = json.dumps(telemetryFrame)

    client.publish(TOPIC, payload, qos= 1)
    print("Published telemetry frame")

    time.sleep(publishRate)

'''while True:
    for topic in topics:
        value = generate_value(topic)
        client.publish(topic, str(value), qos=0)
        print(f"Published {topic}: {value}")
    time.sleep(publishRate)'''