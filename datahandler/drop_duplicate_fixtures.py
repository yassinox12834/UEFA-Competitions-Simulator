from uefa.config import PROCESSED_DIR
import pandas as pd

link = PROCESSED_DIR / "fixtures_updated.csv"

df = pd.read_csv(link)

df_propre = df.drop_duplicates(subset=['fixture_id'], keep='first')

df_propre.to_csv(PROCESSED_DIR / "fixtures_without.csv", index=False)
