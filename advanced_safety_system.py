# python advanced_safety_system.py --webcam webcam_index

from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2
import pygame
from gpiozero import Buzzer, MCP3008
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import serial
import random
import string
import speech_recognition as sr
from adxl345 import ADXL345

# -------------------------
# CONFIGURATION - EDIT THESE
# -------------------------
EMAIL_SENDER = "your_email@gmail.com"  # Gmail account configured on Pi
EMAIL_PASSWORD = "your_app_password"   # Gmail app password
EMAIL_RECIPIENT = "emergency_contact@gmail.com"  # Emergency contact email

BUZZER_PIN = 18
ALCOHOL_SENSOR_CHANNEL = 0  # MCP3008 channel for MQ sensor
ALCOHOL_THRESHOLD = 500  # Adjust based on your sensor calibration
TILT_THRESHOLD = 45  # degrees

GPS_SERIAL_PORT = "/dev/ttyAMA0"  # or /dev/serial0 for Pi 5
GPS_BAUDRATE = 9600

# -------------------------
# Audio & Buzzer setup
# -------------------------
pygame.mixer.init()
external_buzzer = Buzzer(BUZZER_PIN)

try:
    beep_sound = pygame.mixer.Sound('bep.wav')
except:
    print("Warning: beep.wav not found. Using system beep.")
    beep_sound = None

alert_active = False
beep_start_time = None
buzzer_active = False
BEEP_DURATION = 6  # seconds before external buzzer

# -------------------------
# Hardware initialization
# -------------------------
# Alcohol sensor (MQ sensor via MCP3008)
try:
    alcohol_sensor = MCP3008(channel=ALCOHOL_SENSOR_CHANNEL)
    print("✓ Alcohol sensor initialized")
except Exception as e:
    print(f"⚠️ Alcohol sensor error: {e}")
    alcohol_sensor = None

# Accelerometer ADXL345
try:
    accelerometer = ADXL345()
    print("✓ Accelerometer initialized")
except Exception as e:
    print(f"⚠️ Accelerometer error: {e}")
    accelerometer = None

# GPS Module
try:
    gps_serial = serial.Serial(GPS_SERIAL_PORT, GPS_BAUDRATE, timeout=1)
    print("✓ GPS module initialized")
except Exception as e:
    print(f"⚠️ GPS error: {e}")
    gps_serial = None

# Speech recognition
recognizer = sr.Recognizer()

# -------------------------
# State variables
# -------------------------
alcohol_test_active = False
test_text = ""
alcohol_test_failed = False
accident_detected = False
last_gps_coords = {"lat": None, "lon": None}

# -------------------------
# Alert & Buzzer functions
# -------------------------
def play_beep_alert():
    if beep_sound:
        beep_sound.play(-1)
    else:
        import os
        os.system('beep -f 1000 -l 200 -r 5 &')

def stop_beep_alert():
    if beep_sound:
        beep_sound.stop()

def activate_external_buzzer():
    global buzzer_active
    buzzer_active = True
    external_buzzer.beep(on_time=0.5, off_time=0.5, n=None, background=True)
    print("⚠️ EXTERNAL BUZZER ACTIVATED!")

def deactivate_external_buzzer():
    global buzzer_active
    buzzer_active = False
    external_buzzer.off()
    print("✓ External buzzer deactivated")

# -------------------------
# EAR & MAR calculations
# -------------------------
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def final_ear(shape):
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
    leftEye = shape[lStart:lEnd]
    rightEye = shape[rStart:rEnd]
    leftEAR = eye_aspect_ratio(leftEye)
    rightEAR = eye_aspect_ratio(rightEye)
    ear = (leftEAR + rightEAR) / 2.0
    return ear, leftEye, rightEye

def mouth_aspect_ratio(shape):
    mouth = shape[48:60]  # outer lips
    A = dist.euclidean(mouth[2], mouth[10])
    B = dist.euclidean(mouth[4], mouth[8])
    C = dist.euclidean(mouth[0], mouth[6])
    mar = (A + B) / (2.0 * C)
    return mar

# -------------------------
# Alcohol detection
# -------------------------
def check_alcohol_level():
    if alcohol_sensor is None:
        return False
    try:
        reading = alcohol_sensor.value * 1024  # Convert to ADC value
        return reading > ALCOHOL_THRESHOLD
    except:
        return False

