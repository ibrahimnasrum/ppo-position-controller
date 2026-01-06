# ⚙️ Intelligent DC Motor Position Controller (PPO vs PID) — Arduino + Python + MQTT + Node-RED

This repository contains a mini project for **DC motor position control** using:
- ✅ **Reinforcement Learning (PPO – Proximal Policy Optimization)** for intelligent control
- ✅ **Classical PID controller** as a benchmark
- ✅ **Arduino Uno + L298N + Potentiometer** hardware implementation
- ✅ **Python inference bridge (Serial ↔ PPO ↔ MQTT)** for real-time control
- ✅ **Node-RED dashboard** for live monitoring (Target / Feedback / Error / PWM)

---

## 📌 Project Overview

Traditional **PID control** is fast and stable but requires manual tuning and may struggle with changing dynamics.  
**PPO (RL)** can learn a control policy through interaction and adapt to disturbances, but can introduce processing delay on low-power hardware.

This project:
1) trains a PPO policy in simulation (custom Gym environment)  
2) runs PPO inference in real-time (Python) using Arduino sensor feedback  
3) sends the control outputs to Arduino for motor actuation  
4) publishes telemetry to MQTT for visualization (Node-RED)  
5) compares results vs PID controller (RMSE, stability, responsiveness)

---

## 🧱 System Architecture

**A) PPO Control (Real-Time)**

Potentiometer Target + Feedback (Arduino)
│
├── Serial Packet (AA 55 + target + feedback)
│
Python PPO Inference
│
├── PWM Command (signed int16) → Arduino
│
└── MQTT Publish (dc_motor/control) → Node-RED Dashboard


**B) PID Control**
Arduino reads Target + Feedback
│
PID compute PWM
│
Motor driver output + Serial monitoring / Node-RED (optional)

---

## 📁 Repository Files (Main)

| File | Description |
|------|-------------|
| `1-PPO_training.py` | PPO training script + custom Gymnasium environment |
| `3.1-PPO_mqtt.py` | PPO inference (Python) + Serial + MQTT publish |
| `3.2-PPO_mqtt.ino` | Arduino sketch for PPO mode (sends target+feedback, receives PWM) |
| `2.1-PID_mqtt.ino` | Arduino sketch for PID mode (runs PID locally, prints telemetry) |
| `(Report)_Mini_Project_PPO_PID.pdf` | Full mini project report (methodology, results, evaluation) |

---

## ✅ Hardware Requirements

- Arduino Uno
- L298N Motor Driver
- 12V DC Motor
- 2x Potentiometer (1 = target input, 1 = feedback sensor)
- Breadboard + jumper wires
- External power supply for motor driver

---

## 🧰 Software Requirements

### 1) Arduino IDE
- For uploading `.ino` to Arduino Uno

### 2) Python 3.9+
Install Python dependencies (recommended via venv):

```bash
pip install -U gymnasium numpy matplotlib stable-baselines3 torch pyserial paho-mqtt
```


### 3) MQTT Broker (Mosquitto)

Install Mosquitto and run broker on port 1883
(Default setup assumes localhost:1883)


### 4) Node-RED (optional, for dashboard)

- Node-RED dashboard can subscribe to MQTT topic and show:
- target, feedback, error, pwm

## 🚀 Quick Start (PPO Real-Time Control)

**Step 1 — Upload PPO Arduino code**

1. Open:
  - 3.2-PPO_mqtt.ino
2. Select correct Board and COM Port
3. Upload to Arduino

✅ Arduino will:

- Read target and feedback from analog pins
- Send packet to PC via Serial
- Receive PWM command and drive motor

**Step 2 — Train PPO model (optional if you already have model)**

```bash
python 1-PPO_training.py
```

This will:

- Train PPO agent on a custom Gym environment
- Save model file: ppo_dc_motor_model.zip (or similar)
- Plot training reward progress

> Tip: Training time depends on CPU/GPU and timesteps used.

**Step 3 — Run PPO inference bridge (Serial + MQTT)**

1. Ensure Mosquitto broker is running on localhost:1883
2. Edit these values inside 3.1-PPO_mqtt.py if needed:
  - PPO model path
  - COM port (example: COM9)
3. Run:

```bash
python 3.1-PPO_mqtt.py
```

What happens:

- Python reads Arduino packets (target, feedback)
- PPO model predicts action (PWM)
- Python sends PWM back to Arduino
- Python publishes JSON to MQTT topic dc_motor/control

