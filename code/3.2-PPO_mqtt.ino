#define potInputPin A0
#define potFeedbackPin A1
#define in1Pin 12
#define in2Pin 13
#define enablePin 11

const int PWM_LIMIT = 106;

void setup() {
  pinMode(in1Pin, OUTPUT);
  pinMode(in2Pin, OUTPUT);
  pinMode(enablePin, OUTPUT);

  ADCSRA = (ADCSRA & 0b11111000) | 0x04;  // analogRead at ~57.6 kHz
  Serial.begin(250000);                   // Max reliable rate for Uno/Nano
}

void loop() {
  // Read analog values
  uint16_t target = analogRead(potInputPin);
  uint16_t feedback = analogRead(potFeedbackPin);

  // Send sync header + data (6 bytes total)
  Serial.write(0xAA);
  Serial.write(0x55);
  Serial.write((uint8_t *)&target, 2);
  Serial.write((uint8_t *)&feedback, 2);

  // Receive 2-byte PWM command
  static uint8_t buf[2];
  static uint8_t index = 0;

  while (Serial.available()) {
    buf[index++] = Serial.read();
    if (index >= 2) {
      int16_t pwm = (int16_t)((buf[1] << 8) | buf[0]);  // Little endian
      index = 0;

      pwm = constrain(pwm, -255, 255);
      if (abs(pwm) < 10) {
        digitalWrite(in1Pin, LOW);
        digitalWrite(in2Pin, LOW);
        analogWrite(enablePin, 0);
      } else {
        digitalWrite(in1Pin, pwm > 0);
        digitalWrite(in2Pin, pwm < 0);
        analogWrite(enablePin, min(abs(pwm), PWM_LIMIT));
      }
    }
  }
}
