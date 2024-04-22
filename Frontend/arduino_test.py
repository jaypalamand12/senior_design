import streamlit as st
import serial
import time

# Setup serial connection (Adjust the port as necessary)
try:
    ser = serial.Serial('/dev/cu.usbmodem21101', 9600, timeout=1)  # Change '/dev/cu.usbmodem11101' to your Arduino's serial port
    time.sleep(2)  # Wait for the connection to establish
except Exception as e:
    print(e)
    st.error("Error: Unable to connect to Arduino. Check your port.")
    st.stop()

st.title('Button Press and LED Flasher')

# Function to send a command to flash the LED
def flash_led():
    if ser.isOpen():
        ser.write("FLASH\n".encode('utf-8'))  # Send the flash command

# UI to send the flash command
if st.button('Flash LED'):
    flash_led()
    st.success("Flash command sent to Arduino")

# Keep the code for listening to the button press as it was, if needed