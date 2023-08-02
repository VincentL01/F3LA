from pathlib import Path
import math
import pandas as pd


from Libs.general import Loader, Time, Events, Area, Distance, Speed, Angle, Speed_A
from Libs.misc import compute_turning_angle, event_extractor, FD_Entropy_Calculator, HullVolumeCalculator, calculate_turning_angle
from . import ALLOWED_DECIMALS

import logging

logger = logging.getLogger(__name__)


class GeneralAnalysis(Loader):
    def __init__(self, project_dir, batch_num, treatment_char, fish_num, params):
        super().__init__(project_dir = project_dir, 
                         batch_num=batch_num, 
                         treatment_char=treatment_char, 
                         fish_num=fish_num,
                         params = params
                         )

        self.TJ_df = self.FISH
        
        # self.BasicCalculation()

    
    def BasicCalculation(self, DEFAULT_INTERVAL = 1):

        if DEFAULT_INTERVAL > self.PARAMS["FRAME RATE"]:
            logger.error(f"User set {DEFAULT_INTERVAL=} but {self.PARAMS['FRAME RATE']=} is smaller than {DEFAULT_INTERVAL=}. Please check the code.")
            raise Exception(f"{self.PARAMS['FRAME RATE']=} is smaller than {DEFAULT_INTERVAL=}. Please check the code.")

        if self.PARAMS["FRAME RATE"] % DEFAULT_INTERVAL != 0:
            logger.error(f"User set {DEFAULT_INTERVAL=} but {self.PARAMS['FRAME RATE']=} is not divisible by {DEFAULT_INTERVAL=}. Please check the code.")
            raise Exception(f"{self.PARAMS['FRAME RATE']=} is not divisible by {DEFAULT_INTERVAL=}. Please check the code.")


        distance_list = []

        for i in range(len(self.TJ_df)-1):
            # Distance = (SQRT((A4-A3)^2+(B4-B3)^2+(D4-D3)^2)/$E$3)
            dist_X = self.TJ_df['X'].iloc[i+1] - self.TJ_df['X'].iloc[i]
            dist_Y = self.TJ_df['Y'].iloc[i+1] - self.TJ_df['Y'].iloc[i]
            dist_Z = self.TJ_df['Z'].iloc[i+1] - self.TJ_df['Z'].iloc[i]

            dist = math.sqrt(dist_X**2 + dist_Y**2 + dist_Z**2)
            dist = dist/self.PARAMS["CONVERSION TV"]

            distance_list.append(dist)
            # UNIT: cm

        self.distance = Distance(distance_list = distance_list)

        #####################################################################################

        SPEED_THRESHOLD = 50
        speed_list = []
        for i in range(len(distance_list)):
            # Speed = Distance/Time
            speed = distance_list[i]/(1/self.PARAMS["FRAME RATE"])
            if speed >= SPEED_THRESHOLD:
                logger.debug(f"Speed of {speed} cm/s detected at frame {i} (index {i+1})")
                # Find the nearest frame with speed < SPEED_THRESHOLD
                for j in range(i-1, 0, -1):
                    if speed_list[j] < SPEED_THRESHOLD:
                        # Replace the speed with the nearest frame
                        speed = speed_list[j]
                        logger.debug(f"Speed replaced with {speed} cm/s at frame {j} (index {j+1})")
                        break
            
            speed_list.append(speed)
            # UNIT: cm/s

        self.speed = Speed(speed_list = speed_list,
                           total_frames=self.TOTAL_FRAMES)

        #####################################################################################

        # We only care about the turning angle of the fish on XY plane
        # We don't care about the turning angle of the fish on Z axis
        # Because the fish is not supposed to turn on Z axis

        turning_angle = TurningAngles(X_coords = self.TJ_df['X'].tolist(),
                                      Y_coords = self.TJ_df['Y'].tolist())
        
        
        self.turning_angle = Angle(angle_class = turning_angle, 
                                   frame_rate=self.PARAMS["FRAME RATE"], 
                                   interval = DEFAULT_INTERVAL)

        #####################################################################################
        
        self.meandering = self.turning_angle.total / self.distance.total * 100

        #####################################################################################

        self.time_in_top = 0
        self.time_in_middle = 0
        self.time_in_bottom = 0

        self.positions = []

        for z_sv in self.TJ_df['Z_SV'].tolist():
            if z_sv < self.PARAMS["UPPER"]:
                self.time_in_top += 1
                self.positions.append("TOP")
            elif z_sv > self.PARAMS["LOWER"]:
                self.time_in_bottom += 1
                self.positions.append("BOT")
            else:
                self.time_in_middle += 1
                self.positions.append("MID")

        self.time_in_top = self.time_in_top / self.TOTAL_FRAMES * 100
        self.time_in_middle = self.time_in_middle / self.TOTAL_FRAMES * 100
        self.time_in_bottom = self.time_in_bottom / self.TOTAL_FRAMES * 100

        try:
            travel_in_TOP_dict = event_extractor(self.positions, "TOP")
            travel_in_TOP_dict = {k: v/self.PARAMS["FRAME RATE"] for k, v in travel_in_TOP_dict.items()}
        except:
            # find unique values in self.positions
            unique_values = list(set(self.positions))
            # count the number of each unique value
            counts = {}
            for value in unique_values:
                counts[value] = self.positions.count(value)

            message = f"self.position does not have 'TOP' value. It has "
            for value, count in counts.items():
                message += f"{value} : {count}; "
            logger.debug(message)

            if len(self.positions) == self.TOTAL_FRAMES:
                travel_in_TOP_dict = {"-1" : -1}
                logger.debug("set travel_in_TOP_dict to {-1}:-1, so that the program can continue.")
            else:
                raise Exception("There were something wrong with the position counting step. Please check the code.")

        self.travel_in_TOP = Events(event_dict = travel_in_TOP_dict, duration=self.PARAMS["DURATION"])

        #####################################################################################

        distance_to_center_list = self.distance_to(TARGET="CENTER")
        self.distance_to_center = Distance(distance_list = distance_to_center_list)

        #####################################################################################

        distance_in_TOP = self.distance_in(distance_list, self.positions, "TOP")
        self.distance_in_TOP = Distance(distance_list = distance_in_TOP)

        #####################################################################################

        self.fractal_dimension, self.entropy = FD_Entropy_Calculator(self.TJ_df)

        #####################################################################################



