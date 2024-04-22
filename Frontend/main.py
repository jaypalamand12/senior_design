import streamlit as st
from assets import Assets
from dataloader import display_battery_data
from swap import Swap
import serial
import time
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
import logging



try:
    ser = serial.Serial('/dev/cu.usbmodem21401', 9600, timeout=1)
    time.sleep(2)  # Wait for the connection to establish
except Exception as e:
    print(e)
    st.error("Error: Unable to connect to Arduino. Check your port.")
    st.stop()

if 'battery_states' not in st.session_state:
    st.session_state.battery_states = {"0001": "Discharge", "0002": "Charge", "0003": "Charge"}
if 'pending_update' not in st.session_state:
    st.session_state.pending_update = False
if 'batteries_to_update' not in st.session_state:
    st.session_state.batteries_to_update = []
if 'swap_history' not in st.session_state:
    st.session_state.swap_history = []
if 'swap_states' not in st.session_state: 
    st.session_state.swap_states = {"0001": "Discharge", "0002": "Charge", "0003": "Charge"}
if 'swap' not in st.session_state:
     st.session_state.swap = False


def listen_for_commands(ser):  
    while True:
        try:
            if ser.inWaiting() > 0:
                command = ser.readline().decode('utf-8').rstrip()
                if command:
                    st.session_state['swap'] = True
                    st.rerun()
            time.sleep(0.1)  # Add a small delay to reduce CPU usage
        except serial.SerialException as e:
            logging.error(f"Serial connection issue: {str(e)}")
            # Optionally, you can add code here to perform non-intrusive recovery or logging
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
              # If an unexpected error occurs, break out of the loop



def start_listening():
    try:
        ser = serial.Serial('/dev/cu.usbmodem21401', 9600, timeout=1)
        time.sleep(2)  # Wait for the connection to establish
        listening_thread = threading.Thread(target=listen_for_commands, args=(ser,))
        ctx = get_script_run_ctx()
        add_script_run_ctx(listening_thread)
        listening_thread.start()
        st.session_state['listening_thread'] = listening_thread
    except Exception as e:
        print(e)
        st.error("Error: Unable to connect to Arduino. Check your port.")
        st.stop()

st.title("Battery Status Dashboard")


with st.sidebar:
    st.header("Battery Settings")

    st.markdown("### Alerts", unsafe_allow_html=True)
    alert_temp1 = st.empty()
    alert_temp2 = st.empty()
    alert_temp3 = st.empty()
    alert_health1 = st.empty()
    alert_health2 = st.empty()
    alert_health3 = st.empty()

    st.markdown("### Battery Cycles")
    cycle_b1 = st.number_input("Select Cycle Number:", min_value=1, value=st.session_state.get('cycle_0001', 1), step=1, key="cycle_b1")
    st.session_state['cycle_0001'] = cycle_b1
    
    cycle_b3 = st.number_input("Select Cycle Number:", min_value=1, value=st.session_state.get('cycle_0002', 1), step=1, key="cycle_b3")
    st.session_state['cycle_0002'] = cycle_b3

    cycle_b2 = st.number_input("Select Cycle Number:", min_value=1, value=st.session_state.get('cycle_0003', 1), step=1, key="cycle_b2")
    st.session_state['cycle_0003'] = cycle_b2

    start_listening()

    st.subheader("Swap History")
    if st.session_state.get('swap_history', []):
        for history_item in st.session_state.swap_history:
            st.text(history_item)
    if st.session_state['swap']:
        Swap().prepare_for_swap()

battery_data_placeholder = st.empty()  # The placeholder for battery data

for _ in range(200):
    with battery_data_placeholder.container():
        display_battery_data("0001", cycle_b1, alert_temp1, alert_health1)
        display_battery_data("0002", cycle_b3, alert_temp2, alert_health2)
        display_battery_data("0003", cycle_b2, alert_temp3, alert_health3)

