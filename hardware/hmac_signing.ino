#include <Wire.h>
#include <MPU6050.h>
#include <Crypto.h>
#include <SHA256.h>

MPU6050 mpu;

const uint8_t SECRET_KEY[] = "MORPHOLOCK_SECRET_2026";

void computeHMAC(String message, char* output) {
  SHA256 sha256;
  uint8_t result[32];

  sha256.resetHMAC(SECRET_KEY, sizeof(SECRET_KEY) - 1);
  sha256.update((const uint8_t*)message.c_str(), message.length());
  sha256.finalizeHMAC(SECRET_KEY, sizeof(SECRET_KEY) - 1, result, sizeof(result));

  for (int i = 0; i < 32; i++) {
    sprintf(output + (i * 2), "%02x", result[i]);
  }
  output[64] = '\0';
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  delay(100);
  mpu.initialize();
  delay(100);

  Serial.println("READY");
}

void loop() {
  // ---- Continuous sensor stream ----
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  float Ax = ax / 16384.0;
  float Ay = ay / 16384.0;
  float Az = az / 16384.0;
  float Gx = gx / 131.0;
  float Gy = gy / 131.0;
  float Gz = gz / 131.0;

  Serial.print(Ax, 4); Serial.print(",");
  Serial.print(Ay, 4); Serial.print(",");
  Serial.print(Az, 4); Serial.print(",");
  Serial.print(Gx, 4); Serial.print(",");
  Serial.print(Gy, 4); Serial.print(",");
  Serial.println(Gz, 4);

  // ---- Listen for SIGN: command ----
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("SIGN:")) {
      String nonce = input.substring(5);

      char hmac_output[65];
      computeHMAC(nonce, hmac_output);

      Serial.print("TOKEN:");
      Serial.println(hmac_output);
    }
  }

  delay(9);
}