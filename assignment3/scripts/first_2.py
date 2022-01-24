import matplotlib.pyplot as plt
import pandas as pd
import sys

s = sys.argv[0][:-10]
file = s + sys.argv[1] + ".txt"
df = pd.read_csv(file, sep='\t', header=None)
t = df[0];
cwnd = df[1];

fig, ax = plt.subplots()
ax.plot(t, cwnd);
ax.set_xlabel('Time(in seconds)')
ax.set_ylabel('Congestion Window Size')
ax.set_title(sys.argv[1])
fig.savefig(s + sys.argv[1]+'_plot.png')

plt.show()