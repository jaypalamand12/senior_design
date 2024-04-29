import os
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error


# Dynamic path determination
base_dir = os.path.dirname(__file__)
data_dir = os.path.join(base_dir, 'TransformedData')
model_dir = os.path.join(base_dir, 'SklearnModels')
os.makedirs(model_dir, exist_ok=True)

# Reading data
df1 = pd.read_csv(os.path.join(data_dir, 'B0006_results.csv'))
df2 = pd.read_csv(os.path.join(data_dir, 'B0018_results.csv'))
concatenated_df = pd.concat([df1, df2])
concatenated_df.reset_index(drop=True, inplace=True)

def load_and_prepare_data(df):
    features = df[['cycle', 'constant_current_time', 'constant_voltage_time', 'DVD', 'avg_temp_discharge', 'TIEVD', 'TVE']]
    target = df['Capacity']
    return features, target

X_full, y_full = load_and_prepare_data(concatenated_df)

# Scaling features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_full)

# Model definition
models = {
    'Decision Tree': DecisionTreeRegressor(),
    'Linear Regression': LinearRegression(),
    'Random Forest': RandomForestRegressor(),
    'Gradient Boosting': GradientBoostingRegressor(),
    'SVR': SVR()
}

param_grids = {
    'Decision Tree': {'max_depth': [None, 10, 20, 30]},
    'Linear Regression': {},
    'Random Forest': {'n_estimators': [100, 200, 300], 'max_depth': [None, 10, 20]},
    'Gradient Boosting': {'n_estimators': [100, 200, 300], 'learning_rate': [0.01, 0.1, 0.5]},
    'SVR': {'C': [1, 10, 100], 'gamma': [0.1, 1, 10]}
}
best_models = {}

for name, model in models.items():
    grid_search = GridSearchCV(model, param_grids[name], cv=5, scoring='neg_mean_squared_error', n_jobs=-1)
    grid_search.fit(X_scaled, y_full)
    best_models[name] = grid_search.best_estimator_
    filename = f"{name.replace(' ', '_').lower()}.pkl"
    model_path = os.path.join(model_dir, filename)
    
    with open(model_path, 'wb') as f:
        pickle.dump(grid_search.best_estimator_, f)


test_df = pd.read_csv(os.path.join(data_dir, 'B0005_results.csv'))
X_new, y_new = load_and_prepare_data(test_df)
X_new_scaled = scaler.transform(X_new)

plt.figure(figsize=(10, 6))
plt.scatter(y_new, y_new, color='k', label='Actual')

for name, best_model in best_models.items():
    predictions = best_model.predict(X_new_scaled)
    plt.scatter(y_new, predictions, label=name)

plt.xlabel('Actual Capacity')
plt.ylabel('Predicted Capacity')
plt.title('Predicted vs Actual Capacities for Different Models after Hyperparameter Tuning')
plt.legend()
plt.grid(True)
plt.show()


# Initialize lists to store error statistics
mse_list = []
rmse_list = []
mae_list = []

# Calculate error statistics for each best model
for name, best_model in best_models.items():  # Iterate over the best models
    predictions = best_model.predict(X_new_scaled)
    mse = mean_squared_error(y_new, predictions)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_new, predictions)
    mse_list.append(mse)
    rmse_list.append(rmse)
    mae_list.append(mae)

# Create a dataframe to display error statistics
error_df = pd.DataFrame({
    'Model': list(best_models.keys()),  # Use the best models dictionary keys
    'MSE': mse_list,
    'RMSE': rmse_list,
    'MAE': mae_list
})

print("Error Statistics:")
print(error_df)