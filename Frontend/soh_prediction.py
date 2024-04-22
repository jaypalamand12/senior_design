import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.io import loadmat
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from math import sqrt
import pickle

class BatteryPredictor:
    def __init__(self, battery):
        self.battery = battery
        self.df = None
        self.load_data()

    def load_data(self):
        mat = loadmat(f'Frontend/Datasets/mat/' + self.battery + '.mat')
        dataset = []
        capacity_data = []
        for i in range(len(mat[self.battery][0, 0]['cycle'][0])):
            row = mat[self.battery][0, 0]['cycle'][0][i]
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
                    dataset.append([
                        i + 1,  # cycle number
                        ambient_temperature,
                        date_time,
                        capacity,
                        data[0][0]['Voltage_measured'][0][j],
                        data[0][0]['Current_measured'][0][j],
                        data[0][0]['Temperature_measured'][0][j],
                        data[0][0]['Current_load'][0][j],
                        data[0][0]['Voltage_load'][0][j],
                        data[0][0]['Time'][0][j]
                    ])
                capacity_data.append([i + 1, ambient_temperature, date_time, capacity])
        dataset_df = pd.DataFrame(data=dataset, columns=['cycle', 'ambient_temperature', 'datetime', 'capacity',
                                                        'voltage_measured', 'current_measured', 'temperature_measured',
                                                        'current_load', 'voltage_load', 'time'])
        self.save_csv(dataset_df, self.battery)
        self.df = dataset_df
    
    def save_csv(self, df, name):
        df.to_csv(f'Frontend/Datasets/{self.battery}/{name}.csv', index=False)

    def save_predictions(self, y_test, y_pred):
        y_test_df = pd.DataFrame(y_test).reset_index(drop=True)

        # Convert y_pred to a DataFrame
        y_pred_df = pd.DataFrame(y_pred, columns=['Predicted Capacity'])

        # Concatenate the two DataFrames along the columns
        results_df = pd.concat([y_test_df, y_pred_df], axis=1)

        # You can rename the columns of y_test_df if needed, for example:
        results_df.columns = ['Actual Capacity', 'Predicted Capacity']

        results_df.to_csv(f'Frontend/Datasets/{self.battery}/soh_pred.csv', index=False)

    def train(self):
        features = ['cycle', 'ambient_temperature', 'voltage_measured']
        if self.df is not None and not self.df.empty:
            X = self.df[features]
            nominal_capacity = self.df['capacity'].max()
            self.df['SoH'] = (self.df['capacity'] / nominal_capacity) * 100

            y = self.df['SoH']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            regressor = RandomForestRegressor(n_estimators=100, random_state=42)
            print(f'\nTraining {self.battery}....\n')
            regressor.fit(X_train, y_train)

            y_pred = regressor.predict(X_test)

            # Evaluating the model
            print('Evaluating Model....\n')
            rms = sqrt(mean_squared_error(y_test, y_pred))
            print('Root Mean Square Error:', rms)

            self.save_predictions(y_test, y_pred)
            with open(f'models/{self.battery}.pkl', 'wb') as file:
                pickle.dump(regressor, file)
        
