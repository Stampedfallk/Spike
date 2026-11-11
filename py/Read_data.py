'''
-------------------------------------------------------------------------------
-- Title      : Read data
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : Read_data.py
-- Author     : Jere Nissinen
-- Edited     : 11.11.2026
-------------------------------------------------------------------------------
-- Description: Python script for reading data from the fpga through com-port.
-------------------------------------------------------------------------------
'''
import serial
import struct
import time

# SETTINGS: Change the COM-gate to match your own port
SERIAL_PORT = 'COM5' 
BAUD_RATE = 115200

def main():
    print(f"Opening connection to port {SERIAL_PORT}...")
    try:
        # Opening the serial gate
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
            print("Connection established, waiting for sensor data...\n")
            
            # Clear the possible old values from buffer
            ser.reset_input_buffer()
            
            while True:
                # Wait that there are atleast 7 bytes in the buffer
                if ser.in_waiting >= 7:
                    # Read exactly 7 bytes
                    raw_data = ser.read(7)

                    # Unpack bytes back to original variables.
                    # 'B' = 8-bit unsigned char (1 byte)
                    # 'H' = 16-bit unsigned short (2 bytes)
                    # '>' = big-endian
                    light, temperature, humidity, moisture = struct.unpack('>BHHH', raw_data)
                    
                    # Print data
                    print(f"--- Sensor data [{time.strftime('%X')}] ---")
                    print(f" Moisture:    {moisture}")
                    print(f" Humidity: {humidity * 100 / 65536}")
                    print(f" Light:       {light}")
                    print(f" Temperature: {temperature * 165 / 65536 - 40} C")
                    print("-" * 30 + "\n")
                    
                time.sleep(0.1)
                
    except serial.SerialException:
        print(f"Error: gate {SERIAL_PORT} not found or already in use")
    except KeyboardInterrupt:
        print("\nProgram closed by the user.")

if __name__ == '__main__':
    main()
