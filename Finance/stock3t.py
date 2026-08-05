import numpy as np
import matplotlib.pyplot as plt

def experiment():
    money = 100000
    for i in range(0, 1000):
        earning = np.random.choice([100, -50], 1, p=[0.6, 0.4])
        money = money * earning
    return money

data = []
for i in range(0, 200):
    datapoint = experiment()
    data.append(datapoint)
plt.plot(np.array(data))
plt.hlines(np.array(data).mean(), 0, 200, color='red')
plt.show()
