import paho.mqtt.client as paho
from paho import mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import WriteOptions
import time
import threading
from dotenv import load_dotenv
import os
import json

load_dotenv('../config/.env')

# ==========================
# HiveMQ cloud details
# ==========================
BROKER = os.getenv("HIVEMQ_HOST")
PORT = int(os.getenv("HIVEMQ_PORT"))
USER = os.getenv("HIVEMQ_USER")
PASSWORD = os.getenv("HIVEMQ_PASSWORD")

TOPIC = "boat/telemetry/frame"

# ==========================
# InfluxDB details
# ==========================
INFLUXDB_URL = os.getenv("INFLUX_URL")
INFLUXDB_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUX_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUX_BUCKET")

client_db = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client_db.write_api(write_options=WriteOptions(batch_size=100, flush_interval=1000, jitter_interval=200,retry_interval=5000))

# ======================================================
# DEFINE ALL EXPECTED TOPICS FOR A FULL TELEMETRY CYCLE
# ======================================================


# ==========================
# MQTT callbacks
# ==========================

def on_connect(client, userdata, flags, rc, props=None):
    if rc == 0:
        print("Connected OK!")
        client.subscribe("boat/telemetry/frame", qos=1)
        print("Subscribed to boat/telemetry/frame")
    else:
        print("Connection failed:", rc)

global messageCounter
messageCounter = 0
def on_message(client, userdata, msg):
    global messageCounter
    messageCounter += 1 

    payload = msg.payload.decode()
    frame = json.loads(payload)

    print("Recieves teleemetry frame")

    p = Point("telemetry").tag("object", "boat")

    for battery_id, battery_data in frame["battery"].items():
        for key, value in battery_data.items():
            field_name = f"battery_{battery_id}_{key}"
            p = p.field(field_name, value)

    for key, value in frame["gps"].items():
        p = p.field(f"gps_{key}", value)

    for key, value in frame["motor"].items():
        if isinstance(value, (int, float)):
            p = p.field(f"motor_{key}", value)
        else:
            p = p.tag(f"motor_{key}", value)

    for key, value in frame["DHT + LV battery"].items():
        p = p.field(key, value)

    write_api.write(
        bucket=INFLUXDB_BUCKET,
        org=INFLUXDB_ORG,
        record=p
    )

    print("Wrote telemetry frame to InfluxDB")



# ==========================
# MQTT client setup
# ==========================
client = paho.Client(client_id="TelemetrySubscriber", userdata=None, protocol=paho.MQTTv5)
client.tls_set()
client.username_pw_set(USER, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT)
client.loop_forever()