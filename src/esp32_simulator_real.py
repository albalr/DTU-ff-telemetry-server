import os
import time
import math
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, List, Any

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# =========================================================
# ENV SETUP
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(ENV_PATH)

BROKER = os.getenv("HIVEMQ_HOST")
PORT = int(os.getenv("HIVEMQ_PORT", "8883"))
USER = os.getenv("HIVEMQ_USER")
PASSWORD = os.getenv("HIVEMQ_PASSWORD")

if not BROKER:
    raise ValueError(f"HIVEMQ_HOST is missing. Check {ENV_PATH}")

CLIENT_ID = "esp32_can_bridge_simulator"

# =========================================================
# RUNTIME CONFIG
# =========================================================
MQTT_QOS = 0
MQTT_RETAIN = True

PRINT_EACH_MESSAGE = False
PRINT_TASK_RUNS = False
STATS_INTERVAL_S = 10

# =========================================================
# MQTT SETUP
# =========================================================
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected with rc={rc}")

def on_disconnect(client, userdata, rc, properties=None):
    print(f"[MQTT] Disconnected with rc={rc}")

client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5)
client.username_pw_set(USER, PASSWORD)
client.tls_set()
client.on_connect = on_connect
client.on_disconnect = on_disconnect

print(f"[BOOT] Loading env from: {ENV_PATH}")
print(f"[BOOT] Broker: {BROKER}:{PORT}")
print(f"[BOOT] User: {USER}")
print("[BOOT] Connecting to broker...")

client.connect(BROKER, PORT)
client.loop_start()

# =========================================================
# STATS
# =========================================================
message_count_total = 0
message_count_window = 0
stats_last_time = time.time()

# =========================================================
# SHARED STATE
# =========================================================
@dataclass
class SimState:
    start_time: float = field(default_factory=time.time)

    lat: float = 55.4000
    lon: float = 12.3000
    altitude: float = 1.8
    speed_mps: float = 2.2
    heading_deg: float = 70.0
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    trip_m: float = 0.0

    accel_x: float = 0.0
    accel_y: float = 0.0
    accel_z: float = 9.81
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0

    motor_rpm: float = 1100.0
    motor_power_w: float = 850.0
    motor_direction: str = "Forward"

    dht_temp: float = 22.0
    dht_hum: float = 50.0

    lv_temp: float = 28.0
    lv_hum: float = 45.0

    fix_type: int = 3
    satellites: int = 12

    batt_v: List[float] = field(default_factory=lambda: [53.2, 53.1, 53.0, 53.3])
    batt_i: List[float] = field(default_factory=lambda: [5.5, 5.7, 5.3, 5.8])
    batt_t: List[float] = field(default_factory=lambda: [29.0, 29.6, 28.8, 29.4])
    batt_soc: List[float] = field(default_factory=lambda: [96.2, 95.8, 96.5, 95.9])
    batt_status: List[int] = field(default_factory=lambda: [1, 1, 1, 1])
    batt_alarm: List[int] = field(default_factory=lambda: [0, 0, 0, 0])

state = SimState()

# =========================================================
# HELPERS
# =========================================================
def clamp(value, lo, hi):
    return max(lo, min(hi, value))

def _record_publish(topic: str, payload: str, info):
    global message_count_total, message_count_window
    message_count_total += 1
    message_count_window += 1

    if PRINT_EACH_MESSAGE:
        print(
            f"{time.strftime('%H:%M:%S')} MQTT {topic} -> {payload} "
            f"| rc={info.rc} | qos={MQTT_QOS} | retain={MQTT_RETAIN}"
        )

def publish_float(topic: str, value: float, decimals: int = 2):
    payload = f"{value:.{decimals}f}"
    info = client.publish(topic, payload, qos=MQTT_QOS, retain=MQTT_RETAIN)
    _record_publish(topic, payload, info)

def publish_int(topic: str, value: int):
    payload = str(int(value))
    info = client.publish(topic, payload, qos=MQTT_QOS, retain=MQTT_RETAIN)
    _record_publish(topic, payload, info)

