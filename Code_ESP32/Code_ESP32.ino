#include <WiFi.h>
#include <esp_camera.h>

// ── WiFi ──────────────────────────────────────────────────────────────────────
const char* SSID = "DESKTOP-5GIDVPG 9477";
const char* PASS = "65s2D26$";

// ── Camera pins (AI-Thinker ESP32-CAM) ───────────────────────────────────────
#define PWDN_GPIO_NUM  32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM   0
#define SIOD_GPIO_NUM  26
#define SIOC_GPIO_NUM  27
#define Y9_GPIO_NUM    35
#define Y8_GPIO_NUM    34
#define Y7_GPIO_NUM    39
#define Y6_GPIO_NUM    36
#define Y5_GPIO_NUM    21
#define Y4_GPIO_NUM    19
#define Y3_GPIO_NUM    18
#define Y2_GPIO_NUM     5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM  23
#define PCLK_GPIO_NUM  22

// ── UART to Arduino ───────────────────────────────────────────────────────────
// GPIO 14 = RX (Arduino TX → here)
// GPIO 13 = TX (here → Arduino RX)
// These are SD card pins — only free if SD card is NOT used
#define UART_RX 13
#define UART_TX 14

// ── Authorized UIDs ───────────────────────────────────────────────────────────
const String AUTHORIZED_UIDS[] = {
  "A1:B2:C3:D4",
  "11:22:33:44"
};
const int UID_COUNT = sizeof(AUTHORIZED_UIDS) / sizeof(AUTHORIZED_UIDS[0]);

WiFiServer server(80);

// ── Camera init ───────────────────────────────────────────────────────────────
void initCamera() {
  camera_config_t config = {};
  config.ledc_channel    = LEDC_CHANNEL_0;
  config.ledc_timer      = LEDC_TIMER_0;
  config.pin_d0          = Y2_GPIO_NUM;
  config.pin_d1          = Y3_GPIO_NUM;
  config.pin_d2          = Y4_GPIO_NUM;
  config.pin_d3          = Y5_GPIO_NUM;
  config.pin_d4          = Y6_GPIO_NUM;
  config.pin_d5          = Y7_GPIO_NUM;
  config.pin_d6          = Y8_GPIO_NUM;
  config.pin_d7          = Y9_GPIO_NUM;
  config.pin_xclk        = XCLK_GPIO_NUM;
  config.pin_pclk        = PCLK_GPIO_NUM;
  config.pin_vsync       = VSYNC_GPIO_NUM;
  config.pin_href        = HREF_GPIO_NUM;
  config.pin_sccb_sda    = SIOD_GPIO_NUM;
  config.pin_sccb_scl    = SIOC_GPIO_NUM;
  config.pin_pwdn        = PWDN_GPIO_NUM;
  config.pin_reset       = RESET_GPIO_NUM;
  config.xclk_freq_hz    = 20000000;
  config.pixel_format    = PIXFORMAT_JPEG;
  config.frame_size      = psramFound() ? FRAMESIZE_UXGA : FRAMESIZE_SVGA;
  config.jpeg_quality    = psramFound() ? 10 : 12;
  config.fb_count        = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed");
    while (true);
  }
}

// ── Handle HTTP client (camera snapshot) ─────────────────────────────────────
void handleHTTPClient() {
  WiFiClient client = server.accept();
  if (!client) return;

  String req = "";
  unsigned long t = millis();
  while (client.connected() && millis() - t < 3000) {
    if (client.available()) {
      char c = client.read();
      if (c == '\n') break;
      if (c != '\r') req += c;
    }
  }
  while (client.available()) client.read();

  if (req.startsWith("GET /frame")) {
    camera_fb_t* stale = esp_camera_fb_get();
    if (stale) esp_camera_fb_return(stale);

    camera_fb_t* fb = esp_camera_fb_get();
    if (fb) {
      client.printf(
        "HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\n"
        "Content-Length: %u\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n",
        fb->len
      );
      client.write(fb->buf, fb->len);
      esp_camera_fb_return(fb);
    } else {
      client.print("HTTP/1.1 500 Internal Server Error\r\nConnection: close\r\n\r\nCapture failed");
    }
  } else {
    client.print("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\nUse GET /frame");
  }

  client.stop();
}

// ── Handle RFID UID from Arduino ─────────────────────────────────────────────
void handleRFID() {
  if (!Serial2.available()) return;

  String uid = Serial2.readStringUntil('\n');
  uid.trim();
  if (uid.length() == 0) return;

  Serial.println("Received UID: " + uid);

  bool authorized = false;
  for (int i = 0; i < UID_COUNT; i++) {
    if (uid.equalsIgnoreCase(AUTHORIZED_UIDS[i])) {
      authorized = true;
      break;
    }
  }

  if (authorized) {
    Serial2.println("OK");
    Serial.println("→ Access granted");
  } else {
    Serial2.println("NOT_OK");
    Serial.println("→ Access denied");
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, UART_RX, UART_TX);

  WiFi.begin(SSID, PASS);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.printf("\nConnected! IP: %s\n", WiFi.localIP().toString().c_str());

  initCamera();
  server.begin();

  Serial.printf("Camera ready: http://%s/frame\n", WiFi.localIP().toString().c_str());
  Serial.printf("RFID listener on RX=GPIO%d, TX=GPIO%d\n", UART_RX, UART_TX);
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  handleRFID();
  handleHTTPClient();
}