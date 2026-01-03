#include <math.h>

// === Pin Definitions ===
#define potInputPin A0
#define potFeedbackPin A1
#define in1Pin 12
#define in2Pin 13
#define enablePin 11

// === PID Coefficients ===
float Kp = 1.8;
float Ki = 0.03;
float Kd = 0.4;

// === PID Variables ===
float error = 0;
float previousError = 0;
float integral = 0;
float derivative = 0;

int outputPWM = 0;
const int deadband = 5;

// === RMSE Calculation Variables ===
unsigned long squaredErrorSum = 0;
unsigned long sampleCount = 0;
unsigned long lastRMSEPrint = 0;

// === RMSE Average Tracking ===
float totalRMSE = 0.0;
unsigned int rmseIntervals = 0;

int smoothAnalogRead(int pin) {
  long sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(pin);
    delayMicroseconds(500);
  }
  return sum / 10;
}

void setup() {
  pinMode(in1Pin, OUTPUT);
  pinMode(in2Pin, OUTPUT);
  pinMode(enablePin, OUTPUT);
  Serial.begin(115200); // High baud rate for fast streaming
  delay(100);
}

void loop() {
  int target = smoothAnalogRead(potInputPin);
  int feedback = smoothAnalogRead(potFeedbackPin);

  error = target - feedback;
  integral += error;
  integral = constrain(integral, -1000, 1000);
  derivative = error - previousError;
  previousError = error;

  float controlSignal = Kp * error + Ki * integral + Kd * derivative;

  outputPWM = 0;
  digitalWrite(in1Pin, LOW);
  digitalWrite(in2Pin, LOW);

  if (abs(error) > deadband) {
    outputPWM = constrain(abs(controlSignal), 0, 255);
    if (controlSignal > 0) {
      digitalWrite(in1Pin, HIGH);
      digitalWrite(in2Pin, LOW);
    } else {
      digitalWrite(in1Pin, LOW);
      digitalWrite(in2Pin, HIGH);
    }
  } else {
    integral = 0;
  }

  analogWrite(enablePin, outputPWM);

  squaredErrorSum += (long)error * error;
  sampleCount++;

  // === Serial Print for Node-RED MQTT ===
  Serial.print("T:");
  Serial.print(target);
  Serial.print(",F:");
  Serial.print(feedback);
  Serial.print(",E:");
  Serial.print(error);
  Serial.print(",PWM:");
  Serial.println(outputPWM);

  // === Optional RMSE log every 5s (tagged for debug log) ===
  if (millis() - lastRMSEPrint >= 5000) {
    float rmse = sqrt((float)squaredErrorSum / sampleCount);
    totalRMSE += rmse;
    rmseIntervals++;
    float avgRMSE = totalRMSE / rmseIntervals;

    Serial.print("#RMSE:");
    Serial.print(rmse, 2);
    Serial.print(",Avg:");
    Serial.println(avgRMSE, 2);

    squaredErrorSum = 0;
    sampleCount = 0;
    lastRMSEPrint = millis();
  }

  delay(10);
}