**📡 MQTT Message Format**

```text
dc_motor/control
```

Published JSON payload:

```json
{
  "target": 512,
  "feedback": 490,
  "error": 22,
  "pwm": 80
}
```
---
## 🔌 Serial Packet Protocol (Arduino ↔ Python)

**Arduino → Python**
- Header: 0xAA 0x55
- Payload: 4 bytes
- target (uint16 little-endian)
- feedback (uint16 little-endian)

**Python → Arduino**

- Payload: 2 bytes
  - signed int16 PWM command (little-endian)
This is designed to be compact and fast for real-time streaming.

---
## 🧪 Quick Start (PID Control)

**Step 1 — Upload PID Arduino code**

1) Open:
2.1-PID_mqtt.ino

2) Upload to Arduino

ID coefficients used:
- Kp = 1.8
- Ki = 0.03
- Kd = 0.4

The PID sketch:
- Reads target + feedback
- Computes control signal and drives motor
- Prints telemetry in Serial Monitor format:
- T:<target>,F:<feedback>,E:<error>,PWM:<pwm>

**📊 Evaluation (What to Compare)**

- Suggested evaluation metrics:
- RMSE (Tracking error magnitude)
- Rise time (speed to reach setpoint)
- Overshoot
- Steady-state error
- Response under disturbance/load

From reported results (summary):
- PID tends to be more stable and lower-latency
- PPO shows adaptability but may suffer delays on Arduino-class hardware
---
## 🧠 PPO Training Details (Summary)
**Environment (Gymnasium)**

Observation:
- [actual_position_norm, setpoint_norm]

Action:
- continuous PWM normalized (0.0 to 0.8)

Reward shaping (concept):
- penalize squared error
- penalize large PWM usage
- bonus when error is very small
- episode ends when error small or max steps reached

**PPO Parameters (from training script/report)**
- Policy: MlpPolicy
- learning_rate = 5e-4
- n_steps = 1024
- batch_size = 128
- gamma = 0.98
- gae_lambda = 0.95
- ent_coef = 0.0001
- device = CPU
- timesteps ≈ 100,000 (adjustable)

---
## 🖥️ Node-RED Dashboard (Optional)

Recommended flow:
1. MQTT in node subscribe to:
dc_motor/control

2. JSON parse node

3. Dashboard widgets:

- target
- feedback
- error
- pwm
This gives real-time monitoring without opening Serial Monitor.

---

## 🛠 Troubleshooting
1) Serial connection failed

- Confirm Arduino COM port in Device Manager
- Update Python script COM port (e.g., COM9 → COM3)
- Close Arduino Serial Monitor (only one app can use the port)

2) MQTT connection failed

- Ensure Mosquitto broker is running:
- localhost:1883
- Check firewall permissions
- Verify topic and port

3) Motor not moving / weak torque

- Check external 12V supply and common ground
- Confirm L298N wiring and enable pin
- Check PWM limit settings in Arduino sketch

4) PPO feels laggy

- Reduce print frequency / increase serial timeout efficiency
- Decrease sleep delay in Python loop
- Use faster hardware for inference (future improvement)

## 🔧 Customization

**Change COM port / baud rate**
In Python (3.1-PPO_mqtt.py), update:
-   serial.Serial('COM9', 250000, timeout=0.01)
In Arduino (3.2-PPO_mqtt.ino), ensure:
- Serial.begin(250000);

**Change MQTT broker address**

In Python (3.1-PPO_mqtt.py), update:
- mqtt_client.connect("localhost", 1883, 60)

**Improve PPO performance**
- Train longer timesteps
- Improve reward shaping
- Add noise/disturbance during training for robustness
- Move inference to Raspberry Pi / more powerful SBC

---
## ✅ Conclusion

This project demonstrates the feasibility of applying reinforcement learning (PPO) for DC motor position control on low-cost embedded systems while benchmarking against a classical PID controller.

- PID: faster response, lower computation, stable baseline
- PPO: more adaptable to dynamic changes but limited by inference delay and embedded constraints

Overall, it provides a strong foundation for future work such as:
- more powerful hardware (Raspberry Pi / Jetson)
- better real-time optimization
- extension to safety-critical control applications (robotics / steer-by-wire)

📚 References / Report

See the included report:

(Report)_Mini_Project_PPO_PID.pdf
