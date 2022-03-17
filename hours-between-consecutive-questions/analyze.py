import pandas as pd
import numpy as np
from scipy.stats import expon
import matplotlib.pyplot as plt

# Query
# https://data.stackexchange.com/stackoverflow/query/1568830/hours-between-consecutive-posts

# Read Data
df = pd.read_csv('data.csv')
data = df["Tau"]

# Analyze
print(f"Sample size: {len(data)}")
print(f"Sample mean: {np.mean(data)}")
print(f"Sample median: {np.median(data)}")

# Plot
fig, ax = plt.subplots()
ax.set(xlim=(0, np.max(data)), ylim=(0, 1))

# Histogram
bin_width = 168
num_bins = int(np.ceil(np.max(data) / bin_width))
bins = np.linspace(0, bin_width * num_bins, num_bins + 1)
hist,_ = np.histogram(data, bins)
hist = hist / len(data)

ax.bar(bins[:-1] + bin_width / 2, hist, width=0.9 * bin_width, label="pdf")

# Cumulative 
ax.plot(sorted(data), np.linspace(0, 1, len(data)), "r", label="cdf")

# Est. Parameters
params = expon.fit(data)
print(params)

ax.plot(bins[1:], expon.cdf(bins[1:], *params), ":r", label="cdf^")

plt.legend(loc='upper left')
plt.show()