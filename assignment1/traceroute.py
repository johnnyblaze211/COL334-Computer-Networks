import sys
import os
import logging
from datetime import datetime
logging.getLogger('scapy.runtime').setLevel(logging.ERROR)
from scapy.all import *
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


#print("hello")
if(len(sys.argv) != 2):
	print("usage: \n\tpython3 traceroute.py <domain-name>")
	sys.exit(1)

addr = sys.argv[1]

output = []

hops = 64

br = False

for i in range(hops):
	print(f"hop {i+1}:")
	output.append([])
	for j in range(3):
		pkt = IP(dst = addr, ttl = i)/ICMP()
		res = sr1(pkt, verbose = 0, timeout = 2)
		if(res == None):
			output[i].append(('*', ''))

		else:
			rtt = res.time - pkt.sent_time
			output[i].append((rtt * 1000, res.src))
			if(i>4 and output[i][j][1] == output[i-1][j][1] and output[i][j][1] == output[i-2][j][1]):
				br = True

		if(str(output[i][j][0]) == '*'):
			print(f'ping {j}: *')
		else:
			print(f'ping {j}: {round(output[i][j][0], 2)}ms {output[i][j][1]}')
	if(br == True):
		break
	print('\n')


x = [i+1 for i in range(len(output))]
y = []
clr = []
for out in output:
	total = 0
	c = 0
	for j in range(3):
		if(str(out[j][0]) == '*'):
			continue
		else:
			c+=1
			total+=out[j][0]
	if(c != 0):
		y.append(total/c)
		clr.append('blue')
	else:
		y.append(0)
		clr.append('red')


plt.scatter(x,y, color = clr, zorder = 2)
plt.plot(x,y, zorder = 1)
plt.title(f'RTT vs no. of hops for traceroute to {addr}')
plt.xlabel('hop number')
plt.ylabel('RTT(in milliseconds)')
legend_elements = [Line2D([0], [0], marker = 'o', label = 'Response Received', markerfacecolor = 'b', markersize = '6'),
Line2D([0], [0], marker = 'o', label = 'No Response Received', markerfacecolor = 'r', markersize = '6')]
plt.legend(handles = legend_elements, loc = 'best')

plt.savefig('plot.jpg')
plt.show()





#print(output)