def publish_string(topic: str, value: str):
    info = client.publish(topic, value, qos=MQTT_QOS, retain=MQTT_RETAIN)
    _record_publish(topic, value, info)

# =========================================================
# BOAT PHYSICS / STATE UPDATE
# =========================================================
def update_state(dt: float):
    t = time.time() - state.start_time

    target_speed = 2.5 + 1.0 * math.sin(t / 25.0) + 0.4 * math.sin(t / 7.0)
    state.speed_mps += 0.12 * (target_speed - state.speed_mps)
    state.speed_mps = clamp(state.speed_mps, 0.0, 6.5)

    state.heading_deg = (state.heading_deg + random.uniform(-1.2, 1.2)) % 360
    state.roll_deg = clamp(4.0 * math.sin(t / 4.0) + random.uniform(-0.3, 0.3), -10.0, 10.0)
    state.pitch_deg = clamp(2.0 * math.sin(t / 6.0) + random.uniform(-0.2, 0.2), -5.0, 5.0)

    distance = state.speed_mps * dt
    state.trip_m += distance

    heading_rad = math.radians(state.heading_deg)
    d_north = distance * math.cos(heading_rad)
    d_east = distance * math.sin(heading_rad)

    state.lat += d_north / 111_320.0
    state.lon += d_east / (111_320.0 * math.cos(math.radians(state.lat)))

    state.altitude = clamp(
        1.8 + 0.2 * math.sin(t / 20.0) + random.uniform(-0.05, 0.05),
        0.5,
        3.0,
        )

    state.fix_type = 3
    state.satellites = random.randint(10, 16)

    state.accel_x = random.uniform(-0.25, 0.25)
    state.accel_y = random.uniform(-0.25, 0.25)
    state.accel_z = 9.81 + random.uniform(-0.12, 0.12)
    state.gyro_x = random.uniform(-0.15, 0.15)
    state.gyro_y = random.uniform(-0.15, 0.15)
    state.gyro_z = random.uniform(-0.20, 0.20)

    target_rpm = 850 + state.speed_mps * 170
    state.motor_rpm += 0.18 * (target_rpm - state.motor_rpm)
    state.motor_rpm = clamp(state.motor_rpm, 700, 2200)

    target_power = 250 + state.speed_mps * 300 + random.uniform(-20, 20)
    state.motor_power_w += 0.20 * (target_power - state.motor_power_w)
    state.motor_power_w = clamp(state.motor_power_w, 150, 2500)

    state.motor_direction = "Forward" if state.speed_mps > 0.2 else "Neutral"

    state.dht_temp = clamp(state.dht_temp + random.uniform(-0.08, 0.08), 18.0, 32.0)
    state.dht_hum = clamp(state.dht_hum + random.uniform(-0.5, 0.5), 30.0, 70.0)

    state.lv_temp = clamp(state.lv_temp + random.uniform(-0.08, 0.08), 22.0, 40.0)
    state.lv_hum = clamp(state.lv_hum + random.uniform(-0.5, 0.5), 25.0, 70.0)

    for i in range(4):
        discharge = (state.motor_power_w / 2500.0) * 0.0025 * dt
        state.batt_soc[i] = clamp(state.batt_soc[i] - discharge, 0.0, 100.0)

        current_target = 3.5 + state.motor_power_w / 400.0 + random.uniform(-0.3, 0.3)
        state.batt_i[i] += 0.20 * (current_target - state.batt_i[i])
        state.batt_i[i] = clamp(state.batt_i[i], 0.0, 20.0)

        voltage_target = 49.5 + 0.04 * state.batt_soc[i] - 0.05 * state.batt_i[i]
        state.batt_v[i] += 0.20 * (voltage_target - state.batt_v[i])
        state.batt_v[i] = clamp(state.batt_v[i], 48.0, 54.6)

        temp_target = 25.0 + 0.6 * state.batt_i[i]
        state.batt_t[i] += 0.08 * (temp_target - state.batt_t[i])
        state.batt_t[i] = clamp(state.batt_t[i], 20.0, 45.0)

        state.batt_status[i] = 1
        state.batt_alarm[i] = 1 if (state.batt_t[i] > 42.0 or state.batt_v[i] < 48.5) else 0

