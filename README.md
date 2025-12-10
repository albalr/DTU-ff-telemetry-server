"""

The subscribeAndSendToDB.py replaces the old Raspberry Pi telemetry script.

What it does:

- Connect to HiveMQ Cloud securely (MQTT over TLS, port 8883)

- Subscribe to all boat telemetry topics

- Parse and validate incoming MQTT messages

- Write processed telemetry into InfluxDB
    - use official InfluxDB Python client
    - Flux-compatible format
    - write at defined intervals (e.g. 1 Hz)
    - bucket: "boat_telemetry"
    - organization: "docs"

- Handle unexpected network disconnects
    - reconnect automatically to HiveMQ Cloud
    - retry database writes if needed

- (Optional) Forward telemetry to MEBC API (the one provided by Monaco)
    - same logic as older script
    - HTTP POST with JSON payload

- (Optional) Log CSV backup files locally
    - timestamped logs
    - helpful for offline debugging
    - optional, configurable

This new script is 100% equivalent in functionality to the 
old Raspberry Pi script, but modernized for:
    • HiveMQ Cloud MQTT broker (secure & external)
    • InfluxDB 2.x (modern DB with Flux)
    • The new mini-PC server environment
    • Remote access through Cloudflare Tunnel

"""
