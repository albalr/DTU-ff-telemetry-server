#import time
import paho.mqtt.client as paho
from paho import mqtt

#HiveMQ cloud details
BROKER = "fbe643f0aede453b8a874f9eef1b696b.s1.eu.hivemq.cloud"  #cluster Id / URL
PORT = 8883 #TLS port
USER = "ffServer"
PASSWORD = "DtuServer25"
TOPIC = "esp32"


def on_connect(client, userdata, flags, resultCode, props=None):
	if resultCode == 0:
		print("Connected:", resultCode)
		client.subscribe(TOPIC, qos=1)    #subscribe to specified topic
	else:
		print("Connection failed: ", resultCode)

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print messages 
def on_message(client, userdata, msg):
    print("Topic:  "+ msg.topic + "   rc: " + str(msg.qos) + "   msg: " + str(msg.payload.decode()))


# client_id must be unique for each client
client = paho.Client(client_id="subscriberServer", userdata=None, protocol=paho.MQTTv5)

# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)

# set username and password
client.username_pw_set(USER, PASSWORD)

client.on_connect = on_connect

# connect to HiveMQ Cloud on port 8883
client.connect(BROKER, PORT)

# using the callback functions
client.on_subscribe = on_subscribe
client.on_message = on_message

# loop_forever for simplicity, here need to stop the loop manually
# can also use loop_start and loop_stop
client.loop_forever()
