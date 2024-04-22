import datetime
import pandas as pd
from scipy.io import loadmat
from pandas import DataFrame
from sqlalchemy import create_engine
import numpy as np

def disch_data(battery):
  mat = loadmat(f'/Users/jaypalamand/Senior_Design/Frontend/Datasets/mat/{battery}.mat') 
  print('Total data in dataset: ', len(mat[battery][0, 0]['cycle'][0]))
  c = 0
  disdataset = []
  capacity_data = []
  
  for i in range(len(mat[battery][0, 0]['cycle'][0])):
    row = mat[battery][0, 0]['cycle'][0, i]
    if row['type'][0] == 'discharge':
      ambient_temperature = row['ambient_temperature'][0][0] 
      date_time = datetime.datetime(int(row['time'][0][0]),
                               int(row['time'][0][1]),
                               int(row['time'][0][2]),
                               int(row['time'][0][3]),
                               int(row['time'][0][4])) + datetime.timedelta(seconds=int(row['time'][0][5]))
      data = row['data']
      capacity = data[0][0]['Capacity'][0][0]
      for j in range(len(data[0][0]['Voltage_measured'][0])):
        voltage_measured = data[0][0]['Voltage_measured'][0][j]
        current_measured = data[0][0]['Current_measured'][0][j]
        temperature_measured = data[0][0]['Temperature_measured'][0][j]
        current_load = data[0][0]['Current_load'][0][j]
        voltage_load = data[0][0]['Voltage_load'][0][j]
        time = data[0][0]['Time'][0][j]
        disdataset.append([c + 1, ambient_temperature, date_time, capacity,
                        voltage_measured, current_measured,
                        temperature_measured, current_load,
                        voltage_load, time])
        capacity_data.append([c + 1, ambient_temperature, date_time, capacity])
      c = c + 1
  return pd.DataFrame(data=disdataset,
                       columns=['cycle', 'ambient_temperature', 'datetime',
                                'capacity', 'voltage_measured',
                                'current_measured', 'temperature_measured',
                                'current_load', 'voltage_load', 'time'])

def charge_data(battery):
  mat = loadmat(f'/Users/jaypalamand/Senior_Design/Frontend/Datasets/mat/{battery}.mat')
  c = 0
  chdataset = []
  for i in range(len(mat[battery][0, 0]['cycle'][0])):
    row = mat[battery][0, 0]['cycle'][0, i]
    if row['type'][0] == 'charge' :
            
      ambient_temperature = row['ambient_temperature'][0][0]
      date_time = datetime.datetime(int(row['time'][0][0]),
                               int(row['time'][0][1]),
                               int(row['time'][0][2]),
                               int(row['time'][0][3]),
                               int(row['time'][0][4])) + datetime.timedelta(seconds=int(row['time'][0][5]))
      data = row['data']
      for j in range(len(data[0][0]['Voltage_measured'][0])):
        voltage_measured = data[0][0]['Voltage_measured'][0][j]
        current_measured = data[0][0]['Current_measured'][0][j]
        temperature_measured = data[0][0]['Temperature_measured'][0][j]
        current_charge = data[0][0]['Current_charge'][0][j]
        voltage_charge = data[0][0]['Voltage_charge'][0][j]
        time = data[0][0]['Time'][0][j]
        chdataset.append([c + 1, ambient_temperature, date_time,
                        voltage_measured, current_measured,
                        temperature_measured, current_charge,
                        voltage_charge, time])
      c = c + 1
  return pd.DataFrame(data=chdataset,columns=['cycle', 'ambient_temperature', 'datetime', 
                                'voltage_measured','current_measured',
                                'temperature_measured','current',
                                'voltage', 'time'])


