import streamlit as st
from dataloader import load_battery_data
import time

class Swap:
    def prepare_for_swap(self):
        print("\nInitial battery states, charge, and health before swapping:")
        st.session_state['discharging_battery'] = None
        st.session_state['candidate_battery'] = None
        highest_combined_value = -1

        for battery_id, state in st.session_state.battery_states.items():
            cycle_key = f'cycle_{battery_id}'
            cycle_count = st.session_state.get(cycle_key, 1)
            battery_data = load_battery_data(battery_id, state, cycle_count)
            soc = battery_data.get("State of charge", "N/A")
            soh = battery_data.get("State of health", "N/A")
            if state == "Discharge":
                st.session_state['discharging_battery'] = battery_id
            elif state == "Charge":
                soc = float(soc.replace('%', ''))
                soh = float(soh.replace('%', ''))
                combined_value = soc + soh
                if soc >= 75 and soh >= 75 and combined_value > highest_combined_value:
                    highest_combined_value = combined_value
                    st.session_state['candidate_battery'] = battery_id
        st.session_state.swap_states[st.session_state['discharging_battery']] = "Docked"
        print('cool')
        self.set_robot_battery_na()

    def set_robot_battery_na(self):
        if 'discharging_battery' in st.session_state:
            battery_id = st.session_state['discharging_battery']
            st.session_state.battery_states[battery_id] = "NA"
            # Set a flag indicating that this battery should not load data
            st.session_state[f'na_{battery_id}'] = True
            st.session_state['unplugged'] = True
            st.session_state['docked'] = False
            st.session_state.swap_states[battery_id] = "EJECTED"
            self.start_charging_robot_battery()

    def start_charging_robot_battery(self):
        if 'discharging_battery' in st.session_state:
            battery_id = st.session_state['discharging_battery']
            # Change the state from "NA" to "Charge"
            st.session_state.battery_states[battery_id] = "Charge"
            # Reset the NA flag since the battery is now charging
            if f'na_{battery_id}' in st.session_state:
                del st.session_state[f'na_{battery_id}']
            st.session_state.swap_states[battery_id] = "charge"
            self.set_swapping_battery_na()

    def set_swapping_battery_na(self):
        if 'candidate_battery' in st.session_state:
            battery_id = st.session_state['candidate_battery']
            st.session_state.battery_states[battery_id] = "NA"
            # Similarly, set a flag for the swapping battery
            st.session_state[f'na_{battery_id}'] = True
            st.session_state.swap_states[battery_id] = "EJECTED"
            self.execute_swap()

    def execute_swap(self):
        if 'discharging_battery' in st.session_state and 'candidate_battery' in st.session_state:
            discharging_battery = st.session_state['discharging_battery']
            candidate_battery = st.session_state['candidate_battery']

            # Execute the swap in battery states
            st.session_state.battery_states[discharging_battery] = "Charge"
            st.session_state.swap_states[discharging_battery] = "Charge"
            st.session_state.battery_states[candidate_battery] = "Discharge"
            st.session_state.swap_states[candidate_battery] = "Discharge"

            # Log the swap for history
            swap_reason = f"{discharging_battery} --> {candidate_battery}"
            st.session_state.swap_history.append(swap_reason)
            st.session_state[f'swap_count_{discharging_battery}'] = st.session_state.get(f'swap_count_{discharging_battery}', 0) + 1
            st.session_state[f'swap_count_{candidate_battery}'] = st.session_state.get(f'swap_count_{candidate_battery}', 0) + 1

            # Set completion flags for tracking state
            st.session_state['discharge_complete_{discharging_battery}'] = True
            st.session_state['charge_complete_{candidate_battery}'] = True

            # Reset NA flags to allow data loading
            if f'na_{discharging_battery}' in st.session_state:
                del st.session_state[f'na_{discharging_battery}']
            if f'na_{candidate_battery}' in st.session_state:
                del st.session_state[f'na_{candidate_battery}']

            # Increment the cycle index based on the swap count
            if st.session_state[f'swap_count_{discharging_battery}'] % 2 == 0:
                cycle_key = f'cycle_{discharging_battery}'
                st.session_state[cycle_key] = st.session_state.get(cycle_key, 1) + 1

            if st.session_state[f'swap_count_{candidate_battery}'] % 2 == 0:
                cycle_key = f'cycle_{candidate_battery}'
                st.session_state[cycle_key] = st.session_state.get(cycle_key, 1) + 1
            st.session_state['swap'] = False
            time.sleep(55)
            st.rerun()