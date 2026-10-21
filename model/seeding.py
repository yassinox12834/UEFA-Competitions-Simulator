import numpy as np
import pandas as pd
import math

formula1 = lambda P, mP : 1500 + 100 * (math.log(P + 1) - math.log(mP + 1))

formula2 = lambda P, mP : 1500 + 100 * (np.log(P + 1) - np.log(mP + 1))


