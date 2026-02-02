#!/usr/bin/env python3
"""
GPS NEO-6M Test and Verification Script
Tests GPS module and displays location data
"""

import serial
import time

# Configuration
GPS_SERIAL_PORT = "/dev/ttyAMA0"  # or /dev/serial0
GPS_BAUDRATE = 9600

print("="*60)
print("GPS NEO-6M MODULE TEST")
print("="*60)

print("\nAttempting to connect to GPS module...")
print(f"Port: {GPS_SERIAL_PORT}")
print(f"Baudrate: {GPS_BAUDRATE}")

try:
    gps = serial.Serial(GPS_SERIAL_PORT, GPS_BAUDRATE, timeout=1)
    print("✓ GPS serial connection established")
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check serial port is enabled: sudo raspi-config")
    print("   Interface Options -> Serial Port")
    print("   - Disable serial console")
    print("   - Enable serial hardware")
    print("\n2. Try alternative port:")
    print("   - /dev/ttyAMA0")
    print("   - /dev/serial0")
    print("   - /dev/ttyS0")
    print("\n3. Verify wiring:")
    print("   GPS TX -> Pi RX (GPIO 15)")
    print("   GPS RX -> Pi TX (GPIO 14)")
    print("   GPS VCC -> 5V")
    print("   GPS GND -> GND")
    print("\n4. Check GPS has power (LED should blink)")
    exit(1)

print("\n" + "="*60)
print("READING RAW GPS DATA")
print("="*60)
print("\nNote: GPS may take 30-60 seconds to get a fix.")
print("Ensure GPS has clear view of the sky.\n")
print("Press Ctrl+C to stop\n")

def parse_gpgga(sentence):
    """Parse GPGGA sentence for location data"""
    try:
        parts = sentence.split(',')
        if len(parts) < 10:
            return None
        
        # Check if we have valid data
        if not parts[2] or not parts[4]:
            return None
        
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
        
        # GPS quality
        quality = parts[6]
        satellites = parts[7]
        altitude = parts[9] if len(parts) > 9 else "N/A"
        
        return {
            'lat': lat,
            'lon': lon,
            'quality': quality,
            'satellites': satellites,
            'altitude': altitude
        }
    except:
        return None

fix_acquired = False
valid_data_count = 0

try:
    while True:
        line = gps.readline().decode('ascii', errors='replace').strip()
        
        if line:
            # Show raw sentences (limited output)
            if line.startswith('$'):
                print(f"Raw: {line[:60]}...")
            
            # Parse GPGGA (Global Positioning System Fix Data)
            if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                data = parse_gpgga(line)
                
                if data:
                    valid_data_count += 1
                    
                    if not fix_acquired:
                        print("\n" + "="*60)
                        print("✓ GPS FIX ACQUIRED!")
                        print("="*60)
                        fix_acquired = True
                    
                    quality_map = {
                        '0': 'No fix',
                        '1': 'GPS fix',
                        '2': 'DGPS fix',
                        '3': 'PPS fix',
                        '4': 'RTK fix',
                        '5': 'Float RTK',
                        '6': 'Estimated',
                    }
                    
                    quality_str = quality_map.get(data['quality'], 'Unknown')
                    
                    print(f"\n--- GPS Data (Reading #{valid_data_count}) ---")
                    print(f"Latitude:    {data['lat']:.6f}°")
                    print(f"Longitude:   {data['lon']:.6f}°")
                    print(f"Quality:     {quality_str}")
                    print(f"Satellites:  {data['satellites']}")
                    print(f"Altitude:    {data['altitude']} m")
                    print(f"\nGoogle Maps: https://www.google.com/maps?q={data['lat']},{data['lon']}")
                    print("-" * 60)
                else:
                    if not fix_acquired:
                        print("Waiting for GPS fix... (ensure clear sky view)")
        
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n\n" + "="*60)
    print("GPS TEST SUMMARY")
    print("="*60)
    
    if valid_data_count > 0:
        print(f"✓ GPS module is working!")
        print(f"✓ Received {valid_data_count} valid location readings")
        print("\nYour GPS module is ready for use in the safety system.")
    else:
        print("⚠️  No valid GPS data received")
        print("\nPossible issues:")
        print("1. GPS needs clear view of sky")
        print("2. First fix can take 30-60 seconds (cold start)")
        print("3. Indoor locations may not work")
        print("4. Check antenna connection")
        print("\nTry testing outdoors with clear sky view.")
    
    gps.close()
    print("\n✓ GPS connection closed")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