def generate_random_text():
    """Generate random text for sobriety test"""
    words = ['apple', 'banana', 'computer', 'elephant', 'freedom', 
             'guitar', 'hospital', 'internet', 'jacket', 'kitchen']
    return ' '.join(random.sample(words, 4))

def verify_speech(expected_text):
    """Capture and verify speech input"""
    try:
        with sr.Microphone() as source:
            print("🎤 Listening... Speak now!")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            
            spoken_text = recognizer.recognize_google(audio).lower()
            expected_lower = expected_text.lower()
            
            print(f"Expected: {expected_lower}")
            print(f"Heard: {spoken_text}")
            
            # Check similarity (allow some flexibility)
            words_expected = set(expected_lower.split())
            words_spoken = set(spoken_text.split())
            match_ratio = len(words_expected & words_spoken) / len(words_expected)
            
            return match_ratio >= 0.75  # 75% match required
    except sr.WaitTimeoutError:
        print("⚠️ Timeout - No speech detected")
        return False
    except sr.UnknownValueError:
        print("⚠️ Could not understand audio")
        return False
    except Exception as e:
        print(f"⚠️ Speech recognition error: {e}")
        return False

# -------------------------
# Accelerometer - Tilt detection
# -------------------------
def check_tilt_angle():
    """Check if vehicle has tilted beyond threshold"""
    if accelerometer is None:
        return False, 0
    
    try:
        axes = accelerometer.get_axes(True)  # Get g-force values
        x, y, z = axes['x'], axes['y'], axes['z']
        
        # Calculate tilt angle from vertical (z-axis)
        # When upright, z ≈ 1g, x ≈ 0, y ≈ 0
        tilt_angle = np.degrees(np.arccos(z / np.sqrt(x**2 + y**2 + z**2)))
        
        is_tilted = tilt_angle > TILT_THRESHOLD
        return is_tilted, tilt_angle
    except Exception as e:
        print(f"⚠️ Tilt detection error: {e}")
        return False, 0

# -------------------------
# GPS - Location tracking
# -------------------------
def parse_gps_data():
    """Parse NMEA sentences from GPS module"""
    global last_gps_coords
    
    if gps_serial is None:
        return last_gps_coords
    
    try:
        for _ in range(10):  # Try reading multiple lines
            line = gps_serial.readline().decode('ascii', errors='replace')
            
            if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                parts = line.split(',')
                if len(parts) > 6 and parts[2] and parts[4]:
                    # Parse latitude
                    lat_raw = parts[2]
                    lat_deg = float(lat_raw[:2])
                    lat_min = float(lat_raw[2:])
                    lat = lat_deg + lat_min / 60
                    if parts[3] == 'S':
                        lat = -lat
                    
                    # Parse longitude
                    lon_raw = parts[4]
                    lon_deg = float(lon_raw[:3])
                    lon_min = float(lon_raw[3:])
                    lon = lon_deg + lon_min / 60
                    if parts[5] == 'W':
                        lon = -lon
                    
                    last_gps_coords = {"lat": lat, "lon": lon}
                    return last_gps_coords
    except Exception as e:
        print(f"⚠️ GPS parsing error: {e}")
    
    return last_gps_coords

# -------------------------
# Email alert system
# -------------------------
def send_emergency_email(incident_type, gps_coords):
    """Send emergency email with GPS coordinates"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECIPIENT
        msg['Subject'] = f"🚨 EMERGENCY ALERT - {incident_type}"
        
        body = f"""
EMERGENCY ALERT - DRIVER SAFETY SYSTEM

Incident Type: {incident_type}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}

GPS Coordinates:
- Latitude: {gps_coords['lat'] if gps_coords['lat'] else 'N/A'}
- Longitude: {gps_coords['lon'] if gps_coords['lon'] else 'N/A'}

Google Maps Link:
https://www.google.com/maps?q={gps_coords['lat']},{gps_coords['lon']}

This is an automated alert from the vehicle safety monitoring system.
Please check on the driver immediately.

---
Driver Safety Monitoring System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, text)
        server.quit()
        
        print(f"✓ Emergency email sent: {incident_type}")
        return True
    except Exception as e:
        print(f"⚠️ Email send error: {e}")
        return False

