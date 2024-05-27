#include <DHT.h>
#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>

// Replace with your network credentials
const char *ssid = "EC8C9A4F9138-2G";
const char *password = "05351107860372";

const String token = "ANISSA000754";

//const String host = "https://take.pagekite.me";
const String host = "http://192.168.3.235";


/*
ESP8266 board:
 
D1: GPIO5
D2: GPIO4
D3: GPIO0
D4: GPIO2
D5: GPIO14
D6: GPIO12
D7: GPIO13
D8: GPIO15
*/


#define DHTPIN 12  //D6

#define DHTTYPE DHT22

DHT dht(DHTPIN, DHT22, 12);

// Define GPIO pins
#define GPIO14 14 //D5     LED
#define GPIO13 13 //D7 

// Define GPIO states
String output4State = "off";
String output5State = "off";

// Create an ESP8266WebServer object
ESP8266WebServer server(80);

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
    // Print the IP address
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  dht.begin();

  // Set GPIO pins as outputs
  pinMode(GPIO14, OUTPUT);
  pinMode(GPIO13, OUTPUT);

  // Start the web server
  server.on("/4/on", HTTP_GET, []() {
    if (server.arg("token") == token) { // Check if token matches
      digitalWrite(GPIO14, HIGH);
      output4State = "on";
      server.send(200, "text/plain", "D5 turned on");
    } else {
      server.send(403, "text/plain", "Unauthorized");
    }
  });

  server.on("/4/off", HTTP_GET, []() {
    if (server.arg("token") == token) { // Check if token matches
      digitalWrite(GPIO14, LOW);
      output4State = "off";
      server.sendHeader("Access-Control-Allow-Origin", "*");
      server.send(200, "text/plain", "D5 turned off");
    } else {
      server.send(403, "text/plain", "Unauthorized");
    }
  });

  server.on("/5/on", HTTP_GET, []() {
    if (server.arg("token") == token) { // Check if token matches
      digitalWrite(GPIO13, HIGH);
      output5State = "on";
      server.send(200, "text/plain", "D7 turned on");
    } else {
      server.send(403, "text/plain", "Unauthorized");
    }
  });

  server.on("/5/off", HTTP_GET, []() {
    if (server.arg("token") == token) { // Check if token matches
      digitalWrite(GPIO13, LOW);
      output5State = "off";
      server.send(200, "text/plain", "D7 turned off");
    } else {
      server.send(403, "text/plain", "Unauthorized");
    }
  });

  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient(); // Handle client requests

  // Your existing code here
  delay(60000);
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(humidity) || isnan(temperature)) {
    humidity = 0;
    temperature = 0;
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.println("%");
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.print("°C ");

  sendDataToServer(1, temperature, token);
  delay(1000);
  sendDataToServer(2, humidity, token);
}

void sendDataToServer(int sensorNumber, float data, const String &token) {
  WiFiClient client;
  HTTPClient http;

  // Construct the URL
  String url = host + "/sensor" + String(sensorNumber) + "?token=" + token + "&sensor" + String(sensorNumber) + "=" + String(data);

  Serial.print("Sending data to URL: ");
  Serial.println(url);

  // Begin the HTTP request with GET method
  http.begin(client, url);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");

  // Specify the HTTP method explicitly
  http.GET();

  // Send the request and get the response code
  int httpResponseCode = http.GET();

  // Handle the response
  if (httpResponseCode > 0) {
    Serial.printf("HTTP response code for sensor%d: %d\n", sensorNumber, httpResponseCode);
  } else {
    Serial.printf("HTTP request failed for sensor%d: %s\n", sensorNumber, http.errorToString(httpResponseCode).c_str());
  }

  // End the HTTP session
  http.end();
}