# =========================================================
# CAN FRAME -> MQTT PUBLISHERS
# =========================================================
def frame_0x359_batt1_vct():
    publish_float("boat/telemetry/battery/1/voltage", state.batt_v[0], 2)
    publish_float("boat/telemetry/battery/1/current", state.batt_i[0], 2)
    publish_float("boat/telemetry/battery/1/temperature", state.batt_t[0], 2)

def frame_0x360_batt2_vct():
    publish_float("boat/telemetry/battery/2/voltage", state.batt_v[1], 2)
    publish_float("boat/telemetry/battery/2/current", state.batt_i[1], 2)
    publish_float("boat/telemetry/battery/2/temperature", state.batt_t[1], 2)

def frame_0x361_batt3_vct():
    publish_float("boat/telemetry/battery/3/voltage", state.batt_v[2], 2)
    publish_float("boat/telemetry/battery/3/current", state.batt_i[2], 2)
    publish_float("boat/telemetry/battery/3/temperature", state.batt_t[2], 2)

def frame_0x362_batt4_vct():
    publish_float("boat/telemetry/battery/4/voltage", state.batt_v[3], 2)
    publish_float("boat/telemetry/battery/4/current", state.batt_i[3], 2)
    publish_float("boat/telemetry/battery/4/temperature", state.batt_t[3], 2)

def frame_0x35A_batt1_extra():
    publish_int("boat/telemetry/battery/1/status", state.batt_status[0])
    publish_int("boat/telemetry/battery/1/alarm", state.batt_alarm[0])

def frame_0x35B_batt2_extra():
    publish_int("boat/telemetry/battery/2/status", state.batt_status[1])
    publish_int("boat/telemetry/battery/2/alarm", state.batt_alarm[1])

def frame_0x35C_batt3_extra():
    publish_int("boat/telemetry/battery/3/status", state.batt_status[2])
    publish_int("boat/telemetry/battery/3/alarm", state.batt_alarm[2])

def frame_0x35D_batt4_extra():
    publish_int("boat/telemetry/battery/4/status", state.batt_status[3])
    publish_int("boat/telemetry/battery/4/alarm", state.batt_alarm[3])

def frame_0x355_batt1_soc():
    publish_float("boat/telemetry/battery/1/soc", state.batt_soc[0], 2)

def frame_0x356_batt2_soc():
    publish_float("boat/telemetry/battery/2/soc", state.batt_soc[1], 2)

def frame_0x357_batt3_soc():
    publish_float("boat/telemetry/battery/3/soc", state.batt_soc[2], 2)

def frame_0x358_batt4_soc():
    publish_float("boat/telemetry/battery/4/soc", state.batt_soc[3], 2)

def frame_0x001_gnss_status():
    publish_int("boat/telemetry/gps/status", state.fix_type)
    publish_int("boat/telemetry/gps/Nsatellites", state.satellites)

def frame_0x003_gnss_position():
    publish_float("boat/telemetry/gps/latitude", state.lat, 6)
    publish_float("boat/telemetry/gps/longitude", state.lon, 6)

def frame_0x004_gnss_altitude():
    publish_float("boat/telemetry/gps/altitude", state.altitude, 1)

def frame_0x005_gnss_attitude():
    publish_float("boat/telemetry/gps/roll", state.roll_deg, 2)
    publish_float("boat/telemetry/gps/pitch", state.pitch_deg, 2)
    publish_float("boat/telemetry/gps/heading", state.heading_deg, 2)

def frame_0x006_gnss_odo():
    publish_float("boat/telemetry/gps/last_distance", state.trip_m, 2)

def frame_0x007_gnss_speed():
    publish_float("boat/telemetry/gps/speed", state.speed_mps, 2)

def frame_0x009_gnss_imu():
    publish_float("boat/telemetry/gps/accel_x", state.accel_x, 2)
    publish_float("boat/telemetry/gps/accel_y", state.accel_y, 2)
    publish_float("boat/telemetry/gps/accel_z", state.accel_z, 2)
    publish_float("boat/telemetry/gps/angular_rate_x", state.gyro_x, 2)
    publish_float("boat/telemetry/gps/angular_rate_y", state.gyro_y, 2)
    publish_float("boat/telemetry/gps/angular_rate_z", state.gyro_z, 2)

