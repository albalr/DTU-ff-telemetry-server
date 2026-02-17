import time
import random
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import json

load_dotenv('../config/.env')


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

#send a frame with all the topics in the 
#payload, this reduces the overhead of having arounf 50 topics
#and hopefully lets us use qos1

def generate_frame():
    frame = {
        "battery": {},
        "gps": {},
        "motor": {},
        "DHT + LV battery": {}
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