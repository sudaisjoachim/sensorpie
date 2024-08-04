import logging
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import RPi.GPIO as GPIO
import requests
import Adafruit_DHT
import subprocess
from datetime import datetime, timedelta

# Network credentials and host
SSID = "EC8C9A4F9138-2G"
PASSWORD = "05351107860372"
TOKEN = "ANISSA000754"
# HOST = "http://192.168.3.7"
HOST = "https://take.pagekite.me"

# Initialize Flask app
app = Flask(__name__)
CORS(app)
GPIO.cleanup()

# GPIO configuration
DHT_PIN = 5  # GPIO5 (BCM)
PIN_1 = 17  # GPIO17
PIN_2 = 27  # GPIO27

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_1, GPIO.OUT)
GPIO.setup(PIN_2, GPIO.OUT)

# DHT sensor configuration
DHT_SENSOR = Adafruit_DHT.DHT22

# Initialize the I2C interface
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Calibration values (replace with actual measurements for each sensor)
wet_voltage_A = 1.48  # Fully submerged in water (Sensor A)
dry_voltage_A = 3.3  # Completely dry (Sensor A)

wet_voltage_B = 2.3  # Fully submerged in water (Sensor B)
dry_voltage_B = 3.5  # Completely dry (Sensor B)

# Last watering time
last_watering_time_A = datetime.now() - timedelta(days=3)  # Initially set to 3 days ago
last_watering_time_B = datetime.now() - timedelta(days=3)  # Initially set to 3 days ago

def convert_to_percent(voltage, wet_voltage, dry_voltage):
    voltage = max(min(voltage, dry_voltage), wet_voltage)
    percent = int(round((dry_voltage - voltage) / (dry_voltage - wet_voltage) * 100))
    return max(min(percent, 100), 0)

def read_moisture(pin, wet_voltage, dry_voltage):
    chan = AnalogIn(ads, pin)
    logging.info(f"Moisture Voltage: {chan.voltage}")
    moisture_percent = convert_to_percent(chan.voltage, wet_voltage, dry_voltage)
    return chan.voltage, moisture_percent

def read_dht_sensor():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if humidity is None or temperature is None:
        return 0, 0  # Return 0 if failed to read
    return humidity, temperature

def send_data_to_server(sensor_number, data):
    url = f"{HOST}/sensor{sensor_number}?token={TOKEN}&sensor{sensor_number}={data}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Data sent to server: {data}")
        else:
            print(f"Failed to send data to server: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request to server failed: {e}")

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sensors', methods=['GET'])
def get_sensor_data():
    if request.args.get('token') == TOKEN:
        humidity, temperature = read_dht_sensor()
        voltage_A, moisture_percent_A = read_moisture(ADS.P0, wet_voltage_A, dry_voltage_A)
        voltage_B, moisture_percent_B = read_moisture(ADS.P1, wet_voltage_B, dry_voltage_B)
        return jsonify({
            'temperature': temperature,
            'humidity': humidity,
            'moisture_voltage_A': voltage_A,  
            'moisture_percent_A': moisture_percent_A,
            'moisture_voltage_B': voltage_B,  
            'moisture_percent_B': moisture_percent_B
        })
    else:
        return "Unauthorized", 403

@app.route('/4/on', methods=['GET'])
def turn_on_1():
    if request.args.get('token') == TOKEN:
        GPIO.output(PIN_1, GPIO.HIGH)
        return f"GPIO {PIN_1} turned on", 200
    else:
        return "Unauthorized", 403

@app.route('/4/off', methods=['GET'])
def turn_off_1():
    if request.args.get('token') == TOKEN:
        GPIO.output(PIN_1, GPIO.LOW)
        return f"GPIO {PIN_1} turned off", 200
    else:
        return "Unauthorized", 403

@app.route('/5/on', methods=['GET'])
def turn_on_2():
    if request.args.get('token') == TOKEN:
        GPIO.output(PIN_2, GPIO.HIGH)
        return f"GPIO {PIN_2} turned on", 200
    else:
        return "Unauthorized", 403

@app.route('/5/off', methods=['GET'])
def turn_off_2():
    if request.args.get('token') == TOKEN:
        GPIO.output(PIN_2, GPIO.LOW)
        return f"GPIO {PIN_2} turned off", 200
    else:
        return "Unauthorized", 403

@app.route('/reboot', methods=['GET'])
def reboot():
    if request.args.get('token') == TOKEN:
        try:
            subprocess.run(['sudo', 'reboot'], check=True)
            return "Rebooting...", 200
        except subprocess.CalledProcessError as e:
            return str(e), 500
    else:
        return "Unauthorized", 403

@app.route('/shutdown', methods=['GET'])
def shutdown():
    if request.args.get('token') == TOKEN:
        try:
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
            return "Shutting down...", 200
        except subprocess.CalledProcessError as e:
            return str(e), 500
    else:
        return "Unauthorized", 403

# Main function to read sensor data and send to server
def main():
    global last_watering_time_A, last_watering_time_B
    while True:
        try:
            humidity, temperature = read_dht_sensor()
            if humidity is not None and temperature is not None:
                send_data_to_server(3, temperature)
                send_data_to_server(4, humidity)
            else:
                logging.warning("Failed to read DHT sensor.")
            
            voltage_A, moisture_percent_A = read_moisture(ADS.P0, wet_voltage_A, dry_voltage_A)
            voltage_B, moisture_percent_B = read_moisture(ADS.P1, wet_voltage_B, dry_voltage_B)
            
            send_data_to_server(1, moisture_percent_A)
            send_data_to_server(2, moisture_percent_B)

            # Check watering conditions
            if moisture_percent_A < 50 and (datetime.now() - last_watering_time_A).days >= 3:
                GPIO.output(PIN_1, GPIO.HIGH)
                logging.info("Watering Sensor A")
                time.sleep(1 * 60)  # Water for 1 minute
                GPIO.output(PIN_1, GPIO.LOW)
                last_watering_time_A = datetime.now()
            if moisture_percent_B < 50 and (datetime.now() - last_watering_time_B).days >= 3:
                GPIO.output(PIN_2, GPIO.HIGH)
                logging.info("Watering Sensor B")
                time.sleep(1 * 60)  # Water for 1 minute
                GPIO.output(PIN_2, GPIO.LOW)
                last_watering_time_B = datetime.now()
            time.sleep(60)
        except Exception as e:
            logging.error(f"Exception in main loop: {e}")

if __name__ == '__main__':
    from threading import Thread
    server_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=8000))
    server_thread.start()
    main()
