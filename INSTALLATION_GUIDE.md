# Advanced Driver Safety System - Installation Guide

## Hardware Requirements
- Raspberry Pi 5
- Webcam
- MQ Alcohol Sensor (connected via MCP3008 ADC)
- ADXL345 Accelerometer
- GPS NEO-6M Module
- Buzzer (GPIO pin 18)
- LED system (connected with buzzer)

## Software Installation

### 1. System Updates
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Install Python Dependencies
```bash
pip install --break-system-packages scipy imutils dlib opencv-python pygame gpiozero numpy pillow

# Additional packages for new features
pip install --break-system-packages pyserial SpeechRecognition pyaudio adxl345-python

# For MCP3008 (if not already installed)
pip install --break-system-packages spidev
```

### 3. Install System Packages
```bash
# For speech recognition
sudo apt-get install -y portaudio19-dev python3-pyaudio flac

# For GPS serial communication
sudo apt-get install -y python3-serial

# Enable I2C for ADXL345
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable

# Enable SPI for MCP3008
sudo raspi-config
# Navigate to: Interface Options -> SPI -> Enable
```

### 4. Download Required Files
```bash
# Download dlib face landmarks predictor
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
```

### 5. Hardware Wiring

#### MCP3008 (for MQ Alcohol Sensor):
```
MCP3008 Pin -> Pi 5 Pin
VDD    -> 3.3V
VREF   -> 3.3V
AGND   -> GND
CLK    -> GPIO 11 (SCLK)
DOUT   -> GPIO 9 (MISO)
DIN    -> GPIO 10 (MOSI)
CS/SHDN-> GPIO 8 (CE0)
DGND   -> GND

MQ Sensor -> MCP3008
AO     -> CH0 (pin 1)
```

#### ADXL345 (Accelerometer):
```
ADXL345 -> Pi 5
VCC    -> 3.3V
GND    -> GND
SDA    -> GPIO 2 (SDA)
SCL    -> GPIO 3 (SCL)
```

#### GPS NEO-6M:
```
GPS    -> Pi 5
VCC    -> 5V
GND    -> GND
TX     -> GPIO 15 (RXD)
RX     -> GPIO 14 (TXD)
```

#### Buzzer & LED:
```
Buzzer/LED -> Pi 5
+      -> GPIO 18
-      -> GND
```

### 6. Configure Gmail for Email Alerts

1. Go to your Google Account settings
2. Enable 2-Step Verification
3. Generate an App Password:
   - Go to Security -> 2-Step Verification -> App Passwords
   - Create password for "Mail" on "Other (Custom name)"
   - Copy the 16-character password

4. Edit the script and update:
```python
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_16_char_app_password"
EMAIL_RECIPIENT = "emergency_contact@gmail.com"
```

### 7. Calibrate Sensors

#### Alcohol Sensor Calibration:
```bash
python3 calibrate_alcohol.py
# Note the baseline value and adjust ALCOHOL_THRESHOLD in the script
```

#### Accelerometer Calibration:
```bash
python3 calibrate_accelerometer.py
# Ensure vehicle is level, note the readings
```

## Running the System

### Basic Usage:
```bash
python3 advanced_safety_system.py
```

### With specific webcam:
```bash
python3 advanced_safety_system.py --webcam 1
```

### Keyboard Controls:
- `q` - Quit the program
- `a` - Manually test alcohol sensor
- `s` - Start speech recognition during alcohol test
- `r` - Reset accident/alcohol detection

## System Features

### 1. Drowsiness Detection
- Monitors Eye Aspect Ratio (EAR)
- Triggers alert after 20 consecutive frames of closed eyes
- Plays audio beep for 6 seconds
- If driver doesn't wake up, activates external buzzer
- Sends emergency email with GPS coordinates

### 2. Yawn Detection
- Monitors Mouth Aspect Ratio (MAR)
- Calibrates baseline during first 30 frames
- Triggers if MAR exceeds 1.7x baseline

### 3. Alcohol Detection
- Continuously monitors MQ sensor
- When alcohol detected:
  1. Displays random text on screen
  2. User must read text aloud
  3. Speech recognition verifies sobriety
  4. If test failed, sends emergency email

### 4. Accident Detection (Tilt)
- Monitors ADXL345 for vehicle orientation
- Triggers if tilt exceeds 45 degrees
- Immediately:
  1. Activates buzzer/LED
  2. Gets GPS coordinates
  3. Sends emergency email

### 5. GPS Tracking
- Continuously reads NEO-6M module
- Parses NMEA sentences (GPGGA/GNGGA)
- Provides coordinates for emergency alerts

### 6. Emergency Email System
- Sends alerts for:
  - Drowsiness (no response after 6 seconds)
  - Failed alcohol test
  - Accident (tilt > 45°)
- Includes GPS coordinates and Google Maps link

## Troubleshooting

### GPS not working:
```bash
# Check serial port
ls -l /dev/ttyAMA0
ls -l /dev/serial0

# Disable serial console (if needed)
sudo raspi-config
# Interface Options -> Serial Port
# "Would you like a login shell accessible over serial?" -> No
# "Would you like serial port hardware enabled?" -> Yes
```

### I2C/SPI issues:
```bash
# Check if enabled
ls /dev/i2c* /dev/spi*

# Test I2C devices
sudo i2cdetect -y 1
# Should show ADXL345 at address 0x53
```

### Microphone not working:
```bash
# List audio devices
arecord -l

# Test recording
arecord -d 5 test.wav
aplay test.wav
```

### GPIO permissions:
```bash
sudo usermod -a -G gpio,i2c,spi $USER
# Logout and login again
```

## Auto-Start on Boot

Create systemd service:
```bash
sudo nano /etc/systemd/system/safety-system.service
```

Add:
```ini
[Unit]
Description=Advanced Driver Safety System
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/safety-system
ExecStart=/usr/bin/python3 /home/pi/safety-system/advanced_safety_system.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable safety-system.service
sudo systemctl start safety-system.service
```

## Safety Notes

⚠️ **Important Safety Considerations:**
- This system is a safety aid, not a replacement for responsible driving
- Always ensure proper sensor calibration
- Test all features before actual use
- Keep emergency contact updated
- Regularly check sensor functionality
- Ensure stable power supply
- Keep system logs for debugging

## Support

For issues or questions:
1. Check sensor connections
2. Verify GPIO/I2C/SPI are enabled
3. Review system logs: `journalctl -u safety-system.service`
4. Test each sensor individually with calibration scripts
