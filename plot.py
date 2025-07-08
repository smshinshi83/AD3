import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

fig, ax = plt.subplots()

df = pd.read_csv("1e-07_data.csv")
df = df[(df["Time[s]"]>5.9e-6)&(df["Time[s]"]<6.4e-6)]
data = df.to_numpy()

ax.plot(data[:,0], data[:,1])
ax.grid()

ax.set_xlabel("Time[s]")
ax.set_ylabel("Voltage[V]")

fig.savefig("1e-07_plot.png")