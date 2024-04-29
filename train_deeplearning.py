import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Flatten



import os

# Dynamic path determination
base_dir = os.path.dirname(__file__)
model_dir = os.path.join(base_dir, 'DeepLearningModels')
os.makedirs(model_dir, exist_ok=True)

df1 = pd.read_csv('/Users/jaypalamand/Desktop/ME597/TransformedData/B0005_results.csv')
df2 = pd.read_csv('/Users/jaypalamand/Desktop/ME597/TransformedData/B0006_results.csv')
df3 = pd.read_csv('/Users/jaypalamand/Desktop/ME597/TransformedData/B0007_results.csv')
df4 = pd.read_csv('/Users/jaypalamand/Desktop/ME597/TransformedData/B0018_results.csv')

def normalize_dataframe(df):
    scaler = StandardScaler()
    features = df.drop(['Capacity'], axis=1)
    df_normalized = pd.DataFrame(scaler.fit_transform(features), columns=features.columns)
    df_normalized['Capacity'] = df['Capacity'].values  # Keeping Capacity in the last column
    return df_normalized

# Normalize each DataFrame
df1_normalized = normalize_dataframe(df1)
df2_normalized = normalize_dataframe(df2)
df3_normalized = normalize_dataframe(df3)
df4_normalized = normalize_dataframe(df4)

def create_sequences(df, sequence_length):
    sequences = []
    labels = []
    for i in range(len(df) - sequence_length):
        seq = df.iloc[i:i+sequence_length, :-1].values  # Exclude the last column (Capacity)
        label = df.iloc[i+sequence_length, -1]  # Last column value (Capacity) of the last row of the sequence
        sequences.append(seq)
        labels.append(label)
    return np.array(sequences), np.array(labels)

sequence_length = 10  # Example sequence length
X_train_1, y_train_1 = create_sequences(df2_normalized, sequence_length)
X_train_2, y_train_2 = create_sequences(df4_normalized, sequence_length)

# Training Data: Use B0006 and B0018
X_train = np.concatenate((X_train_1, X_train_2), axis=0)
y_train = np.concatenate((y_train_1, y_train_2), axis=0)

# Validation Data: Use B0007
X_val, y_val = create_sequences(df3_normalized, sequence_length)

# Testing Data: Use B0005
X_test, y_test = create_sequences(df1_normalized, sequence_length)

# TensorFlow requires the labels to be of a certain shape for the Sequential API
y_train = y_train.reshape(-1, 1)
y_val = y_val.reshape(-1, 1)
y_test = y_test.reshape(-1, 1)

# Create TensorFlow Dataset objects for training, validation, and testing
train_dataset = tf.data.Dataset.from_tensor_slices((X_train, y_train)).batch(64).shuffle(buffer_size=len(X_train))
val_dataset = tf.data.Dataset.from_tensor_slices((X_val, y_val)).batch(64)
test_dataset = tf.data.Dataset.from_tensor_slices((X_test, y_test)).batch(64)

learning_rate = 0.009
lstm_units = 128
dropout_rate = 0.1

model1 = Sequential([
    LSTM(lstm_units, input_shape=(X_train.shape[1], X_train.shape[2])),
    Dropout(dropout_rate),  # Adding dropout to combat overfitting
    Dense(1)
])

adam_optimizer = Adam(learning_rate=learning_rate)
model1.compile(optimizer=adam_optimizer, loss='mse', metrics=['mae'])


# Summary of the model to see its architecture
model1.summary()

history1 = model1.fit(
    train_dataset,
    epochs=100,
    validation_data=val_dataset
)

model1_path = os.path.join(model_dir, 'LSTM_model.h5')
model1.save(model1_path)

model2 = Sequential([
    Flatten(input_shape=(X_train.shape[1], X_train.shape[2])),
    Dense(256, activation='relu'),
    Dropout(dropout_rate),
    Dense(1)
])
model2.compile(optimizer=Adam(learning_rate=learning_rate), loss='mse', metrics=['mae'])
model2.summary()

history2 = model2.fit(
    train_dataset,
    epochs=100,
    validation_data=val_dataset
)

model2_path = os.path.join(model_dir, 'ANN_model.h5')
model2.save(model2_path)
