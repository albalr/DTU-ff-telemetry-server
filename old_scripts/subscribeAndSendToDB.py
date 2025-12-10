import paho.mqtt.client as paho
from paho import mqtt
from influxdb_client import InfluxDBClient, Point, WriteOptions
import json

# ====== HiveMQ cloud details ======
BROKER = "fbe643f0aede453b8a874f9eef1b696b.s1.eu.hivemq.cloud"  #cluster Id / URL
PORT = 8883 #TLS port
USER = "ffServer"
PASSWORD = "DTUBoat2025" 

TOPIC = "esp32"
# >>> Consider using wildcard later ("esp32/#")

# ====== Configure InfluxDB connection ========
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "hlZWIE2Tr42azh7C1swJ9dfmn2yyCaXBJkrNE1e6ajaZ2waDGA5azDveP9EukF-RvOsjYfGGTLFTNbm7vl-0hg=="
INFLUXDB_ORG = "docs"
INFLUXDB_BUCKET = "boat_telemetry"

influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = influx_client.write_api(write_options=WriteOptions(batch_size=1))

# ------------------------
# MQTT callbacks
# ------------------------

# Subscribe to specified topic esp32
def on_connect(client, userdata, flags, resultCode, props=None):
    if resultCode == 0:
        print("Connected:", resultCode)
        client.subscribe(TOPIC, qos=1)
    else:
        print("Connection failed:", resultCode)

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    #print("Subscribed:", mid, granted_qos)
    
def on_message(client, userdata, msg):
    print("MSG:", msg.payload.decode())

    # TRY TO PARSE YOUR MQTT DATA
    try:
        data = json.loads(msg.payload.decode())
        # example expected structure:
        # {"temp": 21.5, "humidity": 70, "device": "boat1"}

        measurement = Point("esp32_data")

        for key, value in data.items():
            if isinstance(value, (int, float)):
                measurement = measurement.field(key, value)
            else:
                measurement = measurement.tag(key, str(value))

        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=measurement)
        print("→ Written to InfluxDB")

    except Exception as e:
        print("Error parsing/writing:", e)



# ====== MQTT connection setup ======

# Note: client_id must be unique for each client
client = paho.Client(client_id="subscriberServer", userdata=None, protocol=paho.MQTTv5)

# Enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)

# Set username and password
client.username_pw_set(USER, PASSWORD)

client.on_connect = on_connect

# Using the callback functions
client.on_subscribe = on_subscribe
client.on_message = on_message

# Connect to HiveMQ Cloud on port 8883
client.connect(BROKER, PORT)

# loop_forever for simplicity, here need to stop the loop manually
# We can also use loop_start and loop_stop
client.loop_forever()
