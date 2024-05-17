from flask import Flask, request, jsonify
import requests
import RPi.GPIO as GPIO
import Adafruit_DHT
import time

app = Flask(__name__)

GPIO.cleanup()

# GPIO configuration
DHT_PIN = 18  # GPIO18 (BCM numbering)
LED_PIN_1 = 14  # GPIO14 (BCM numbering)
LED_PIN_2 = 13  # GPIO13 (BCM numbering)


GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN_1, GPIO.OUT)
GPIO.setup(LED_PIN_2, GPIO.OUT)

# DHT sensor configuration
DHT_SENSOR = Adafruit_DHT.DHT22

# Network credentials and host
SSID = "EC8C9A4F9138-2G"
PASSWORD = "05351107860372"
TOKEN = "ANISSA000754"
HOST = "http://192.168.3.7"

# Define helper functions

def read_dht_sensor():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if humidity is None or temperature is None:
        return 0, 0  # Return 0 if failed to read
    return humidity, temperature

def send_data_to_server(sensor_number, data):
    url = f"{HOST}/sensor{sensor_number}?token={TOKEN}&sensor{sensor_number}={data}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f"Data sent to server: {data}")
    else:
        print(f"Failed to send data to server: {response.status_code}")

# Define Flask routes

@app.route('/4/on', methods=['GET'])
def turn_on_led_1():
    if request.args.get('token') == TOKEN:
        GPIO.output(LED_PIN_1, GPIO.HIGH)
        return f"GPIO {LED_PIN_1} turned on", 200
    else:
        return "Unauthorized", 403

@app.route('/4/off', methods=['GET'])
def turn_off_led_1():
    if request.args.get('token') == TOKEN:
        GPIO.output(LED_PIN_1, GPIO.LOW)
        return f"GPIO {LED_PIN_1} turned off", 200
    else:
        return "Unauthorized", 403

@app.route('/5/on', methods=['GET'])
def turn_on_led_2():
    if request.args.get('token') == TOKEN:
        GPIO.output(LED_PIN_2, GPIO.HIGH)
        return f"GPIO {LED_PIN_2} turned on", 200
    else:
        return "Unauthorized", 403

@app.route('/5/off', methods=['GET'])
def turn_off_led_2():
    if request.args.get('token') == TOKEN:
        GPIO.output(LED_PIN_2, GPIO.LOW)
        return f"GPIO {LED_PIN_2} turned off", 200
    else:
        return "Unauthorized", 403

# Main function to read sensor data and send to server

def main():
    while True:
        humidity, temperature = read_dht_sensor()
        if humidity == 0 and temperature == 0:
            print("Failed to read from DHT sensor!")
        else:
            print(f"Humidity: {humidity}%")
            print(f"Temperature: {temperature}°C")
            send_data_to_server(1, temperature)
            send_data_to_server(2, humidity)
        time.sleep(60)

if __name__ == '__main__':
    # Start the web server in a separate thread
    from threading import Thread
    server_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=8000))
    server_thread.start()
    # Run the main loop
    main()
