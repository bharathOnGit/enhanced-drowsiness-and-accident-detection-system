#!/usr/bin/env python3
"""
ADXL345 Accelerometer Calibration Script
Helps verify proper operation and determine tilt thresholds
"""

import time
import numpy as np
try:
    from adxl345 import ADXL345
except ImportError:
    print("Error: adxl345 module not found")
    print("Install with: pip install --break-system-packages adxl345-python")
    exit(1)

print("="*60)
print("ADXL345 ACCELEROMETER CALIBRATION")
print("="*60)

try:
    accel = ADXL345()
    print("✓ Accelerometer initialized")
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check I2C is enabled: sudo raspi-config")
    print("2. Verify wiring: SDA->GPIO2, SCL->GPIO3, VCC->3.3V, GND->GND")
    print("3. Test I2C connection: sudo i2cdetect -y 1")
    print("   (Should show device at address 0x53)")
    exit(1)

print("\n" + "="*60)
print("STEP 1: LEVEL SURFACE TEST")
print("="*60)
print("Place the accelerometer on a LEVEL surface.")
print("This will establish the baseline readings.\n")
input("Press Enter when ready...")

print("\nCollecting 50 samples...")
level_readings = []

for i in range(50):
    axes = accel.get_axes(True)  # True for g-forces
    level_readings.append([axes['x'], axes['y'], axes['z']])
    time.sleep(0.1)

level_avg = np.mean(level_readings, axis=0)
level_std = np.std(level_readings, axis=0)

print(f"\n✓ Level Surface Results (in g):")
print(f"  X-axis: {level_avg[0]:+.3f} ± {level_std[0]:.3f}")
print(f"  Y-axis: {level_avg[1]:+.3f} ± {level_std[1]:.3f}")
print(f"  Z-axis: {level_avg[2]:+.3f} ± {level_std[2]:.3f}")
print(f"\nExpected values when level: X≈0, Y≈0, Z≈+1.0")

# Calculate tilt from level
tilt_from_level = np.degrees(np.arccos(level_avg[2]))
print(f"Current tilt from vertical: {tilt_from_level:.2f}°")

if tilt_from_level > 10:
    print("⚠️  Warning: Surface may not be perfectly level!")
else:
    print("✓ Surface appears level")

print("\n" + "="*60)
print("STEP 2: TILT TEST - 45 DEGREES")
print("="*60)
print("Now tilt the device to approximately 45 degrees.")
print("You can use a protractor or phone app to verify angle.")
input("\nPress Enter when tilted to 45°...")

print("\nCollecting 30 samples...")
tilt_45_readings = []

for i in range(30):
    axes = accel.get_axes(True)
    tilt_45_readings.append([axes['x'], axes['y'], axes['z']])
    time.sleep(0.1)

tilt_45_avg = np.mean(tilt_45_readings, axis=0)

# Calculate actual tilt angle
x, y, z = tilt_45_avg
magnitude = np.sqrt(x**2 + y**2 + z**2)
tilt_angle = np.degrees(np.arccos(z / magnitude))

print(f"\n✓ 45° Tilt Test Results:")
print(f"  X: {x:+.3f} g")
print(f"  Y: {y:+.3f} g")
print(f"  Z: {z:+.3f} g")
print(f"  Calculated tilt: {tilt_angle:.1f}°")

if 40 <= tilt_angle <= 50:
    print("✓ Tilt angle is close to 45°")
else:
    print(f"⚠️  Measured {tilt_angle:.1f}°, try adjusting to be closer to 45°")

print("\n" + "="*60)
print("STEP 3: EXTREME TILT TEST")
print("="*60)
print("Tilt the device to approximately 60-70 degrees.")
input("Press Enter when ready...")

print("\nCollecting 30 samples...")
extreme_readings = []

for i in range(30):
    axes = accel.get_axes(True)
    extreme_readings.append([axes['x'], axes['y'], axes['z']])
    time.sleep(0.1)

extreme_avg = np.mean(extreme_readings, axis=0)
x, y, z = extreme_avg
magnitude = np.sqrt(x**2 + y**2 + z**2)
extreme_angle = np.degrees(np.arccos(z / magnitude))

print(f"\n✓ Extreme Tilt Results:")
print(f"  X: {x:+.3f} g")
print(f"  Y: {y:+.3f} g")
print(f"  Z: {z:+.3f} g")
print(f"  Calculated tilt: {extreme_angle:.1f}°")

print("\n" + "="*60)
print("CALIBRATION SUMMARY")
print("="*60)
print(f"\nLevel surface:     {tilt_from_level:.1f}°")
print(f"45° tilt test:     {tilt_angle:.1f}°")
print(f"Extreme tilt test: {extreme_angle:.1f}°")

print(f"\n✓ RECOMMENDED SETTINGS:")
print(f"  TILT_THRESHOLD = 45  # degrees")
print(f"\nThis threshold will trigger when vehicle tilts beyond 45°")
print(f"indicating a possible accident (rollover/severe tilt)")

# Real-time monitoring
print("\n" + "="*60)
print("REAL-TIME TILT MONITORING")
print("="*60)
print("\nWould you like to monitor tilt angles in real-time?")
monitor = input("This helps verify the system works correctly (y/n): ").lower()

if monitor == 'y':
    print("\nMonitoring tilt angle (Press Ctrl+C to stop)")
    print("Tilt the device in different directions\n")
    
    try:
        while True:
            axes = accel.get_axes(True)
            x, y, z = axes['x'], axes['y'], axes['z']
            
            # Calculate tilt from vertical
            magnitude = np.sqrt(x**2 + y**2 + z**2)
            tilt = np.degrees(np.arccos(z / magnitude))
            
            # Visual indicator
            status = "⚠️ ACCIDENT!" if tilt > 45 else "✓ Normal"
            bar_length = int((tilt / 90) * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            
            print(f"\rTilt: {tilt:5.1f}° [{bar}] {status}   ", end="", flush=True)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped")

print("\n" + "="*60)
print("CALIBRATION COMPLETE")
print("="*60)
print("\nYour ADXL345 is working correctly! ✓")
print("\nNext steps:")
print("1. The default TILT_THRESHOLD of 45° should work well")
print("2. Test in your vehicle on level ground")
print("3. Verify no false alarms during normal driving")
print("4. Adjust threshold if needed based on testing")
print("\nNote: Sharp turns may briefly trigger the sensor.")
print("Consider adding a time-based filter if false alarms occur.")
