import ssl, paho.mqtt.client as mqtt
BROKER = "fbe643f0aede453b8a874f9eef1b696b.s1.eu.hivemq.cloud"  #cluster Id / URL
PORT = 8883 #TLS port
USER = "ffServer"
PASSWORD = "DtuServer25"
TOPIC = "esp32"
#qos -> Quality of Service;  1 = at least one delivery
#on connect call back
def on_connect(client, userdata, flags, resultCode, props=None):
	if resultCode== 0:
		print("Connected:", resultCode)
		client.subscribe(TOPIC, qos=1)
	else:
		print("Connection failed: ", resultCode)
#Call back for incoming messages
def on_message(client, userdata, msg):
	print(msg.topic, msg.payload.decode())
	
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="subscriber")
client.username_pw_set(USER, PASSWORD)
#Enable TLS
client.tls_set(tls_version=ssl.PROTOCOL_TLS) # add cafile="isrgrootx1.pem" if needed
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT)
client.loop_forever()
