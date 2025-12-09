import pandas as pd

df = pd.read_csv('data/raw/final_training_dataset_v2.csv', nrows=5)
print('Columns:')
for col in df.columns:
    print(f'  - {col}')
print(f'\nShape: {df.shape}')
print(f'\nFirst row:')
print(df.iloc[0])
