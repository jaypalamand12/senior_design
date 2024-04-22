import streamlit as st
from dataclasses import dataclass
import pandas as pd
import numpy as np
import time
from threading import Thread, Lock
import serial
from assets import Assets

# Initialize Streamlit app
st.title("Battery Status Dashboard")


if 'battery_states' not in st.session_state:
    st.session_state.battery_states = {"0005": "Discharge", "0007": "Charge", "0018": "Charge"}

def load_battery_data(battery_id, mode, cycle):
    file_name = f"B{str(battery_id).zfill(4)}_{mode}.csv"
    file_path = f"{Assets.file_path}{file_name}"
    df = pd.read_csv(file_path)
    df_cycle = df[df['cycle'] == cycle]

    if not df_cycle.empty:
        current_index = st.session_state.get(f'index_{battery_id}_{mode}_{cycle}', 0) * (30 if mode == "Charge" else 10)
        
        if current_index >= len(df_cycle):
            current_index = len(df_cycle) - 1
        else:
            st.session_state[f'index_{battery_id}_{mode}_{cycle}'] = st.session_state.get(f'index_{battery_id}_{mode}_{cycle}', 0) + 1

        row_data = df_cycle.iloc[current_index]

        display_data = {
            "Temperature": f"{row_data['temperature_measured']:.3f}°C",
            "State of charge": f"{row_data['SOC_CC'] * 100:.3f}%",
            "State of health": f"{row_data['SOH'] * 100:.3f}%",
            "Voltage": f"{row_data['voltage_measured']:.3f}V",
            "Current supplied": f"{row_data['current_measured']:.3f}A",
            "Time": f"{row_data['time']:.3f}s"
        }

        return display_data
    else:
        return {
            "Temperature": "N/A",
            "State of charge": "N/A",
            "State of health": "N/A",
            "Voltage": "N/A",
            "Current supplied": "N/A"
        }

def swap_battery_states():
    print("\nInitial battery states, charge, and health before swapping:")
    for battery_id, state in st.session_state.battery_states.items():
        cycle_key = f'cycle_{battery_id}'
        cycle_count = st.session_state.get(cycle_key, 1)
        battery_data = load_battery_data(battery_id, state, cycle_count)
        soc = battery_data.get("State of charge", "N/A")
        soh = battery_data.get("State of health", "N/A")
        print(f"Battery {battery_id}: State - {state}, Cycle Count - {cycle_count}, SOC - {soc}, SOH - {soh}")

    discharging_battery = next((b for b, v in st.session_state.battery_states.items() if v == "Discharge"), None)
    candidate_battery = None
    highest_combined_value = -1

    for battery_id, state in st.session_state.battery_states.items():
        if state == "Charge":
            cycle_key = f'cycle_{battery_id}'
            cycle_count = st.session_state.get(cycle_key, 1)
            battery_data = load_battery_data(battery_id, state, cycle_count)
            soc = float(battery_data.get("State of charge", "N/A").replace('%', ''))
            soh = float(battery_data.get("State of health", "N/A").replace('%', ''))

            if soc >= 75 and soh >= 75:
                combined_value = soc + soh
                if combined_value > highest_combined_value:
                    highest_combined_value = combined_value
                    candidate_battery = battery_id

    if discharging_battery and candidate_battery:
        st.session_state.battery_states[discharging_battery] = "Charge"
        st.session_state.battery_states[candidate_battery] = "Discharge"

        swap_reason = f"{discharging_battery} --> {candidate_battery}"
        st.session_state.swap_history.append(swap_reason)

        discharge_complete_flag = f'discharge_complete_{discharging_battery}'
        if st.session_state.get(discharge_complete_flag, False):
            cycle_key = f'cycle_{discharging_battery}'
            st.session_state[cycle_key] += 1
            st.session_state[discharge_complete_flag] = False  # Reset the flag

        st.session_state[f'charge_complete_{discharging_battery}'] = True

        charge_complete_flag = f'charge_complete_{candidate_battery}'
        if st.session_state.get(charge_complete_flag, False):
            cycle_key = f'cycle_{candidate_battery}'
            st.session_state[cycle_key] += 1
            st.session_state[charge_complete_flag] = False  # Reset the flag

        st.session_state[f'discharge_complete_{candidate_battery}'] = True