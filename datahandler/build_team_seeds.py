from uefa.config import COUNTRIES_CSV, COUNTRY_SEEDS_JSON, TEAM_SEEDS_JSON
import json
import pandas as pd

filename = COUNTRY_SEEDS_JSON
df = pd.read_csv(COUNTRIES_CSV, skipinitialspace=True)
with open(filename, "r") as f:
    file = json.load(f)

df_indexed = df.set_index("Club")

dic = {club: file.get(df_indexed.loc[club, "Country"]) for club in df["Club"]}

with open(TEAM_SEEDS_JSON, 'w') as f2:
    json.dump(dic, f2, indent=4, ensure_ascii=False)


