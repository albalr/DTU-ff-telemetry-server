import paho.mqtt.client as paho
from paho import mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import WriteOptions
import time
import threading
from dotenv import load_dotenv
import os

load_dotenv()

# ==========================
# HiveMQ cloud details
# ==========================
BROKER = os.getenv("HIVEMQ_HOST")
PORT = int(os.getenv("HIVEMQ_PORT"))
USER = os.getenv("HIVEMQ_USER")
PASSWORD = os.getenv("HIVEMQ_PASSWORD")

# ==========================
# InfluxDB details
# ==========================
INFLUXDB_URL = os.getenv("INFLUX_URL")
INFLUXDB_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUX_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUX_BUCKET")

client_db = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client_db.write_api(write_options=WriteOptions(batch_size=1))

# ==========================
# Cache for incoming values
# ==========================
last_known_values = {}
cache_lock = threading.Lock()

# ==========================
# MQTT callbacks
# ==========================
def on_connect(client, userdata, flags, rc, props=None):
    if rc == 0:
        print("Connected OK!")
        client.subscribe("boat/telemetry/#", qos=1)
        print("Subscribed to boat/telemetry/#")
    else:
        print("Connection failed:", rc)

def on_message(client, userdata, msg):
    global last_known_values

    topic_key = msg.topic.replace("boat/telemetry/", "")
    payload = msg.payload.decode().strip()

    # Parse float when possible
    try:
        value = float(payload)
    except ValueError:
        value = payload

    with cache_lock:
        last_known_values[topic_key] = value

    print(f"Received {topic_key} = {value}")

# ==========================
# Periodic writer
# ==========================
def write_periodically():
    while True:
        time.sleep(1)

        with cache_lock:
            if not last_known_values:
                continue

            p = Point("telemetry").tag("object", "boat")

            for key, value in last_known_values.items():
                if isinstance(value, (int, float)):
                    p = p.field(key.replace("/", "_"), value)
                else:
                    p = p.tag(key.replace("/", "_"), value)

            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=p)

            print("\n--- Wrote 1 telemetry row to InfluxDB ---")
            print(last_known_values)
            print("----------------------------------------\n")

# Start writer thread
threading.Thread(target=write_periodically, daemon=True).start()

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