class TurningAngles():

    def __init__(self, X_coords, Y_coords):

        self.X_coords = X_coords
        self.Y_coords = Y_coords

    def turning_angles(self, interval=1):
        """
        Calculate the turning angles of the fish
        :param interval: the interval between two points
        :return: a list of turning angles
        """
        turning_angles = []

        intervalized_X_coords = self.X_coords[::interval]
        intervalized_Y_coords = self.Y_coords[::interval]

        for i in range(len(intervalized_X_coords) - 2):
            turning_angle = calculate_turning_angle(intervalized_X_coords[i], intervalized_Y_coords[i], intervalized_X_coords[i + 1], intervalized_Y_coords[i + 1], intervalized_X_coords[i + 2], intervalized_Y_coords[i + 2])
            turning_angles.append(turning_angle)

        # for i in range(len(self.X_coords) - 2 * interval):
        #     turning_angle = compute_turning_angle(self.X_coords[i], self.Y_coords[i], self.X_coords[i + interval], self.Y_coords[i + interval], self.X_coords[i + 2 * interval], self.Y_coords[i + 2 * interval])
        #     turning_angles.append(turning_angle)

        return turning_angles
    

# class Fishy:
#     def __init__(self, fishes_coords):
#         # make sure input is a dictionary of dataframes
#         assert isinstance(fishes_coords, dict)
#         for key in fishes_coords:
#             assert isinstance(fishes_coords[key], pd.DataFrame)

#         for fish, coords in fishes_coords.items():
#             setattr(self, fish.replace(" ", "_"), coords)


class ShoalingAnalysis():

    def __init__(self, fishes_coords):

        self.fishes_coords = fishes_coords

        self.shoalingarea = self.CalculateShoalingArea()

        self.shoalingvolume = self.CalculateShoalingVolume()


    def CalculateShoalingArea(self):

        return HullVolumeCalculator(self.fishes_coords, surface = ["X", "Y"])
                                    
    def CalculateShoalingVolume(self):
    
        return HullVolumeCalculator(self.fishes_coords)