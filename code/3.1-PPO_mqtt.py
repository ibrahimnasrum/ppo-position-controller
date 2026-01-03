import serial
import struct
import numpy as np
import json
import time
import paho.mqtt.client as mqtt
from stable_baselines3 import PPO

# === Load PPO Model ===
print("Loading PPO model...")
model = PPO.load(r"C:\Users\ACER\Desktop\Education\MCTA 4362\ppo_dc_motor_model.zip", device="cpu")
print("PPO model loaded")

# === Serial Setup ===
try:
    ser = serial.Serial('COM9', 250000, timeout=0.01)
    print("Serial connected on COM9")
except Exception as e:
    print("Serial connection failed:", e)
    exit()

# === MQTT Setup ===
mqtt_client = mqtt.Client()
try:
    mqtt_client.connect("localhost", 1883, 60)
    print("MQTT connected to localhost:1883")
except Exception as e:
    print("MQTT connection failed:", e)
    exit()

MAX_POSITION = 1023.0
MAX_PWM = 255.0

def read_packet():
    while True:
        if ser.read(1) == b'\xAA' and ser.read(1) == b'\x55':
            data = ser.read(4)
            if len(data) == 4:
                return struct.unpack('<HH', data)

print("Listening to Arduino and publishing to MQTT...")

while True:
    try:
        target, feedback = read_packet()
        obs = np.array([[target / MAX_POSITION, feedback / MAX_POSITION]], dtype=np.float32)
        action, _ = model.predict(obs, deterministic=True)
        pwm_norm = float(action[0])
        error = target - feedback
        pwm_signed = int(np.clip(pwm_norm * MAX_PWM, 0, MAX_PWM) * np.sign(error))

        # === Send PWM back to Arduino ===
        ser.write(struct.pack('<h', pwm_signed))

        # === MQTT Publish ===
        payload = json.dumps({
            "target": target,
            "feedback": feedback,
            "error": error,
            "pwm": pwm_signed
        })
        mqtt_client.publish("dc_motor/control", payload)

        # === Debug print ===
        print(payload)

        time.sleep(0.05)

    except Exception as e:
        print("⚠️ Error:", e)
        continue
