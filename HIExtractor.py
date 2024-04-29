import pandas as pd
import numpy as np
import os

class HIExtractor:
    def __init__(self, charge, discharge):
        self.charge = charge
        self.discharge = discharge
    def charge_features(self):
        results = []

        for cycle in self.charge['cycle'].unique():
            cycle_data = self.charge[self.charge['cycle'] == cycle]
            
            # Finding the row where voltage first reaches 4.2V
            cc_end_idx = cycle_data[cycle_data['voltage_measured'] >= 4.2000].index.min()
            
            if pd.notnull(cc_end_idx):
                # Time at which CC ends and CV begins
                cc_end_time = cycle_data.loc[cc_end_idx, 'time']
                
                # CC start is assumed to be at the beginning of the cycle
                cc_start_time = cycle_data['time'].min()
                
                # CV ends at the end of the cycle
                cv_end_time = cycle_data['time'].max()
                
                # Calculating constant current and constant voltage times
                constant_current_time = cc_end_time - cc_start_time
                constant_voltage_time = cv_end_time - cc_end_time
                avg_temp = cycle_data['temperature_measured'].mean()
                
                # Extracting the datetime for the cycle, assuming it's the same for all entries
                time_charge = cycle_data['datetime'].iloc[0]
                
                results.append({
                    'cycle': cycle,
                    'constant_current_time': constant_current_time,
                    'constant_voltage_time': constant_voltage_time,
                    'avg_temp_charge': avg_temp,
                    'time_charge': time_charge  # Adding the datetime to the results
                })

        # Creating a new DataFrame with the results
        results_df = pd.DataFrame(results)
        results_df = self.discharge_features(results_df)
        return results_df

    def discharge_features(self, results_df):

        def moving_average(voltages, window_size):
            # Extend the edges to minimize edge effects
            extended_voltages = np.pad(voltages, (window_size//2, window_size-1-window_size//2), mode='edge')
            return np.convolve(extended_voltages, np.ones(window_size) / window_size, mode='valid')

        cycle_dvd_soh_temp_time = {}  # Dictionary to store cycle, DVD, SOH, average temperature, discharge time, and discharge datetime

        # Iterate over each unique cycle
        for cycle in self.discharge['cycle'].unique():
            # Extract data for the cycle
            cycle_data = self.discharge[self.discharge['cycle'] == cycle]
            
            # Extract voltage measurements, SOH, temperature, time, and datetime for the cycle
            cycle_voltages = cycle_data['voltage_measured']
            cycle_capacity = cycle_data['capacity'].iloc[0]
            cycle_temps = cycle_data['temperature_measured']
            cycle_times = cycle_data['time']
            cycle_datetime = cycle_data['datetime'].iloc[0]

            # Calculate the average temperature during the discharge for the cycle
            average_temp_discharge = cycle_temps.mean()

            # Apply the moving average filter to smooth the voltage data
            smoothed_voltages = moving_average(cycle_voltages.values, window_size=5)
            
            # Calculate the absolute differences between consecutive smoothed readings and sum them
            dvd = np.sum(np.abs(np.diff(smoothed_voltages)))

            # Find the times when the voltage drops through 4.0V and 3.5V
            time_at_4_0 = cycle_times[cycle_voltages[cycle_voltages >= 4.0].index[-1]] if not cycle_voltages[cycle_voltages >= 4.0].empty else np.nan
            time_at_3_5 = cycle_times[cycle_voltages[cycle_voltages <= 3.5].index[0]] if not cycle_voltages[cycle_voltages <= 3.5].empty else np.nan
            
            # Calculate the time to discharge from 4.0V to 3.5V
            time_to_discharge = time_at_3_5 - time_at_4_0 if not np.isnan(time_at_4_0) and not np.isnan(time_at_3_5) else np.nan

            # TVE calculations:
            V_max = np.max(cycle_voltages)
            V_min = np.min(cycle_voltages)
            T_max = np.max(cycle_temps)
            T_min = np.min(cycle_temps)
            VE = (V_max - V_min) / V_max if V_max != 0 else 0
            TE = (T_max - T_min) / T_max if T_max != 0 else 0
            TVE = VE / TE if TE != 0 else 0

            # Store the results
            cycle_dvd_soh_temp_time[cycle] = {
                'DVD': dvd, 
                'Capacity': cycle_capacity, 
                'avg_temp_discharge': average_temp_discharge, 
                'TIEVD': time_to_discharge,
                'TVE': TVE,  # Adding the TVE value
                'time_discharge': cycle_datetime
            }

        # Convert the dictionary to a DataFrame
        dvd_soh_temp_time_df = pd.DataFrame(list(cycle_dvd_soh_temp_time.items()), columns=['cycle', 'data'])
        dvd_soh_temp_time_df = pd.concat([dvd_soh_temp_time_df.drop(['data'], axis=1), dvd_soh_temp_time_df['data'].apply(pd.Series)], axis=1)

        # Merge the calculated DVD, SOH, average temperature, discharge time, TVE, and discharge datetime values with the results DataFrame
        results_df = results_df.merge(dvd_soh_temp_time_df, on='cycle', how='left')

        return results_df

# def impedance_features(impedance, results_df):
#     def find_closest_datetime(target, datetime_series):
#         # Find the closest datetime in the series to the target
#         closest_index = datetime_series.sub(target).abs().idxmin()
#         return closest_index

#     for index, row in results_df.iterrows():
#         # For each row, find the closest datetime in the impedance DataFrame
#         # For time_discharge
#         closest_idx_discharge = find_closest_datetime(row['time_discharge'], impedance['datetime'])
#         # For time_charge
#         closest_idx_charge = find_closest_datetime(row['time_charge'], impedance['datetime'])

#         # Determine which index is closer to the respective time in results_df
#         # And use it to extract the Re, Rct, and datetime values
#         if abs(impedance.iloc[closest_idx_discharge]['datetime'] - row['time_discharge']) <= abs(impedance.iloc[closest_idx_charge]['datetime'] - row['time_charge']):
#             closest_index = closest_idx_discharge
#         else:
#             closest_index = closest_idx_charge

#         # Extract Re and Rct values
#         row['Re'] = impedance.loc[closest_index, 'Re']
#         row['Rct'] = impedance.loc[closest_index, 'Rct']
        
#         # Extract and assign the datetime from the impedance dataframe
#         row['closest_impedance_datetime'] = impedance.loc[closest_index, 'datetime']

#         # Update the results DataFrame
#         results_df.at[index, 'Re'] = row['Re']
#         results_df.at[index, 'Rct'] = row['Rct']
#         results_df.at[index, 'closest_impedance_datetime'] = row['closest_impedance_datetime']

#     return results_df

if __name__ == "__main__":
    # Get the directory of the currently executing script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'Data')
    output_dir = os.path.join(base_dir, 'TransformedData')

    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    for battery in ['B0005', 'B0006', 'B0007', 'B0018']:
        charge_path = os.path.join(data_dir, f'{battery}_charge.csv')
        discharge_path = os.path.join(data_dir, f'{battery}_discharge.csv')

        charge = pd.read_csv(charge_path)
        discharge = pd.read_csv(discharge_path)
        battery_class = HIExtractor(charge, discharge)
        results_df = battery_class.charge_features()

        results_df['time_discharge'] = pd.to_datetime(results_df['time_discharge'])
        results_df['time_charge'] = pd.to_datetime(results_df['time_charge'])

        results_df = results_df.drop(columns=['time_charge', 'time_discharge'])
        results_df.to_csv(f'TransformedData/{battery}_results.csv', index=False)