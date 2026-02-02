# Quick Start Guide - Advanced Driver Safety System

## 🚀 Fast Setup (15 Minutes)

### Step 1: Hardware Connections (5 min)
Connect all components to your Raspberry Pi 5:

**Buzzer/LED System:**
- Positive → GPIO 18
- Ground → GND

**MQ Alcohol Sensor (via MCP3008):**
- Already connected based on your existing setup
- Sensor output → MCP3008 CH0

**ADXL345 Accelerometer:**
- VCC → 3.3V
- GND → GND
- SDA → GPIO 2
- SCL → GPIO 3

**GPS NEO-6M:**
- VCC → 5V
- GND → GND
- TX → GPIO 15 (RXD)
- RX → GPIO 14 (TXD)

**Webcam:**
- USB connection (already working)

### Step 2: Software Installation (5 min)
```bash
# Update system
sudo apt-get update

# Install system dependencies
sudo apt-get install -y portaudio19-dev python3-pyaudio flac python3-serial

# Install Python packages
pip install --break-system-packages scipy imutils dlib opencv-python pygame gpiozero numpy pyserial SpeechRecognition pyaudio adxl345-python spidev

# Download face landmarks file (if not already present)
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
```

### Step 3: Enable Interfaces (2 min)
```bash
sudo raspi-config
```
- Navigate to: **Interface Options**
  - Enable **I2C** ✓
  - Enable **SPI** ✓
  - Enable **Serial Port** ✓
    - Disable login shell over serial
    - Enable serial port hardware
- Select **Finish** and **Reboot**

### Step 4: Configure Email (3 min)
1. Edit the main script:
```bash
nano advanced_safety_system.py
```

2. Update these lines (near the top):
```python
EMAIL_SENDER = "your_email@gmail.com"        # Your Gmail
EMAIL_PASSWORD = "your_app_password"         # Gmail App Password (see below)
EMAIL_RECIPIENT = "emergency_contact@gmail.com"  # Emergency contact
```

**To get Gmail App Password:**
- Go to Google Account → Security → 2-Step Verification → App Passwords
- Generate password for "Mail" on "Other device"
- Copy the 16-character password (no spaces)

### Step 5: Calibrate Sensors (Optional but Recommended)
```bash
# Test GPS (ensure outdoor/sky view)
python3 test_gps.py

# Calibrate alcohol sensor
python3 calibrate_alcohol.py

# Calibrate accelerometer
python3 calibrate_accelerometer.py
```

### Step 6: Run the System! 🎉
```bash
python3 advanced_safety_system.py
```

---

## 🎮 How to Use

### On-Screen Display:
- **Green circle (top right)**: System normal
- **Red circle**: Alert active
- **EAR value**: Eye openness (lower = more closed)
- **MAR value**: Mouth openness (higher = yawning)
- **Tilt angle**: Vehicle orientation
- **GPS coordinates**: Current location (if available)

### Keyboard Controls:
- **'q'** - Quit program
- **'a'** - Manual alcohol sensor test
- **'s'** - Start speaking during alcohol test
- **'r'** - Reset accident/alcohol detection

### System Behavior:

**1. Drowsiness Detection:**
- Monitors your eyes continuously
- Alert if eyes closed for >2 seconds
- Beeps for 6 seconds
- If no response → activates external buzzer
- If still no response → sends emergency email

**2. Yawn Detection:**
- Detects excessive yawning (fatigue indicator)
- Triggers same alert as drowsiness

**3. Alcohol Detection:**
- Continuously monitors MQ sensor
- If alcohol detected:
  1. Shows random text on screen
  2. Press 's' and read text aloud
  3. System verifies your speech
  4. Failed test → emergency alert

**4. Accident Detection:**
- Monitors tilt angle continuously
- Tilt > 45° → IMMEDIATE alert
- Activates buzzer
- Sends emergency email with GPS

**5. Emergency Emails Include:**
- Type of incident
- GPS coordinates
- Google Maps link
- Timestamp

---

## 🔧 Quick Troubleshooting

### "No face detected" message:
- Ensure good lighting
- Look directly at camera
- Adjust webcam angle

### GPS not working:
```bash
ls -l /dev/ttyAMA0    # Should show serial port
sudo i2cdetect -y 1   # Should show 0x53 (ADXL345)
```

### Alcohol sensor too sensitive:
- Run `python3 calibrate_alcohol.py`
- Adjust `ALCOHOL_THRESHOLD` value higher

### Microphone not picking up:
```bash
arecord -l            # List audio devices
arecord -d 5 test.wav # Test recording
aplay test.wav        # Test playback
```

### Permission errors:
```bash
sudo usermod -a -G gpio,i2c,spi $USER
# Then logout and login
```

---

## 📋 System Test Checklist

Before using in vehicle, verify:

- [ ] Webcam displays your face
- [ ] Eyes closing triggers drowsiness alert
- [ ] Yawning triggers alert
- [ ] Alcohol sensor responds to hand sanitizer
- [ ] Speech recognition understands you
- [ ] Tilting device triggers accident alert
- [ ] GPS shows your location
- [ ] Email alerts are received
- [ ] Buzzer/LED activate correctly

---

## 🛡️ Safety Notes

**IMPORTANT:**
- This is a **safety aid**, not autonomous driving
- Always drive responsibly
- Keep phone charged for GPS
- Test all features before actual use
- Ensure stable power supply to Pi
- Regular maintenance and testing recommended

**In Emergency:**
- System sends email automatically
- Recipients should verify driver safety
- GPS coordinates may have 10-30m accuracy

---

## 🚀 Advanced Features

### Auto-start on boot:
```bash
# Create systemd service
sudo nano /etc/systemd/system/safety-system.service
```

Paste:
```ini
[Unit]
Description=Driver Safety System
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/advanced_safety_system.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable safety-system.service
sudo systemctl start safety-system.service
```

### View logs:
```bash
journalctl -u safety-system.service -f
```

---

## 📞 Need Help?

**Common Issues:**
1. GPS needs outdoor/sky view for first fix (30-60 sec)
2. Speech recognition needs quiet environment
3. Alcohol sensor needs 30-second warm-up
4. I2C/SPI must be enabled in raspi-config

**Files Included:**
- `advanced_safety_system.py` - Main program
- `calibrate_alcohol.py` - Calibrate MQ sensor
- `calibrate_accelerometer.py` - Test ADXL345
- `test_gps.py` - Verify GPS module
- `requirements.txt` - Python dependencies
- `INSTALLATION_GUIDE.md` - Detailed setup
- `QUICK_START.md` - This file

---

## 🎯 You're Ready!

The system is designed to save lives by:
- ✓ Preventing drowsy driving accidents
- ✓ Detecting intoxication early
- ✓ Immediate accident response
- ✓ Automatic emergency notifications

**Drive safe! 🚗💨**
