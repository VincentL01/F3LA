import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk
from tkinter import ttk


def plot_fish_movement(ax, set1, set2, theta, tank_x_size=None, tank_y_size=None, tank_z_size=None):
    x1, y1 = set1
    x_mirrored, y_mirrored = set2

    z2 = y_mirrored * np.sin(np.radians(theta)) / (2 * np.sin(np.radians(90 - theta)))
    x2 = x_mirrored - z2 * np.tan(np.radians(theta))

    x = np.concatenate((x1, x2))
    y = np.concatenate((y1, y1))
    z = np.concatenate((np.zeros_like(z2), z2))

    if tank_x_size is None:
        tank_x_size = max(x) - min(x)
    if tank_y_size is None:
        tank_y_size = max(y) - min(y)
    if tank_z_size is None:
        tank_z_size = max(z) - min(z)

    ax.clear()
    ax.plot(x, y, z)

    ax.set_xlim(0, tank_x_size)
    ax.set_ylim(0, tank_y_size)
    ax.set_zlim(0, tank_z_size)

    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.set_zlabel('Z-axis')

def update_plot(val):
    theta = float(val)
    plot_fish_movement(ax, set1, set2, theta)
    canvas.draw()

def program_quit():
    root.quit()
    root.destroy()

# Example data

# Create random value for x_list with 50 values
x_list = np.random.randint(0, 400, 30)
# Create random value for y_list with 50 values
y_list = np.random.randint(0, 400, 30)
# Create random value for z_list with 50 values
z_list = np.random.randint(0, 400, 30)

set1 = (x_list, y_list)
set2 = (x_list, z_list)

# Create the main window
root = tk.Tk()
root.title("Fish Movement")

# Create the 3D plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Create a canvas for the plot and add it to the main window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Create a slider widget to control the theta value
slider = ttk.Scale(root, from_=0, to=90, orient=tk.HORIZONTAL, command=update_plot)
slider.set(45)  # Set initial value
slider.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

# quit button
quit_button = tk.Button(root, text="Quit", command=program_quit)
quit_button.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

# Initialize the plot with the initial theta value
plot_fish_movement(ax, set1, set2, 45)

# Start the main event loop
root.mainloop()