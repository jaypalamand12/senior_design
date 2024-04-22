from soh_prediction import BatteryPredictor
from typing import Dict
import pandas as pd
import pickle
import numpy as np
import time

def train(battery_list):
    for battery in battery_list:
        battery_predictor = BatteryPredictor(battery)
        battery_predictor.train()

class Battery:

    def __init__(self, name, cycle, temp, voltage):
        self.name = name
        self.cycle = cycle
        self.temp = temp
        self.voltage = voltage
         

    def predict_soh(self):
        with open(f'/Users/jaypalamand/Senior_Design/models/{self.name}.pkl', 'rb') as file:
            model = pickle.load(file)

        data = {
            'cycle': [self.cycle],
            'ambient_temperature': [self.temp],
            'voltage_measured': [self.voltage],
        }

        input_data = pd.DataFrame(data)
        soh_prediction = model.predict(input_data)

        return soh_prediction


if __name__ == "__main__":
    user_input = input("\nWould you like to train the model? (yes/no): ").strip().lower()
    train_flag = user_input == "yes"

    battery_list = ['B0005', 'B0006', 'B0007', 'B0018']

    if train_flag:
        train(battery_list)

    user_input2 = input("\nWould you like to simulate a battery swap (yes/no): ").strip().lower()
    test_flag = user_input2 == "yes"

    if test_flag:

        print("\nBattery B0005 has docked")

        time.sleep(2)

        robot_battery = 'B0005'

        # Name, Cycles, Temperature, Voltage
        b0005 = Battery('B0005', 2, 25, 2.20)

        b0006 = Battery('B0006', 400, 122, 4.20)
        b0007 = Battery('B0007', 400, 122, 4.20)
        b0018 = Battery('B0018', 400, 122, 4.20)

        battery_obj_list = [b0006, b0007, b0018]
        soh_pred_dict: Dict[str, float] = {}
        soc_dict: Dict[str, float] = {}

        for battery_obj in battery_obj_list:
            soh_pred_dict[battery_obj.name] = battery_obj.predict_soh()
            soc_percentage = (battery_obj.voltage / 4.2) * 100
            soc_dict[battery_obj.name] = soc_percentage
        
        combined_scores = {name: soh_pred_dict[name] + soc_dict[name] for name in soh_pred_dict.keys()}
        optimal_battery_key = max(combined_scores, key=lambda k: combined_scores[k])

        optimal_battery_value = optimal_battery_key

        # Print table headers
        print(f"\n{'Battery':<8} {'SoH (%)':<8} {'SoC (%)':<8}")

        # Print a separator
        print('-' * 26)

        for battery in sorted(soh_pred_dict.keys()):
            soh_value = soh_pred_dict[battery]
            soc_value = soc_dict[battery]
            
            # Check and convert to scalar if the values are lists or arrays
            if isinstance(soh_value, (list, np.ndarray)):
                soh_value = soh_value[0]
            if isinstance(soc_value, (list, np.ndarray)):
                soc_value = soc_value[0]

            print(f"{battery:<8} {soh_value:<8.2f} {soc_value:<8.2f}")


        print(f'\nBattery \'B0005\' has been swapped with Battery \'{optimal_battery_value}\'\n')