def frame_0x15F40200_motor():
    publish_float("boat/telemetry/motor/speed", state.motor_rpm, 2)
    publish_float("boat/telemetry/motor/power", state.motor_power_w, 2)
    publish_string("boat/telemetry/motor/direction", state.motor_direction)

def frame_0x020_dht_external():
    publish_float("boat/telemetry/dht/temp", state.dht_temp, 2)
    publish_float("boat/telemetry/dht/hum", state.dht_hum, 2)

def local_lv_dht():
    publish_float("boat/telemetry/lv_dht/temp", state.lv_temp, 2)
    publish_float("boat/telemetry/lv_dht/hum", state.lv_hum, 2)

# =========================================================
# SCHEDULER
# =========================================================
class Task:
    def __init__(self, name: str, period_s: float, fn: Callable[[], Any], jitter_ratio: float = 0.05):
        self.name = name
        self.period_s = period_s
        self.fn = fn
        self.jitter_ratio = jitter_ratio
        self.next_run = time.monotonic()

    def maybe_run(self, now: float):
        if now >= self.next_run:
            if PRINT_TASK_RUNS:
                print(f"[TASK] Running {self.name}")
            self.fn()
            jitter = random.uniform(-self.jitter_ratio, self.jitter_ratio) * self.period_s
            self.next_run = now + self.period_s + jitter

tasks = [
    Task("0x359", 0.20, frame_0x359_batt1_vct),
    Task("0x360", 0.20, frame_0x360_batt2_vct),
    Task("0x361", 0.20, frame_0x361_batt3_vct),
    Task("0x362", 0.20, frame_0x362_batt4_vct),

    Task("0x35A", 1.00, frame_0x35A_batt1_extra),
    Task("0x35B", 1.00, frame_0x35B_batt2_extra),
    Task("0x35C", 1.00, frame_0x35C_batt3_extra),
    Task("0x35D", 1.00, frame_0x35D_batt4_extra),

    Task("0x355", 1.00, frame_0x355_batt1_soc),
    Task("0x356", 1.00, frame_0x356_batt2_soc),
    Task("0x357", 1.00, frame_0x357_batt3_soc),
    Task("0x358", 1.00, frame_0x358_batt4_soc),

    Task("0x001", 1.00, frame_0x001_gnss_status),
    Task("0x003", 0.20, frame_0x003_gnss_position),
    Task("0x004", 1.00, frame_0x004_gnss_altitude),
    Task("0x005", 0.10, frame_0x005_gnss_attitude),
    Task("0x006", 1.00, frame_0x006_gnss_odo),
    Task("0x007", 0.20, frame_0x007_gnss_speed),
    Task("0x009", 0.10, frame_0x009_gnss_imu),

    Task("0x15F40200", 0.10, frame_0x15F40200_motor),

    Task("0x020", 1.00, frame_0x020_dht_external),
    Task("lv_dht_local", 1.00, local_lv_dht),
]

# =========================================================
# MAIN LOOP
# =========================================================
def maybe_print_stats():
    global stats_last_time, message_count_window

    now = time.time()
    elapsed = now - stats_last_time

    if elapsed >= STATS_INTERVAL_S:
        rate = message_count_window / elapsed if elapsed > 0 else 0.0
        print(
            f"[STATS] total_messages={message_count_total} "
            f"| last_window_messages={message_count_window} "
            f"| avg_rate={rate:.2f} msg/s"
        )
        stats_last_time = now
        message_count_window = 0

print("[BOOT] ESP32-like simulator started")

last_time = time.monotonic()

try:
    while True:
        now = time.monotonic()
        dt = now - last_time
        last_time = now

        update_state(dt)

        for task in tasks:
            task.maybe_run(now)

        maybe_print_stats()
        time.sleep(0.01)

except KeyboardInterrupt:
    print("[BOOT] Stopping simulator...")

finally:
    client.loop_stop()
    client.disconnect()
    print("[BOOT] Simulator stopped")