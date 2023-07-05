import pandas as pd
from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

# def update(num, frames, plot):
#     # Clear current plot
#     plot.clear()
    
#     # Create ConvexHull
#     hull = ConvexHull(frames[num][['X', 'Y', 'Z']].values)
    
#     # Plot points
#     plot.scatter(frames[num]['X'], frames[num]['Y'], frames[num]['Z'])
    
#     # Plot hull
#     for s in hull.simplices:
#         s = np.append(s, s[0])  # Here we cycle back to the first coordinate
#         plot.plot(frames[num]['X'].iloc[s], frames[num]['Y'].iloc[s], frames[num]['Z'].iloc[s], "r-")

def update(num, frames, plot):
    # Clear current plot
    plot.clear()
    
    # Create ConvexHull
    hull = ConvexHull(frames[num][['X', 'Y', 'Z']].values)
    
    # Plot points
    plot.scatter(frames[num]['X'], frames[num]['Y'], frames[num]['Z'])
    
    # create Poly3DCollection of the hull
    hull_polygon = Poly3DCollection(hull.points[hull.simplices], alpha=0.5)
    hull_polygon.set_facecolor([0,0,1])
    plot.add_collection3d(hull_polygon)

    # make axis params same
    plot.auto_scale_xyz([0, 1], [0, 1], [0, 1])

def plot_convex_hull(fishes_coords, surface):
    assert 2 <= len(surface) <= 3, "Surface must have 2 or 3 dimensions"
    
    # Get frames
    num_frames = list(fishes_coords.values())[0].shape[0]
    frames = [pd.concat([df.iloc[[frame]][surface] for df in fishes_coords.values()]) for frame in range(num_frames)]
    
    # Create plot
    if len(surface) == 3:
        fig = plt.figure()
        plot = fig.add_subplot(111, projection='3d')
    else:
        fig, plot = plt.subplots()

    ani = animation.FuncAnimation(fig, update, frames=range(num_frames), fargs=(frames, plot))

    # Save animation
    ani.save('convex_hull_animation.mp4', writer=animation.FFMpegWriter())
