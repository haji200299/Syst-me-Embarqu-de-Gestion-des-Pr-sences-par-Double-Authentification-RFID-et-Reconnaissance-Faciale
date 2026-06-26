#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define SS_PIN  10
#define RST_PIN 9

MFRC522 rfid(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(0x27, 16, 2); // adjust I2C address if needed

void setup() {
  Serial.begin(9600);       // UART to ESP32
  SPI.begin();
  rfid.PCD_Init();

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Scan your card");
}

void loop() {
  // Wait for a new card
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Build UID string
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
    if (i < rfid.uid.size - 1) uid += ":";
  }
  uid.toUpperCase();

  // Display scanning message
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("UID: " + uid);

  // Send UID to ESP32
  Serial.println(uid);

  // Wait for response (timeout 3s)
  unsigned long start = millis();
  String response = "";
  while (millis() - start < 3000) {
    if (Serial.available()) {
      response = Serial.readStringUntil('\n');
      response.trim();
      break;
    }
  }

  // Show result on LCD
  lcd.setCursor(0, 1);
  if (response == "OK") {
    lcd.print("Access: OK      ");
  } else if (response == "NOT_OK") {
    lcd.print("Access: NOT OK  ");
  } else {
    lcd.print("No response     ");
  }

  delay(3000);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Scan your card");

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}