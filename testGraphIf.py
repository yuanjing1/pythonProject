import matplotlib.pyplot as plt
import numpy as np

# Define the function
def f(x):
    return x**2 - 2*x + 1

# Generate x-values
x = np.linspace(-5, 5, 100)

# Calculate y-values
y = f(x)

# Plot the function
plt.plot(x, y)

# Add labels and title
plt.xlabel('x')
plt.ylabel('y')
plt.title('Graph of y = x^2 - 2x + 1')

# Display the plot
plt.show()
