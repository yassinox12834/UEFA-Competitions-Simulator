from uefa.config import PROCESSED_DIR
import numpy as np
import pandas as pd

link = PROCESSED_DIR / "fixtures.csv"
df = pd.read_csv(link)

# 1. Create a conditional array for all rows
# If the round is 'Final', set to True. Otherwise, set to an empty string ''.
neutral_values = np.where(df["round"] == "Final", True, "")

# 2. Insert 'neutral_venue' right between 'away_team' and 'home_goals' (index 12)
# This populates the entire column automatically based on the rule above
df.insert(loc=12, column="neutral_venue", value=neutral_values)

# 3. Save the modified DataFrame
output_filename = PROCESSED_DIR / "fixtures_updated.csv"
df.to_csv(output_filename, index=False)

print(f"Success! Scaled to all rows and saved as: {output_filename}")
