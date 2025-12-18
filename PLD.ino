#include <Arduino.h>
#include <SoftwareSerial.h>

SoftwareSerial XBEE(9, 10); // RX, TX

uint32_t pkt = 0;
unsigned long lastTx = 0;

// PUT YOUR GROUND STATION ADDRESS HERE
uint8_t GS_ADDR[8] = { 
  0x00, 0x13, 0xA2, 0x00, 0x42, 0x02, 0x61, 0x17 
};

// -----------------------------------
// SEND TX API FRAME
// -----------------------------------
void sendAPI(const char *payload) {
  uint8_t L = strlen(payload);
  uint16_t len = 14 + L;
  uint8_t sum = 0;

  XBEE.write(0x7E);
  XBEE.write(len >> 8);
  XBEE.write(len & 0xFF);

  auto put = [&](uint8_t b) {
    XBEE.write(b);
    sum += b;
  };

  put(0x10);   // TX frame
  put(0x01);   // frame ID

  for (int i = 0; i < 8; i++) {
    put(GS_ADDR[i]);      // 64-bit destination
  }

  put(0xFF); 
  put(0xFE);              // 16-bit dest unknown
  put(0x00);              // radius
  put(0x00);              // options

  for (int i = 0; i < L; i++) {
    put(payload[i]);
  }

  XBEE.write(0xFF - sum); // checksum
}

// -----------------------------------
// READ RX API FRAME (0x90)
// -----------------------------------
bool readAPI(char *out, size_t maxLen) {

  if (!XBEE.available()) return false;
  if (XBEE.read() != 0x7E) return false;

  while (XBEE.available() < 2);
  uint16_t len = (XBEE.read() << 8) | XBEE.read();

  if (len < 12 || len > 100) return false;

  uint8_t frame[128];

  // Read frame data + checksum
  for (uint16_t i = 0; i < len + 1; i++) {
    while (!XBEE.available());
    frame[i] = XBEE.read();
  }

  if (frame[0] != 0x90) return false;

  // RF payload starts at index 12
  uint8_t idx = 0;
  for (uint16_t i = 12; i < len && idx < maxLen - 1; i++) {
    char c = frame[i];

    if (c >= 32 && c <= 126) {
      out[idx++] = c;
    }
  }

  out[idx] = '\0';
  return true;
}

// -----------------------------------
void setup() {
  Serial.begin(9600);
  XBEE.begin(9600);
  Serial.println("FLIGHT READY");
}

// -----------------------------------
void loop() {

  // 1 Hz telemetry
  if (millis() - lastTx >= 1000) {
    lastTx = millis();
    pkt++;

    float altitude = random(100, 150) + random(0, 99) / 100.0;
    float temperature = random(20, 40) + random(0, 99) / 100.0;
    long pressure = random(100000, 102000);
    float latitude = 23.8103 + (random(-50, 50) / 100000.0);
    float longitude = 90.4125 + (random(-50, 50) / 100000.0);

    String s = String(pkt) + "," +
               String(millis() / 1000.0, 2) + "," +
               String(altitude, 2) + "," +
               String(temperature, 2) + "," +
               String(pressure) + "," +
               String(latitude, 6) + "," +
               String(longitude, 6);

    sendAPI(s.c_str());

    Serial.print("TX: ");
    Serial.println(s);
  }

  // Check command
  char cmd[80];
  if (readAPI(cmd, sizeof(cmd))) {
    Serial.print("COMMAND RECEIVED: ");
    Serial.println(cmd);
  }
}
