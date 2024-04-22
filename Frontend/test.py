import pandas as pd
import os


df = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0018_charge.csv', index_col=0)

# Filter out the minimum cycle
charge_df = df[df['cycle'] != df['cycle'].min()]

# Adjust the 'cycle' column
charge_df.loc[:, 'cycle'] = charge_df['cycle'] - charge_df['cycle'].min() + 1

# Save the updated dataframe to a new CSV file without the index
charge_df.to_csv('B0018_charge_updated.csv', index=False)

# directory = '/Users/jaypalamand/Senior_Design/csv_data'

# for filename in os.listdir(directory):
#     if filename.endswith("_charge.csv") or filename.endswith("_discharge.csv"):
#         file_path = os.path.join(directory, filename)
#         df = pd.read_csv(file_path)
        
#         # Perform the operation only if 'capacity' column exists
#         if 'capacity' in df.columns:
#             df['SOH'] = df['capacity'] / 2
            
#             df.to_csv(file_path, index=False)  # Save the file back to the same location
