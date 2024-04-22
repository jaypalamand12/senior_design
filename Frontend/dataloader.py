import streamlit as st
import pandas as pd
from assets import Assets

def load_battery_data(battery_id, mode, cycle):
    base_path = "/Users/jaypalamand/Desktop/Senior_Design/csv_data/"
    # Check if the battery is set to "NA" and return default values
    if st.session_state.get(f'na_{battery_id}', False):
        return {
            "State of charge": "N/A",
            "State of health": "N/A",
            "Temperature": "N/A",
            "Voltage": "N/A",
            "Current supplied": "N/A"
        }
    

    file_name = f"B{str(battery_id).zfill(4)}_{mode}.csv"
    file_path = f"{base_path}{file_name}"
    df = pd.read_csv(file_path)
    df_cycle = df[df['cycle'] == cycle]

    if not df_cycle.empty:
        increment_factor = 30 if mode == "Charge" else 10

        current_index = st.session_state.get(f'index_{battery_id}_{mode}_{cycle}', 0)
        current_index = int(current_index * increment_factor)
        
        if current_index >= len(df_cycle):
            # When current_index exceeds or meets the length of df_cycle, start decreasing the temperature
            current_index = len(df_cycle) - 1
            # Store or update the temperature decrement state
            temp_decrement = st.session_state.get(f'temp_decrement_{battery_id}', 0.7)
            row_data = df_cycle.iloc[current_index].copy()
            new_temperature = row_data['temperature_measured'] - temp_decrement

            # Clamp temperature at minimum 23°C
            if new_temperature < 23:
                row_data['temperature_measured'] = 23
            else:
                row_data['temperature_measured'] = new_temperature
                st.session_state[f'temp_decrement_{battery_id}'] = temp_decrement + 0.7
        else:
            st.session_state[f'index_{battery_id}_{mode}_{cycle}'] = st.session_state.get(f'index_{battery_id}_{mode}_{cycle}', 0) + 1
            row_data = df_cycle.iloc[current_index]

        if mode == "Discharge":
            soc_value = max(row_data['SOC_CC'] * 100, 20)  # Ensuring SOC doesn't fall below 20% in discharge mode
        else:
            soc_value = row_data['SOC_CC'] * 100

        soh_value = min(row_data['SOH'] * 100, 100)

        display_data = {
            "State of charge": f"{soc_value:.3f}%",
            "State of health": f"{soh_value:.3f}%",
            "Temperature": f"{row_data['temperature_measured']:.3f}°C",
            "Voltage": f"{row_data['voltage_measured']:.3f}V",
            "Current supplied": f"{row_data['current_measured']:.3f}A"
        }

        return display_data
    else:
        return {
            "State of charge": "N/A",
            "State of health": "N/A",
            "Temperature": "N/A",
            "Voltage": "N/A",
            "Current supplied": "N/A"
        }
    
def display_battery_data(battery_id, cycle, alert_temp, alert_health):
    mode = st.session_state.battery_states[battery_id]
    battery_data = load_battery_data(battery_id, st.session_state.battery_states[battery_id], cycle)
        

    # Extracting and validating data
    soc = battery_data["State of charge"].replace('%', '')
    soh = battery_data["State of health"].replace('%', '')
    temp = battery_data["Temperature"].replace('°C', '')

    # Check if values are "N/A" before converting
    soc = float(soc) if soc != "N/A" else "N/A"
    soh = float(soh) if soh != "N/A" else "N/A"
    temp = float(temp) if temp != "N/A" else "N/A"

    # Determine readiness to swap based on mode and values
    if mode.upper() == "DISCHARGE" and isinstance(soc, float):
        swap_ready = soc < 30 and isinstance(temp, float) and temp <= 35
    elif mode.upper() == "CHARGE" and isinstance(soc, float) and isinstance(soh, float):
        swap_ready = soc > 75 and soh >= 75 and isinstance(temp, float) and temp <= 35
    else:
        swap_ready = False

    # Determine colors for indicators based on the available data
    swap_ready_color = "green" if swap_ready else "red"
    soh_color = "green" if isinstance(soh, float) and soh >= 75 else "red"

    swap_ready_indicator = f"<span style='color: {swap_ready_color}; font-size: 24px; position: relative; top: 2px;'>●</span>"
    soh_indicator = f"<span style='color: {soh_color}; font-size: 24px; position: relative; top: 2px;'>●</span>"

    swap_mode = st.session_state.swap_states[battery_id]
    if swap_mode.upper() == "CHARGE":
        new_mode = "CHARGING"
    elif swap_mode.upper() == "DISCHARGE":
        new_mode = "IN ROBOT"
    elif swap_mode.upper() == "DOCKED":
        new_mode = "DOCKED"
    elif swap_mode.upper() == "EJECTED":
        new_mode = "EJECTED"
    else:
        new_mode = "ERROR"
    
    indicators = f"Battery {battery_id} ({new_mode}): <span style='margin-left: 20px;'>{swap_ready_indicator} Ready to Swap</span><span style='margin-left: 10px;'>{soh_indicator} Health</span>"
    st.markdown(indicators, unsafe_allow_html=True)

    with st.expander("View Battery Data",expanded=False):
        for key, value in battery_data.items():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.text(f"{key}:")
            with col2:
                st.text(f"{value}")
    if isinstance(soh, float) and soh < 75:
        if not st.session_state.get(f'alerted_{battery_id}', False):
            with alert_health.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(Assets.lowhealth, width=50)
                with col2:
                    st.markdown(f"<div style='margin-bottom: -2px;'><b>Battery {battery_id}</b></div>", unsafe_allow_html=True)
                    st.markdown("Health below 75%, replace battery", unsafe_allow_html=True)
            st.session_state[f'alerted_{battery_id}'] = True
        else:
            with alert_health.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(Assets.lowhealth, width=50)
                with col2:
                    st.markdown(f"<div style='margin-bottom: -2px;'><b>Battery {battery_id}</b></div>", unsafe_allow_html=True)
                    st.markdown("Health below 75%, replace battery", unsafe_allow_html=True)
    if isinstance(temp, float) and temp > 35:
        if not st.session_state.get(f'alerted_temp_{battery_id}', False):
            with alert_temp.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(Assets.hightemp, width=50)
                with col2:
                    st.markdown(f"<div style='margin-bottom: -2px;'><b>Battery {battery_id}</b></div>", unsafe_allow_html=True)
                    st.markdown("Temperature above critical level", unsafe_allow_html=True)
            st.session_state[f'alerted_temp_{battery_id}'] = True
    else:
        if st.session_state.get(f'alerted_temp_{battery_id}', False):
            with alert_temp.container():
                alert_temp.empty()
            st.session_state[f'alerted_temp_{battery_id}'] = False