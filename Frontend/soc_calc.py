import numpy as np
import pandas as pd

# Load the experimental data
# Uncomment the line corresponding to the dataset you wish to use
data_exp = pd.read_csv('/Users/jaypalamand/Senior_Design/model_creation/Experimental_data_fresh_cell.csv')  # fresh cell
# data_exp = pd.read_csv('Experimental_data_aged_cell.csv')  # pre-aged cell

t_exp = data_exp.iloc[:, 0].values
I_exp = data_exp.iloc[:, 1].values
V_exp = data_exp.iloc[:, 2].values

# Define model parameters
C_N = 19.96 * 3600  # Nominal capacity in As. 9Ahr = average of first four half-cycles of the fresh cell.
R = 0.004579  # Internal resistance in Ohm

# Open-circuit voltage V0(SOC): vector with 1001 entries, SOC=0...1 in steps of 0.001.
data = pd.read_csv('/Users/jaypalamand/Senior_Design/model_creation/OCV_vs_SOC_curve.csv')
V0_curve = data.iloc[:, 1].values  # Open-circuit voltage in V

# Initialize result vectors
SOC = np.zeros(len(t_exp))  # Prepare result vector
SOC[0] = 0.5  # Set start SOC to an arbitrary value of 50 %
I_sim = np.zeros(len(t_exp))  # Prepare result vector

# Initialize SOH diagnosis
C_exp = 0
C_sim = 0
SOH = []
t_SOH = []

# Initialize Coulomb counter
SOC_CC = np.zeros(len(t_exp))  # Prepare result vector
SOC_CC[0] = 0

# Loop over all available experimental time steps
for n in range(1, len(t_exp)):

    # SOC diagnosis "simple" model
    delta_t = t_exp[n] - t_exp[n - 1]  # Time step

    # Open-circuit voltage based on linear interpolation
    i = SOC[n - 1] * 1000 + 1
    fi = int(np.floor(i))
    fi = min(max(fi, 1), 1000)  # Ensure fi is within bounds
    V0 = (1 - (i - fi)) * V0_curve[fi - 1] + (i - fi) * V0_curve[fi]

    # Calculate next SOC value
    SOC[n] = SOC[n - 1] - delta_t / (R * C_N) * (V0 - V_exp[n])

    # SOH diagnosis simple model
    I_sim[n] = 1 / R * (V0 - V_exp[n])  # Calculate current from the model
    C_exp += abs(I_exp[n]) * delta_t  # Charge throughput experiment
    C_sim += abs(I_sim[n]) * delta_t  # Charge throughput model
    if C_exp > 2 * C_N:  # Calculate SOH whenever experimental charge throughput is larger than 2 C_N
        SOH.append(C_exp / C_sim)
        t_SOH.append(t_exp[n])
        C_exp = 0
        C_sim = 0

    # Coulomb counter (using a capacity of 19.96 Ah)
    SOC_CC[n] = SOC_CC[n - 1] - delta_t / (19.96 * 3600) * I_exp[n]
    if ((V_exp[n] > 4.19 and abs(I_exp[n]) < 4) or SOC_CC[n] > 1):  # Calibration at upper voltage
        SOC_CC[n] = 1
    elif ((V_exp[n] < 3.01 and abs(I_exp[n]) < 4) or SOC_CC[n] < 0):  # Calibration at lower voltage
        SOC_CC[n] = 0
    if ((V_exp[n] > 4.19 and abs(I_exp[n]) < 4) or SOC[n] > 1):  # Calibration at upper voltage
        SOC[n] = 1
    elif ((V_exp[n] < 3.01 and abs(I_exp[n]) < 4) or SOC[n] < 0):  # Calibration at lower voltage
        SOC[n] = 0


results = {
    'SOC': SOC,
    'I_simulated': I_sim,
    'SOC_CC': SOC_CC
}

results_df = pd.DataFrame(results)

# Concatenate the DataFrames side by side (horizontally)
combined_df = pd.concat([data_exp, results_df], axis=1)
# Save the combined DataFrame to a CSV file
combined_df.to_csv('combined_outputs.csv', index=False)

# Initialize the columns
combined_df['Charge_Discharge'] = 'Charge'  # Default to 'Discharge'; will update below
combined_df['Cycle'] = 0

# Variable to keep track of the cycle count
cycle_count = 0
previous_soc = combined_df['SOC_CC'][0]

# Iterate through the DataFrame to update the 'Charge_Discharge' and 'Cycle' columns
for i in range(1, len(combined_df)):
    current_soc = combined_df['SOC_CC'][i]
    
    # Determine if charging or discharging
    if current_soc > previous_soc:
        combined_df.at[i, 'Charge_Discharge'] = 'Charge'
    elif current_soc < previous_soc:
        combined_df.at[i, 'Charge_Discharge'] = 'Discharge'
    
    # Check for cycle transitions
    if i > 0 and combined_df['Charge_Discharge'][i] != combined_df['Charge_Discharge'][i - 1]:
        cycle_count += 1
    
    combined_df.at[i, 'Cycle'] = cycle_count // 2  # Integer division to count complete cycles
    
    # Update the previous SOC for the next iteration
    previous_soc = current_soc

# Variables for calculating SOH
C_exp_cycle = 0
C_sim_cycle = 0
last_cycle_number = combined_df['Cycle'].max()

# Calculate SOH at the end of each cycle
for cycle_number in range(last_cycle_number + 1):
    cycle_data = combined_df[combined_df['Cycle'] == cycle_number]
    for _, row in cycle_data.iterrows():
        delta_t = row['Time'] - cycle_data.iloc[0]['Time'] if _ > 0 else 0
        C_exp_cycle += abs(row['I_measured']) * delta_t
        C_sim_cycle += abs(row['I_simulated']) * delta_t
    
    # Calculate SOH for the cycle if C_sim_cycle is not zero to avoid division by zero
    if C_sim_cycle > 0:
        soh = C_exp_cycle / C_sim_cycle
        combined_df.loc[combined_df['Cycle'] == cycle_number, 'SOH'] = soh

    # Reset for the next cycle
    C_exp_cycle = 0
    C_sim_cycle = 0

# Fill forward the SOH values to make them constant across each cycle
combined_df['SOH'] = combined_df['SOH'].fillna(method='ffill')

# Save the updated DataFrame to a new CSV file
combined_df.to_csv('combined_outputs_with_cycles_and_soh.csv', index=False)

# Save the updated DataFrame to a new CSV file
combined_df.to_csv('combined_outputs_with_cycles.csv', index=False)
