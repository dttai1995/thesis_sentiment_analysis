import pandas as pd

data = pd.read_excel(io="file:/Users/lap01570/Documents/thesis-data.xlsx", sheet_name=0, engine='openpyxl')
print(data.head())