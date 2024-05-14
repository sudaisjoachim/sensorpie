import Adafruit_DHT
import RPi.GPIO as GPIO
from flask import Flask, request, jsonify
import requests
import time

# Network credentials
ssid = "Myssd"
password = "myPassword"
token = "ANISSA000754"
host = "http://"

# Define GPIO pins
DHT_PIN = 18  # GPIO pin connected to DHT22 data pin
GPIO14 = 14
GPIO13 = 13

# Initialize the DHT sensor
DHT_SENSOR = Adafruit_DHT.DHT22

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO14, GPIO.OUT)
GPIO.setup(GPIO13, GPIO.OUT)

app = Flask(__name__)

@app.route('/<int:gpio>/on', methods=['GET'])
def gpio_on(gpio):
    if request.args.get('token') == token:
        if gpio == 14:
            GPIO.output(GPIO14, GPIO.HIGH)
        elif gpio == 13:
            GPIO.output(GPIO13, GPIO.HIGH)
        else:
            return "Invalid GPIO", 400
        return f"GPIO {gpio} turned on", 200
    else:
        return "Unauthorized", 403

@app.route('/<int:gpio>/off', methods=['GET'])
def gpio_off(gpio):
    if request.args.get('token') == token:
        if gpio == 14:
            GPIO.output(GPIO14, GPIO.LOW)
        elif gpio == 13:
            GPIO.output(GPIO13, GPIO.LOW)
        else:
            return "Invalid GPIO", 400
        return f"GPIO {gpio} turned off", 200
    else:
        return "Unauthorized", 403

def send_data_to_server(sensor_number, data):
    url = f"{host}/sensor{sensor_number}?token={token}&sensor{sensor_number}={data}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f"Data sent to server: {data}")
    else:
        print(f"Failed to send data: {response.status_code}")

def read_and_send_dht_data():
    while True:
        humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
        if humidity is not None and temperature is not None:
            print(f"Temperature: {temperature:.1f}C, Humidity: {humidity:.1f}%")
            send_data_to_server(1, temperature)
            send_data_to_server(2, humidity)
        else:
            print("Failed to retrieve data from DHT sensor")
        time.sleep(60)

if __name__ == "__main__":
    from threading import Thread

    # Start the web server in a separate thread
    server_thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 80})
    server_thread.start()

    # Start reading and sending DHT data
    read_and_send_dht_data()
