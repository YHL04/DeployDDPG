import pandas as pd

pd.set_option('display.max_colwidth', 200)
pd.set_option('display.max_rows', 500)
pd.set_option('display.expand_frame_repr', False)

data = pd.read_pickle("data/data.pkl")
print(data.columns.levels[0])
# data = data.dropna(axis=1, how="all")
# data = data.dropna(axis=0, how="any")
# print(data.columns.levels[0])

print(data)
# print("Length: ", data)