# -------------------------
# Argument parser
# -------------------------
ap = argparse.ArgumentParser()
ap.add_argument("-w", "--webcam", type=int, default=0, help="webcam index")
args = vars(ap.parse_args())

# -------------------------
# Thresholds & constants
# -------------------------
EYE_AR_THRESH = 0.25
EYE_AR_CONSEC_FRAMES = 20
COUNTER = 0

MAR_MULTIPLIER = 1.7
MAR_SMOOTH_WIN = 10
lip_hist = []
calib_base = None
CALIB_FRAMES = 30
calib_count = 0

# -------------------------
# Facial detection setup
# -------------------------
print("="*60)
print("🚗 ADVANCED DRIVER SAFETY MONITORING SYSTEM - PI 5")
print("="*60)
print("Features:")
print("  ✓ Drowsiness Detection (EAR)")
print("  ✓ Yawn Detection (MAR)")
print("  ✓ Alcohol Detection + Sobriety Test")
print("  ✓ Accident Detection (Tilt Sensor)")
print("  ✓ GPS Tracking")
print("  ✓ Emergency Email Alerts")
print("="*60)
print("-> Loading facial landmark predictor...")

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

print("-> Starting Video Stream...")
vs = VideoStream(src=args["webcam"]).start()
time.sleep(2.0)
print("✓ System Ready! Press 'q' to quit, 'a' to test alcohol sensor")
print("="*60)

# -------------------------
# Main Loop
# -------------------------
drowsiness_email_sent = False

