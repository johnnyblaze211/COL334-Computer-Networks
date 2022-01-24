import matplotlib.pyplot as plt
import pandas as pd
import sys

a, c = None, None
if sys.argv[1] == '1':
	a = ['2Mbps', '2Mbps', '2Mbps', '2Mbps', '2Mbps']
	c = ['2Mbps', '4Mbps', '10Mbps', '20Mbps', '50Mbps']
elif sys.argv[1] == '2':
	a = ['0.5Mbps', '1Mbps', '2Mbps', '4Mbps', '10Mbps']
	c = ['6Mbps', '6Mbps', '6Mbps', '6Mbps', '6Mbps']
else:
	print(sys.argv[1])
	sys.exit(1)

for i in range(5):
	file = 'scratch/part'+sys.argv[1]+'_cRate_'+c[i]+'_aRate_'+a[i]+'.txt'
	df = pd.read_csv(file, sep='\t', header=None)
	fig, ax = plt.subplots()
	ax.plot(df[0], df[1])
	ax.set_xlabel('Time(in seconds)')
	ax.set_ylabel('Congestion Window Size')
	ax.set_title(f'Channel Rate: {c[i]}, Application Data Rate: {a[i]}')
	fig.savefig(f'scratch/Q2_part_{sys.argv[1]}_cRate_{c[i]}_aRate_{a[i]}.png')
plt.show()