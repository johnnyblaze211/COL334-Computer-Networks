import matplotlib.pyplot as plt
import pandas as pd
import sys

s = sys.argv[0][:-10]
config = sys.argv[1]
df_N1_sock1 = pd.read_csv(s+'Q3_N1_sock1_config'+config+'.txt', sep = '\t', header = None)
df_N1_sock2 = pd.read_csv(s+'Q3_N1_sock2_config'+config+'.txt', sep = '\t', header = None)
df_N2_sock1 = pd.read_csv(s+'Q3_N2_sock1_config'+config+'.txt', sep = '\t', header = None)

fig1, ax1 = plt.subplots()
fig2, ax2 = plt.subplots()
fig3, ax3 = plt.subplots()

ax1.set_xlabel('Time(in seconds)')
ax2.set_xlabel('Time(in seconds)')
ax3.set_xlabel('Time(in seconds)')

ax1.set_ylabel('Congestion Window Size')
ax2.set_ylabel('Congestion Window Size')
ax3.set_ylabel('Congestion Window Size')

ax1.set_title('Plot for connection 1, configuration ' + str(config))
ax2.set_title('Plot for connection 2, configuration ' + str(config))
ax3.set_title('Plot for connection 3, configuration ' + str(config))

ax1.plot(df_N1_sock1[0], df_N1_sock1[1])
ax2.plot(df_N1_sock2[0], df_N1_sock2[1])
ax3.plot(df_N2_sock1[0], df_N2_sock1[1])

fig1.savefig(s+'Q3_N1_sock1_config_'+config+'.png')
fig2.savefig(s+'Q3_N1_sock2_config_'+config+'.png')
fig3.savefig(s+'Q3_N2_sock1_config_'+config+'.png')

plt.show()