while True:
    frame = vs.read()
    if frame is None:
        time.sleep(0.1)
        continue

    frame = imutils.resize(frame, width=640)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # -------------------------
    # Check sensors
    # -------------------------
    # GPS update (continuous)
    gps_coords = parse_gps_data()
    
    # Tilt detection
    is_tilted, tilt_angle = check_tilt_angle()
    if is_tilted and not accident_detected:
        accident_detected = True
        print(f"🚨 ACCIDENT DETECTED - Tilt: {tilt_angle:.1f}°")
        activate_external_buzzer()
        send_emergency_email(f"ACCIDENT - Vehicle Tilted {tilt_angle:.1f}°", gps_coords)
    
    # Alcohol detection
    if not alcohol_test_active and check_alcohol_level():
        alcohol_test_active = True
        test_text = generate_random_text()
        print(f"\n{'='*60}")
        print("🍺 ALCOHOL DETECTED - SOBRIETY TEST REQUIRED")
        print(f"{'='*60}")
        print(f"READ THIS TEXT: {test_text}")
        print("You have 20 seconds to read it aloud...")
        print(f"{'='*60}\n")

    # -------------------------
    # Face detection & analysis
    # -------------------------
    rects = detector(gray, 0)
    trigger_alert = False
    ear = 0.0
    smooth_mar = 0.0

    if len(rects) == 0:
        cv2.putText(frame, "No face detected - Look at camera", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,165,255), 2)
        COUNTER = 0
        if not accident_detected and not alcohol_test_active:
            beep_start_time = None
            if alert_active:
                stop_beep_alert()
                alert_active = False
            if buzzer_active:
                deactivate_external_buzzer()
    else:
        for rect in rects:
            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)

            ear, leftEye, rightEye = final_ear(shape)
            mar = mouth_aspect_ratio(shape)

            # Smooth MAR
            lip_hist.append(mar)
            if len(lip_hist) > MAR_SMOOTH_WIN:
                lip_hist.pop(0)
            smooth_mar = np.mean(lip_hist)

            # Calibrate neutral MAR
            if calib_count < CALIB_FRAMES:
                calib_base = smooth_mar if calib_base is None else (calib_base + smooth_mar)/2
                calib_count += 1
                cv2.putText(frame, "Calibrating mouth...", (10,60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255),2)
            else:
                if smooth_mar > calib_base * MAR_MULTIPLIER:
                    trigger_alert = True
                    cv2.putText(frame, "YAWN DETECTED", (10,90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

            # Eye drowsiness
            if ear < EYE_AR_THRESH:
                COUNTER += 1
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    trigger_alert = True
                    cv2.putText(frame, "DROWSINESS ALERT!", (10,30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
            else:
                COUNTER = 0

    # -------------------------
    # Alert Logic (Drowsiness/Yawn)
    # -------------------------
    if trigger_alert:
        if not alert_active:
            alert_active = True
            beep_start_time = time.time()
            play_beep_alert()
            print("⚠️ DROWSINESS ALERT STARTED")
            drowsiness_email_sent = False
        else:
            # Check if 6 seconds passed and driver still drowsy
            if beep_start_time and (time.time() - beep_start_time >= BEEP_DURATION):
                if not buzzer_active:
                    activate_external_buzzer()
                
                # Send email if driver didn't wake up
                if not drowsiness_email_sent:
                    send_emergency_email("DROWSINESS - Driver Not Responding", gps_coords)
                    drowsiness_email_sent = True
    else:
        if alert_active and not accident_detected:
            stop_beep_alert()
            alert_active = False
            print("✓ Drowsiness alert cleared")
        if buzzer_active and not accident_detected:
            deactivate_external_buzzer()
        if not accident_detected:
            beep_start_time = None

    # -------------------------
    # Display overlays
    # -------------------------
    # Status indicator
    status_color = (0,255,0) if not alert_active else (0,0,255)
    status_text = "NORMAL" if not alert_active else "ALERT!"
    cv2.circle(frame, (610, 20), 10, status_color, -1)
    cv2.putText(frame, status_text, (530, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    
    # Metrics
    cv2.putText(frame, f"EAR: {ear:.2f}" if ear>0 else "EAR: N/A", (10, 470),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
    cv2.putText(frame, f"MAR: {smooth_mar:.2f}" if smooth_mar>0 else "MAR: N/A", (150, 470),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
    cv2.putText(frame, f"Tilt: {tilt_angle:.1f}°", (290, 470),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
    
    # GPS display
    if gps_coords['lat'] and gps_coords['lon']:
        cv2.putText(frame, f"GPS: {gps_coords['lat']:.4f}, {gps_coords['lon']:.4f}", 
                    (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,0), 1)
    
    # Alcohol test overlay
    if alcohol_test_active:
        overlay = frame.copy()
        cv2.rectangle(overlay, (50, 100), (590, 350), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        cv2.putText(frame, "ALCOHOL DETECTED!", (120, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)
        cv2.putText(frame, "Read this text aloud:", (100, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        
        # Display test text (split into lines if needed)
        words = test_text.split()
        line1 = ' '.join(words[:2])
        line2 = ' '.join(words[2:])
        cv2.putText(frame, line1, (150, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)
        cv2.putText(frame, line2, (150, 290),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)
        
        cv2.putText(frame, "Press 's' to start speaking", (120, 330),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
    
    # Accident detected overlay
    if accident_detected:
        cv2.putText(frame, "ACCIDENT DETECTED!", (150, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)
        cv2.putText(frame, f"Tilt: {tilt_angle:.1f} degrees", (180, 300),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    cv2.imshow("Advanced Safety System - Pi 5", frame)
    
    # -------------------------
    # Keyboard controls
    # -------------------------
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord("q"):
        print("\n-> Shutting down system...")
        break
    
    elif key == ord("s") and alcohol_test_active:
        # Start speech verification
        print("\n🎤 Starting speech verification...")
        speech_correct = verify_speech(test_text)
        
        if speech_correct:
            print("✓ Sobriety test PASSED")
            alcohol_test_active = False
            alcohol_test_failed = False
        else:
            print("✗ Sobriety test FAILED - Driver appears intoxicated")
            alcohol_test_failed = True
            activate_external_buzzer()
            send_emergency_email("ALCOHOL DETECTED - Failed Sobriety Test", gps_coords)
            alcohol_test_active = False
    
    elif key == ord("a"):
        # Manual alcohol test trigger
        print("\n🧪 Manual alcohol sensor test")
        if check_alcohol_level():
            print("⚠️ Alcohol detected!")
        else:
            print("✓ No alcohol detected")
    
    elif key == ord("r"):
        # Reset accident detection
        accident_detected = False
        alcohol_test_failed = False
        deactivate_external_buzzer()
        print("✓ System reset")

# -------------------------
# Cleanup
# -------------------------
stop_beep_alert()
if buzzer_active:
    deactivate_external_buzzer()
cv2.destroyAllWindows()
vs.stop()
if gps_serial:
    gps_serial.close()
print("✓ System shutdown complete")