def impedance_data(battery):
    mat = loadmat(f'/Users/jaypalamand/Senior_Design/Frontend/Datasets/mat/{battery}.mat')
    c = 0
    impdataset = []
    
    for i in range(len(mat[battery][0, 0]['cycle'][0])):
        row = mat[battery][0, 0]['cycle'][0, i]
        if row['type'][0] == 'impedance':
            ambient_temperature = row['ambient_temperature'][0][0]
            date_time = datetime.datetime(int(row['time'][0][0]),
                                          int(row['time'][0][1]),
                                          int(row['time'][0][2]),
                                          int(row['time'][0][3]),
                                          int(row['time'][0][4])) + datetime.timedelta(seconds=int(row['time'][0][5]))
            data = row['data']
            for j in range(len(data[0][0]['Battery_impedance'][0])):
                sense_current = data[0][0]['Sense_current'][0][j]
                battery_current = data[0][0]['Battery_current'][0][j]
                battery_impedance = data[0][0]['Battery_impedance'][0][j]
                rectified_impedance = data[0][0]['Rectified_Impedance'][0][j]
                re = data[0][0]['Re'][0][j]
                rct = data[0][0]['Rct'][0][j]
                impdataset.append([c + 1, ambient_temperature, date_time,
                                   sense_current, battery_current, battery_impedance,
                                   rectified_impedance, re, rct])
            c += 1

    return pd.DataFrame(data=impdataset,
                        columns=['cycle', 'ambient_temperature', 'datetime',
                                 'sense_current', 'battery_current', 'battery_impedance',
                                 'rectified_impedance', 'Re', 'Rct'])


def calc_soc(charge_method, df):
  t_exp = df['time'].values / 3600  # Convert time to hours

  # Initialize SOC_CC
  SOC_CC = np.zeros(len(t_exp))

  SOC_CC[0] = 1.0 if charge_method == 'discharge' else 0

  C_N = 2.00  # Nominal capacity in Ah

  current_cycle = df['cycle'][0]
  for n in range(1, len(t_exp)):
      if df['cycle'][n] != current_cycle:  # Check if the cycle has changed
          
          SOC_CC[n] = 1 if charge_method == 'discharge' else 0
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

  df['SOC_CC'] = SOC_CC
  return df

def main():
   battery_list = ["B0005", "B0006", "B0007", "B0018"]
   for battery in battery_list:
      df = charge_data(battery)
      df2 = disch_data(battery)
      df3 = impedance_data(battery)
      capacity_dict = df2.drop_duplicates('cycle').set_index('cycle')['capacity'].to_dict()
      max_cycle = max(capacity_dict.keys())
      df['capacity'] = df['cycle'].apply(lambda x: capacity_dict[min(x, max_cycle)])
      df = calc_soc('charge', df)
      df2 = calc_soc('discharge', df2)
      df.to_csv(f'/Users/jaypalamand/Senior_Design/csv_data/{battery}_charge.csv')
      df2.to_csv(f'/Users/jaypalamand/Senior_Design/csv_data/{battery}_discharge.csv')
      df3.to_csv(f'/Users/jaypalamand/Senior_Design/csv_data/{battery}_impedance.csv')

if __name__ == '__main__':
  main()
  charge_df1 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0005_charge.csv')
  discharge_df1 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0005_discharge.csv')
  impedance_df1 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0005_impedance.csv')
  charge_df2 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0006_charge.csv')
  discharge_df2 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0006_discharge.csv')
  impedance_df2 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0006_impedance.csv')
  charge_df3 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0007_charge.csv')
  discharge_df3 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0007_discharge.csv')
  impedance_df3 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0007_impedance.csv')
  charge_df4 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0018_charge.csv')
  discharge_df4 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0018_discharge.csv')
  impedance_df4 = pd.read_csv('/Users/jaypalamand/Senior_Design/csv_data/B0018_impedance.csv')

  engine = create_engine('sqlite:///battery_data.db')
  connection = engine.raw_connection()

  batteries = {
      'B0005': {
          'charge': charge_df1,
          'discharge': discharge_df1,
          'impedance': impedance_df1
      },
      'B0006': {
          'charge': charge_df2,
          'discharge': discharge_df2,
          'impedance': impedance_df2
      },
      'B0007': {
          'charge': charge_df3,
          'discharge': discharge_df3,
          'impedance': impedance_df3
      },
      'B0018': {
          'charge': charge_df4,
          'discharge': discharge_df4,
          'impedance': impedance_df4
      },
  }

  for battery_id, tables in batteries.items():
      for table_name, df in tables.items():
          full_table_name = f"{battery_id}_{table_name}"
          df.to_sql(full_table_name, connection, if_exists='replace', index=False)


