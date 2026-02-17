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

EXPECTED_FIELDS = [

    # -------- BATTERY 1 --------
    "battery/1/voltage", "battery/1/current", "battery/1/temperature",
    "battery/1/soc", "battery/1/status", "battery/1/alarm",

    # -------- BATTERY 2 --------
    "battery/2/voltage", "battery/2/current", "battery/2/temperature",
    "battery/2/soc", "battery/2/status", "battery/2/alarm",

    # -------- BATTERY 3 --------
    "battery/3/voltage", "battery/3/current", "battery/3/temperature",
    "battery/3/soc", "battery/3/status", "battery/3/alarm",

    # -------- BATTERY 4 --------
    "battery/4/voltage", "battery/4/current", "battery/4/temperature",
    "battery/4/soc", "battery/4/status", "battery/4/alarm",

    # -------- GPS --------
    "gps/latitude", "gps/longitude", "gps/altitude",
    "gps/status", "gps/Nsatellites", "gps/roll", "gps/pitch",
    "gps/heading", "gps/last_distance", "gps/speed",
    "gps/accel_x", "gps/accel_y", "gps/accel_z",
    "gps/angular_rate_x", "gps/angular_rate_y", "gps/angular_rate_z",

    # -------- MOTOR --------
    "motor/speed", "motor/power", "motor/direction", "motor/current",

    # -------- ENVIRONMENT --------
    "dht/temp", "dht/hum",
    "lv_dht/temp", "lv_dht/hum",
    "lv_batt_v"
]

# ==========================
# Cache for incoming values
# ==========================
data_cache = {} 
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
    #global data_cache
    global messageCounter
    messageCounter += 1 

    payload = msg.payload.decode()
    frmae = json.loads(payload)

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

    for key, value in frame["environment"].items():
        p = p.field(key, value)

    write_api.write(
        bucket=INFLUXDB_BUCKET,
        org=INFLUXDB_ORG,
        record=p
    )

    print("Wrote telemetry frame to InfluxDB")



# ===========================================
# WRITE ONLY WHEN FULL TELEMETRY CYCLE ARRIVES
# ===========================================
def write_periodically():
    global data_cache

    while True:
        time.sleep(1)

        with cache_lock:
            # Debug print: how many fields received so far
            print(f"[DEBUG] Cache size: {len(data_cache)} / {len(EXPECTED_FIELDS)}")

            # Which fields are missing?
            missing = [f for f in EXPECTED_FIELDS if f not in data_cache]
            print(f"[DEBUG] Missing fields ({len(missing)}): {missing[:10]} ...")  # print first 10 only

            # ---- TEMPORARY TEST MODE ----
            # Write to Influx when more than 40 fields exist
            if all(field in data_cache for field in EXPECTED_FIELDS):
                print("\n--- DEBUG WRITE: partial frame ---")

                p = Point("telemetry").tag("object", "boat")

                for key, value in data_cache.items():
                    clean_key = key.replace("/", "_")
                    if isinstance(value, (float, int)):
                        p = p.field(clean_key, value)
                    else:
                        p = p.tag(clean_key, value)

                write_api.write(
                    bucket=INFLUXDB_BUCKET,
                    org=INFLUXDB_ORG,
                    record=p
                )

                print(f"--- Wrote {len(data_cache)} fields to InfluxDB (debug mode) ---\n")
                print("Messages per second:", messageCounter)
                messageCounter= 0

                # data_cache.clear() --> Do NOT clear cache ? so we can see which fields never arrive

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