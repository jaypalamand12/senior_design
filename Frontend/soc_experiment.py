import pandas as pd
import numpy as np

df = pd.read_csv('Frontend/Datasets/B0005/B0005.csv')

t_exp = df['time'].values / 3600  # Convert time to hours

# Initialize SOC_CC
SOC_CC = np.zeros(len(t_exp))
SOC_CC[0] = 1.0  # Starting SOC set to 50%

C_N = 2.00  # Nominal capacity in Ah

current_cycle = df['cycle'][0]
for n in range(1, len(t_exp)):
    if df['cycle'][n] != current_cycle:  # Check if the cycle has changed
        SOC_CC[n] = 1  # Reset SOC_CC to 100% at the start of a new cycle
        current_cycle = df['cycle'][n]
    else:
        C_n = df['capacity'][n]
        delta_t = t_exp[n] - t_exp[n - 1]  # Time difference in hours
        SOC_CC[n] = SOC_CC[n - 1] + delta_t / C_n * df['current_measured'][n]

        # Calibration at upper and lower voltage limits
        if (SOC_CC[n] > 1):
            SOC_CC[n] = 1
        elif (SOC_CC[n] < 0):
            SOC_CC[n] = 0

# Update the DataFrame with the calculated SOC_CC values
df['SOC_CC'] = SOC_CC

# Save the updated DataFrame to a new CSV file
df.to_csv('updated_soc_data_by_cycle.csv', index=False)