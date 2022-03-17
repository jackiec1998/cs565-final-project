import pandas as pd
import numpy as np
from scipy.stats import expon
import matplotlib.pyplot as plt

# Query
# https://data.stackexchange.com/stackoverflow/query/1568857/hours-between-consecutive-answers

# Read Data
df = pd.read_csv('data.csv')
data = df["Tau"]

# Analyze
print(f"Sample size: {len(data)}")
print(f"Sample mean: {np.mean(data)}")
print(f"Sample median: {np.median(data)}")
