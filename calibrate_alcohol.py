#!/usr/bin/env python3
"""
Alcohol Sensor (MQ Series) Calibration Script
Helps determine the appropriate threshold value for your sensor
"""

from gpiozero import MCP3008
import time
import statistics

ALCOHOL_SENSOR_CHANNEL = 0  # MCP3008 channel
SAMPLES = 100
SAMPLE_DELAY = 0.1  # seconds

print("="*60)
print("ALCOHOL SENSOR CALIBRATION")
print("="*60)
print("\nThis script will help you calibrate your MQ alcohol sensor.")
print("We'll take readings in different conditions to find the right threshold.\n")

try:
    alcohol_sensor = MCP3008(channel=ALCOHOL_SENSOR_CHANNEL)
    print("✓ Sensor initialized on MCP3008 channel", ALCOHOL_SENSOR_CHANNEL)
except Exception as e:
    print(f"✗ Error initializing sensor: {e}")
    print("\nTroubleshooting:")
    print("1. Check SPI is enabled: sudo raspi-config")
    print("2. Verify wiring connections")
    print("3. Ensure MCP3008 is properly powered")
    exit(1)

print("\n" + "="*60)
print("STEP 1: CLEAN AIR BASELINE")
print("="*60)
print("Ensure there is NO alcohol in the environment.")
input("Press Enter when ready...")

clean_air_readings = []
print(f"\nCollecting {SAMPLES} samples...")

for i in range(SAMPLES):
    value = alcohol_sensor.value * 1024  # Convert to ADC value (0-1023)
    clean_air_readings.append(value)
    if (i + 1) % 10 == 0:
        print(f"  Sample {i+1}/{SAMPLES}: {value:.1f}")
    time.sleep(SAMPLE_DELAY)

clean_air_avg = statistics.mean(clean_air_readings)
clean_air_std = statistics.stdev(clean_air_readings)

print(f"\n✓ Clean Air Results:")
print(f"  Average: {clean_air_avg:.2f}")
print(f"  Std Dev: {clean_air_std:.2f}")
print(f"  Min: {min(clean_air_readings):.2f}")
print(f"  Max: {max(clean_air_readings):.2f}")

print("\n" + "="*60)
print("STEP 2: ALCOHOL PRESENCE TEST")
print("="*60)
print("Now expose the sensor to alcohol vapor.")
print("You can use:")
print("  - Hand sanitizer (spray near sensor)")
print("  - Rubbing alcohol on cotton ball")
print("  - Alcoholic beverage vapor")
print("\nWARNING: Do NOT expose sensor to open flame!")
input("\nPress Enter when alcohol vapor is present...")

alcohol_readings = []
print(f"\nCollecting {SAMPLES} samples with alcohol present...")

for i in range(SAMPLES):
    value = alcohol_sensor.value * 1024
    alcohol_readings.append(value)
    if (i + 1) % 10 == 0:
        print(f"  Sample {i+1}/{SAMPLES}: {value:.1f}")
    time.sleep(SAMPLE_DELAY)

alcohol_avg = statistics.mean(alcohol_readings)
alcohol_std = statistics.stdev(alcohol_readings)

print(f"\n✓ Alcohol Present Results:")
print(f"  Average: {alcohol_avg:.2f}")
print(f"  Std Dev: {alcohol_std:.2f}")
print(f"  Min: {min(alcohol_readings):.2f}")
print(f"  Max: {max(alcohol_readings):.2f}")

print("\n" + "="*60)
print("CALIBRATION RESULTS")
print("="*60)

difference = alcohol_avg - clean_air_avg
percentage_increase = (difference / clean_air_avg) * 100

print(f"\nClean Air Average:    {clean_air_avg:.2f}")
print(f"Alcohol Average:      {alcohol_avg:.2f}")
print(f"Difference:           {difference:.2f}")
print(f"Percentage Increase:  {percentage_increase:.1f}%")

# Calculate recommended threshold
# Set threshold at 50% between clean air and alcohol reading
recommended_threshold = clean_air_avg + (difference * 0.5)

print(f"\n✓ RECOMMENDED THRESHOLD: {recommended_threshold:.0f}")
print(f"\nUpdate your script with:")
print(f"  ALCOHOL_THRESHOLD = {recommended_threshold:.0f}")

# Conservative and aggressive alternatives
conservative = clean_air_avg + (difference * 0.3)
aggressive = clean_air_avg + (difference * 0.7)

print(f"\nAlternative thresholds:")
print(f"  Conservative (fewer false alarms): {conservative:.0f}")
print(f"  Aggressive (more sensitive):       {aggressive:.0f}")

# Real-time monitoring option
print("\n" + "="*60)
print("REAL-TIME MONITORING")
print("="*60)
print("\nWould you like to monitor the sensor in real-time?")
monitor = input("This will help verify your threshold (y/n): ").lower()

if monitor == 'y':
    print(f"\nMonitoring sensor (threshold: {recommended_threshold:.0f})")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            value = alcohol_sensor.value * 1024
            status = "ALCOHOL!" if value > recommended_threshold else "Clean"
            bar_length = int((value / 1024) * 50)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            
            print(f"\rValue: {value:6.1f} [{bar}] {status}   ", end="", flush=True)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped")

print("\n" + "="*60)
print("CALIBRATION COMPLETE")
print("="*60)
print("\nNext steps:")
print("1. Open advanced_safety_system.py")
print(f"2. Set ALCOHOL_THRESHOLD = {recommended_threshold:.0f}")
print("3. Test the system with actual alcohol exposure")
print("4. Fine-tune if needed based on real-world performance")
print("\nStay safe! 🚗")
