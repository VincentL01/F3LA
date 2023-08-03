import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import matplotlib.pyplot as plt
import matplotlib
from tkinter import *
import tkinter as tk
import tkinter.ttk as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from Libs.misc import HullVolumeCalculator

class VolumePlot(tk.Toplevel):
    def __init__(self, volumes, master=None):
        super().__init__(master)
        self.master = master
        self.volumes = volumes

        # Create the Figure and Axis
        self.fig, self.ax = plt.subplots()
        self.ax.plot(volumes, '-b')  # plot the volumes with a blue line

        # Plot the initial position of the 'dot'
        self.dot, = self.ax.plot(0, volumes[0], 'ro')

        # Create the canvas and pack it
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

    def move_dot(self, frame_num):
        # Update the dot's position
        self.dot.set_data(frame_num, self.volumes[frame_num])

        # Redraw the canvas
        self.canvas.draw()


class AnimatedPlot(tk.Toplevel):
    def __init__(self, fishes_coords, 
                 master=None, 
                 limit_dict=None,
                 volume_list=None):
        super().__init__(master)
        self.master = master
        self.fishes_coords = fishes_coords
        self.frame_num = 0
        self.is_paused = False
    
        if limit_dict == None:
            limit_dict = {"X": 700,
                        "Y": 700,
                        "Z": 550
                        }

        self.XLIM = limit_dict["X"]
        self.YLIM = limit_dict["Y"]
        self.ZLIM = limit_dict["Z"]

        # Calculate the maximum length for the slider
        self.max_length = min([len(df) for df in fishes_coords.values()]) - 1

        # Setup an self.animation to store the id of the 'play' function
        self.animation = None

        # Creating play button
        # self.play_button = tk.Button(self, text='Play', command=self.play)
        # self.play_button.pack()
        self.play_button = tk.Button(self, text='Play', command=self.play_pause)
        self.play_button.pack()

         # Creating slider
        self.slider = ttk.Scale(self, 
                                from_=0, 
                                to=self.max_length,
                                length=500, 
                                command=self.on_slider_moved)
        self.slider.pack()

        # Create a label to display the current frame
        self.frame_label = tk.Label(self, text="Frame: 0")
        self.frame_label.pack()


        # Create the VolumePlot
        print("Calculating volume")
        if volume_list == None:
            self.volumes = HullVolumeCalculator(fishes_coords)['ConvexHullVolume'].tolist()
        else:
            self.volumes = volume_list

        self.volume_plot = VolumePlot(self.volumes, master=self)

        print("Done Volume Calculation, start plotting...")


        # Creating plot frame
        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

        # Creating initial plot
        self.plot_current_frame()


    def updater(self):
        self.frame_label['text'] = f"Frame: {self.frame_num}"
        self.volume_plot.move_dot(self.frame_num)


    def destroy(self):
        if self.animation:
            self.after_cancel(self.animation)  # cancel 'play' function
        tk.Toplevel.destroy(self)

    def play_pause(self):
        if self.is_paused:
            self.play()
        else:
            self.pause()

    def play(self):
        self.is_paused = False
        self.play_button.config(text='Pause')
        if not self.is_paused and self.frame_num < self.max_length:
            self.plot_current_frame()
            self.frame_num += 1
            self.slider.set(self.frame_num)
            self.updater()
            self.animation = self.after(10, self.play)  # save 'play' function id
        elif self.frame_num >= self.max_length:
            self.is_paused = True

    def pause(self):
        self.is_paused = True
        self.play_button.config(text='Play')
        if self.animation:
            self.after_cancel(self.animation)


    # def play(self):
    #     self.is_paused = not self.is_paused
    #     if not self.is_paused and self.frame_num < self.max_length:
    #         self.plot_current_frame()
    #         self.frame_num += 1
    #         self.slider.set(self.frame_num)
    #         self.updater()
    #         self.after(10, self.play)  # call 'play' function after 100 ms
    #     elif self.frame_num >= self.max_length:
    #         self.is_paused = True
    #     else:
    #         print("Animation paused")  # Debugging statement
    #         return

    def on_slider_moved(self, value):
        self.is_paused = True
        self.frame_num = int(float(value))
        self.updater()
        self.plot_current_frame()

    def plot_current_frame(self):
        frame = pd.concat([df.iloc[[self.frame_num]][['X', 'Y', 'Z']] for df in self.fishes_coords.values()])

        # Create ConvexHull
        hull = ConvexHull(frame.values)

        if self.frame_num == 0:  # Initial plot
            self.fig.clear()
            self.ax = self.fig.add_subplot(111, projection='3d')
            self.scatter = self.ax.scatter(frame['X'], frame['Y'], frame['Z'])

            # Plot initial hull
            self.hull_lines = []
            for s in hull.simplices:
                s = np.append(s, s[0])  # Here we cycle back to the first coordinate
                line, = self.ax.plot(frame['X'].iloc[s], frame['Y'].iloc[s], frame['Z'].iloc[s], "r-")
                self.hull_lines.append(line)

            # Create 3D blob
            self.hull_polygon = Poly3DCollection(hull.points[hull.simplices], alpha=0.5)
            self.hull_polygon.set_facecolor([0,0,1])
            self.ax.add_collection3d(self.hull_polygon)
        else:  # Update plot
            # Update scatter plot
            self.scatter._offsets3d = (frame['X'].values, frame['Y'].values, frame['Z'].values)

            # Update hull lines
            for s, line in zip(hull.simplices, self.hull_lines):
                s = np.append(s, s[0])
                line.set_data(frame['X'].iloc[s].values, frame['Y'].iloc[s].values)
                line.set_3d_properties(frame['Z'].iloc[s].values)

            # Update 3D blob
            self.hull_polygon.set_verts(hull.points[hull.simplices])

        # Set equal aspect ratio
        self.ax.set_xlim([0, self.XLIM])
        self.ax.set_ylim([0, self.YLIM])
        self.ax.set_zlim([0, self.ZLIM])

        self.canvas.draw()

def StandAlone3DPlot(given_fish_dict, limit_dict=None):
    root = tk.Tk()
    root.withdraw()
    app = AnimatedPlot(given_fish_dict, master=root, limit_dict=limit_dict)
    app.mainloop()


if __name__ == "__main__":
    StandAlone3DPlot()