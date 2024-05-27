import os
import subprocess
from flask import Flask, request, jsonify, render_template, Response
import requests
from flask_cors import CORS
import RPi.GPIO as GPIO
import Adafruit_DHT
import time
from time import sleep
from datetime import datetime
# from picamera import PiCamera
from io import BytesIO
import logging


app = Flask(__name__)
CORS(app)

GPIO.cleanup()

# GPIO configuration
DHT_PIN = 18  # GPIO18 (BCM numbering)
SERVO_PIN_1 = 17  # GPIO17 (BCM numbering)
SERVO_PIN_2 = 27  # GPIO27 (BCM numbering)
LED_PIN_1 = 14  # GPIO14 (BCM numbering)
LED_PIN_2 = 13  # GPIO13 (BCM numbering)
LED_PIN_3 = 15  # GPIO13 (BCM numbering)

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN_1, GPIO.OUT)
GPIO.setup(LED_PIN_2, GPIO.OUT)
GPIO.setup(LED_PIN_3, GPIO.OUT)
GPIO.setup(SERVO_PIN_1, GPIO.OUT)
GPIO.setup(SERVO_PIN_2, GPIO.OUT)

# # Initialize the PiCamera
# camera = PiCamera()
# camera.resolution = (640, 480)
# camera.framerate = 24

# Initialize Servo
servo_1 = GPIO.PWM(SERVO_PIN_1, 50)  # 50Hz frequency
servo_2 = GPIO.PWM(SERVO_PIN_2, 50)  # 50Hz frequency
servo_1.start(0)  # Initial position
servo_2.start(0)  # Initial position

# Current angles
current_angle_1 = 90
current_angle_2 = 90

# DHT sensor configuration
DHT_SENSOR = Adafruit_DHT.DHT22

# Network credentials and host
SSID = "EC8C9A4F9138-2G"
PASSWORD = "05351107860372"
TOKEN = "ANISSA000754"
#HOST = "http://192.168.3.7"
HOST = "https://take.pagekite.me"

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define helper functions
def gen_frames():
    while True:
        stream = BytesIO()
        camera.capture(stream, format='jpeg')
        stream.seek(0)
        frame = stream.read()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        stream.truncate(0)
        stream.seek(0)

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
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    if request.args.get('token') == TOKEN:
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return "Unauthorized", 403


@app.route('/capture_image', methods=['GET'])
def capture_image():
    if request.args.get('token') == TOKEN:
        try:
            # Ensure the directory exists
            image_dir = '/home/pi/projects/images'
            os.makedirs(image_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_path = os.path.join(image_dir, f'pi_{timestamp}.jpg')
            camera.capture(image_path)
            return f"Image captured at {image_path}", 200
        except Exception as e:
            logging.error(f"Error capturing image: {e}")
            return "Internal Server Error", 500
    else:
        return "Unauthorized", 403

def set_servo_angle(servo, angle):
    duty_cycle = angle / 18 + 2.5
    servo.ChangeDutyCycle(duty_cycle)
    sleep(0.5)  # Allow the servo to reach the position
    servo.ChangeDutyCycle(0)  # Stop sending the signal to prevent jitter

@app.route('/set_servo', methods=['GET'])
def set_servo():
    global current_angle_1, current_angle_2
    if request.args.get('token') == TOKEN:
        try:
            servo_id = int(request.args.get('servo_id'))
            angle = int(request.args.get('angle'))
            if 0 <= angle <= 180:
                if servo_id == 1:
                    current_angle_1 = angle
                    set_servo_angle(servo_1, current_angle_1)
                elif servo_id == 2:
                    current_angle_2 = angle
                    set_servo_angle(servo_2, current_angle_2)
                else:
                    return "Invalid servo ID", 400
                return f"Servo {servo_id} set to {angle} degrees", 200
            else:
                return "Angle must be between 0 and 180", 400
        except ValueError:
            return "Invalid input. Servo ID and angle must be integers.", 400
        except Exception as e:
            app.logger.error(f"Error setting servo: {e}")
            return "Internal Server Error", 500
    else:
        return "Unauthorized", 403

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

@app.route('/6/on', methods=['GET'])
def turn_on_led_3():
    if request.args.get('token') == TOKEN:
        GPIO.output(LED_PIN_3, GPIO.HIGH)
        return f"GPIO {LED_PIN_3} turned on", 200
    else:
        return "Unauthorized", 403

@app.route('/6/off', methods=['GET'])
def turn_off_led_3():
    if request.args.get('token') == TOKEN:
        GPIO.output(LED_PIN_3, GPIO.LOW)
        return f"GPIO {LED_PIN_3} turned off", 200
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
