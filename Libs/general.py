import pandas as pd
import numpy as np
import os
import time
import math
from pathlib import Path
import json
from statistics import mean
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import linear_sum_assignment
from scipy.stats import pearsonr, spearmanr, kendalltau
# from dcor import distance_correlation
# from minepy import MINE

from Libs.misc import *
from Libs.XtendedCorrel import hoeffding

from . import ALLOWED_DECIMALS, TEMPLATE_PATH, FISH_KEY_FORMAT, SAVED_TRAJECTORY_FORMAT, CHARS, NEG_INF, POS_INF

import logging

logger = logging.getLogger(__name__)


##################################### CALCULATE PARAMETERS FROM ESSENTIAL COORDS #####################################

class ParamsCalculator():

    def __init__(self, project_dir=None, batch_num=1, treatment_char="A"):

        logger.info("ParamsCalculator() initiated.")
        
        if project_dir == None:
            self.project_dir = TEMPLATE_PATH
            logger.warning("No project directory specified. Using template directory instead.")
        else:
            self.project_dir = project_dir

        self.static_dir = get_static_dir(self.project_dir, batch_num, treatment_char)

        self.user_annotation_path = self.static_dir / "essential_coords.json"
        self.output_path = self.static_dir / "parameters.json"

        self.user_inputs = self.load_user_input()

        self.output_params = self.loadexisted_output()

        self.calculation()

        self.save_params()

    def load_user_input(self):

        logger.debug("Loading user-input coordinates...")

        raw = self.load_raw()
        polished_user_inputs = self.polisher(raw)

        return polished_user_inputs
    
    def load_raw(self):

        logger.debug("Loading raw user-input coordinates...")

        try:
            with open(self.user_annotation_path, 'r') as file:
                data = file.read()
        except FileNotFoundError:
            logger.error("File of User-input coordinates not found. Please check the path or run Measurer() before hand.")
            raise FileNotFoundError
        
        return json.loads(data)
    
    # {
    #  'A': {'pixel': [[45, 291], [518, 290]], 'real': 20.0},
    #  'B': {'pixel': [[270, 42], [271, 510]], 'real': 20.0},
    #  'C': {'pixel': [[624, 41], [624, 526]], 'real': 20.0},
    #  'D': {'pixel': [[626, 182], [990, 183]], 'real': 0.0}
    # }
    
    def polisher(self, input_dict):

        logger.debug("Polishing user-input coordinates...")

        vertical_lines = ['B', 'C']
        horizontal_lines = ['A', 'D']

        output_dict = input_dict.copy()

        for line in input_dict.keys():
            if line in vertical_lines:
                up_point, down_point = self.coord_recog(input_dict[line]['pixel'], reg_type = "ud").values()
                down_point[0] = up_point[0]
                output_dict[line]['pixel'] = {
                    "start": up_point,
                    "end": down_point,
                    "distance": abs(up_point[1] - down_point[1]),
                    "center": [up_point[0], (up_point[1] + down_point[1]) / 2]
                }
            elif line in horizontal_lines:
                left_point, right_point = self.coord_recog(input_dict[line]['pixel'], reg_type = "lr").values()
                right_point[1] = left_point[1]
                output_dict[line]['pixel'] = {
                    "start": left_point,
                    "end": right_point,
                    "distance": abs(left_point[0] - right_point[0]),
                    "center": [(left_point[0] + right_point[0]) / 2, left_point[1]]
                }

        return output_dict

    
    def coord_recog(self, coord_list, reg_type = "lr"):

        logger.debug("Reorganizing coordinates...")

        assert reg_type in ["lr", "ud"], "reg_type must be either 'lr' or 'ud'"
        output_dict = {}
        if reg_type == "lr":
            if coord_list[0][0] < coord_list[-1][0]:
                output_dict["Left"] = coord_list[0]
                output_dict["Right"] = coord_list[-1] 
            else:
                output_dict["Left"] = coord_list[-1]
                output_dict["Right"] = coord_list[0]
            
        elif reg_type == "ud":
            if coord_list[0][1] < coord_list[-1][1]:
                output_dict["Up"] = coord_list[0]
                output_dict["Down"] = coord_list[-1] 
            else:
                output_dict["Up"] = coord_list[-1]
                output_dict["Down"] = coord_list[0]
        
        return output_dict

    # {
    # "X POSITION": 60,         # DONE
    # "Y POSITION": 61,         #
    # "Z POSITION": 44,         #
    # "CONVERSION TV": 29.8,    #
    # "CONVERSION SV": 31.1,    #
    # "CENTER X" : 350,         #
    # "CENTER Y" : 349.5,       #
    # "CENTER Z" : 1010,        # 
    # "TOP" : 934.3333,         #
    # "MIDDLE" : 1085.6667,     #
    # "FRAME RATE" : 50,        #
    # "DURATION" : 300          #
    # }   

    def loadexisted_output(self):
        try:
            with open(self.output_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            logger.debug("File of User-input coordinates not existed yet, create new one.")
            return {}

        return data

    def calculation(self):

        logger.debug("Calculating parameters...")

        #[TODO] Make something for user to input FRAME RATE AND DURATION
        # FOR NOW, JUST USE DEFAULT

        DEFAULT_FRAMERATE = 50
        DEFAULT_DURATION = 300

        self.output_params["FRAME RATE"] = DEFAULT_FRAMERATE
        self.output_params["DURATION"] = DEFAULT_DURATION

        real_distance_SV = float(self.user_inputs['A']['real'])
        try:
            real_distance_TV = float(self.user_inputs['C']['real'])
        except:
            logger.debug("Couldn't find real distance of TV from line C, Using real distance from line B instead.")
            try:
                real_distance_TV = float(self.user_inputs['B']['real'])
            except:
                logger.debug("Couldn't find real distance of TV from line B, Using real distance from line A instead. (Only when the tank is square)")
                logger.warning("Real Distance TopView is from line A, if the tank is not square, please input the real distance of TopView in line C.")
                real_distance_TV = float(self.user_inputs['A']['real'])
 
        # X POSITION
        self.output_params["X POSITION"] = self.user_inputs['A']['pixel']['start'][0]
        # Center X
        self.output_params["CENTER X"] = self.user_inputs['A']['pixel']['center'][0]
        # Conversion Side View
        try:
            self.output_params["CONVERSION TV"] = self.user_inputs['A']['pixel']['distance'] / real_distance_SV # pixel / cm
        except ZeroDivisionError:
            raise ZeroDivisionError("Real distance of SideView (line A) is 0, please check your input.")

        self.output_params["CONVERSION TV"] = round(self.output_params["CONVERSION TV"], ALLOWED_DECIMALS)

        # Y POSITION
        self.output_params["Y POSITION"] = self.user_inputs['B']['pixel']['start'][1]
        # Center Y
        self.output_params["CENTER Y"] = self.user_inputs['B']['pixel']['center'][1]

        # Conversion Top View
        try:
            self.output_params["CONVERSION SV"] = self.user_inputs['C']['pixel']['distance'] / real_distance_TV # pixel / cm
        except ZeroDivisionError:
            raise ZeroDivisionError("Real distance of TopView (line C) is 0, please check your input.")
        self.output_params["CONVERSION SV"] = round(self.output_params["CONVERSION SV"], ALLOWED_DECIMALS)

        # Immagine the tank is split into 3 parts, top, mid, bottom. "UPPER" and "LOWER" are the upper and lower threshold of the middle part.
        # Upper threshold
        self.output_params["UPPER"] = self.user_inputs['D']['pixel']['start'][0] + 1/3 * self.user_inputs['D']['pixel']['distance']
        self.output_params["UPPER"] = round(self.output_params["UPPER"], ALLOWED_DECIMALS)
        # Middle threshold
        self.output_params["LOWER"] = self.user_inputs['D']['pixel']['start'][0] + 2/3 * self.user_inputs['D']['pixel']['distance']
        self.output_params["LOWER"] = round(self.output_params["LOWER"], ALLOWED_DECIMALS)
        # Center Z
        self.output_params["CENTER Z"] = self.user_inputs['D']['pixel']['center'][0]
        # Z Position
        self.output_params["Z POSITION"] = self.user_inputs['D']['pixel']['end'][0]

        logger.debug("Parameters calculated.")

    def save_params(self):

        logger.debug("Saving params to {}".format(self.output_path))
        
        try:
            with open(self.output_path, 'w') as f:
                json.dump(self.output_params, f, indent=4)
        except:
            logger.error("Failed to save params to {}".format(self.output_path))

        logger.info("Saved params to {}".format(self.output_path))



##################################### LOAD & REARRANGER TRAJECTORIES #####################################

class TrajectoriesLoader():

    def __init__(self, 
                 project_dir=None, 
                 batch_num = 1, 
                 treatment_char="A", 
                 TOTAL_FRAMES = 15000, 
                 NORMALIZE_RATIO = 1,
                 corr_type='pearson'):

        if project_dir == None:
            self.project_dir = TEMPLATE_PATH
            logger.warning("No project directory specified. Using template directory instead.")
        else:
            self.project_dir = project_dir

        self.trajectories_dir = get_trajectories_dir(self.project_dir, batch_num, treatment_char)

        self.trajectories_SV_path = get_sideview_trajectory_path(self.project_dir, batch_num, treatment_char)
        # SideView contains Y and Z coordinates
        self.trajectories_TV_path = get_topview_trajectory_path(self.project_dir, batch_num, treatment_char)
        # TopView contains X and Y coordinates

        self.TOTAL_FRAMES = TOTAL_FRAMES
        self.NORMALIZE_RATIO = NORMALIZE_RATIO

        # self.tj_SV, self.tanks_list_SV, removed_rows_SV = self.RawLoader(self.trajectories_SV_path)
        # self.tj_TV, self.tanks_list_TV, removed_rows_TV = self.RawLoader(self.trajectories_TV_path)

        # if removed_rows_SV > removed_rows_TV:
        #     # Remove the difference from self.tj_SV
        #     self.tj_SV = self.tj_SV.iloc[removed_rows_SV-removed_rows_TV:]
        #     logger.debug("Balancing 2 trajectories files: Removed {} rows from SideView".format(removed_rows_SV-removed_rows_TV))
        # elif removed_rows_SV < removed_rows_TV:
        #     # Remove the difference from self.tj_TV
        #     self.tj_TV = self.tj_TV.iloc[removed_rows_TV-removed_rows_SV:]
        #     logger.debug("Balancing 2 trajectories files: Removed {} rows from TopView".format(removed_rows_TV-removed_rows_SV))

        

        self.tj_SV, self.tj_TV, self.tanks_list_SV, self.tanks_list_TV = self.CoupleRawLoader()

        self.FISH_NUM = len(self.tanks_list_TV)

        # self.tj_SV = self.tj_SV[:self.TOTAL_FRAMES]
        # self.tj_TV = self.tj_TV[:self.TOTAL_FRAMES]

        self.Plot_Y_and_Save("pre-arranged")
        
        self.check_integrity()

        self.set_coorelation_type(corr_type)

        self.FISHES = self.rearranger()

        self.Plot_Y_and_Save("post-arranged")

        self.FISHES = self.converter(self.FISHES)

        self.SaveTrajectories()

    def set_coorelation_type(self, corr_type):

        assert corr_type in ['pearson', 'spearman', 'kendalltau', 'hoeffd', 'dCor', 'MIC'], "corr_type must be either 'pearson', 'spearman', 'kendalltau', 'hoeffd', 'dCor', 'MIC'"

        self.correlation_type = corr_type

        logger.info(f"Correlation type set to {corr_type}")


    def correlation_calculation(self, list1, list2):
        """
            hoeffding algorithm is loaded from : https://github.com/PaulVanDev/HoeffdingD/blob/master/XtendedCorrel.py
        """
        try: 
            corr_type = self.correlation_type
        except:
            corr_type = 'pearsonr'

        # print(f"Calculating correlation using {corr_type}")

        arr1 = np.array(list1)
        arr2 = np.array(list2)
        if not len(arr1) == len(arr2):
            return "The lists have different lengths!"
        
        if corr_type == 'pearson':
            t0 = time.time()
            logger.debug(f"Calculating using {corr_type} correlation")
            coeff = pearsonr(arr1, arr2).statistic
            logger.debug(f"Took {time.time() - t0} seconds to calculate Pearson correlation coefficient")
            return coeff
        elif corr_type == 'spearman':
            logger.debug(f"Calculating using {corr_type} correlation")
            return spearmanr(arr1, arr2).correlation
        elif corr_type == 'kendalltau':
            logger.debug(f"Calculating using {corr_type} correlation")
            return kendalltau(arr1, arr2).correlation
        elif corr_type == 'hoeffd':
            t0 = time.time()
            logger.debug(f"Calculating using {corr_type} correlation")
            coeff = hoeffding(arr1, arr2)
            logger.debug(f"Took {time.time() - t0} seconds to calculate HoeffD correlation coefficient")
            return coeff
        elif corr_type == 'dCor':
            t0 = time.time()
            from dcor import distance_correlation
            logger.debug(f"Took {time.time() - t0} seconds to load dcor")
            t0 = time.time()
            logger.debug(f"Calculating using {corr_type} correlation")
            coeff = distance_correlation(arr1, arr2)
            logger.debug(f"Took {time.time() - t0} seconds to calculate dCor coefficient")
            return coeff
        elif corr_type == 'MIC':
            t0 = time.time()
            from minepy import MINE
            logger.debug(f"Took {time.time() - t0} seconds to load minepy")
            t0 = time.time()
            logger.debug(f"Calculating using {corr_type} correlation")
            mine = MINE()
            mine.compute_score(arr1, arr2)
            logger.debug(f"Took {time.time() - t0} seconds to calculate MIC coefficient")
            return mine.mic()


    def CoupleRawLoader(self):
        """
            Load raw data from 2 files, clean them and couple them together 
        """
        try:
            trajectories_SV, tank_list_SV = load_raw_df(self.trajectories_SV_path)
        except Exception as e:
            logger.error("Failed to load trajectories from {}".format(self.trajectories_SV_path))
            logger.error(e)
            raise ValueError("Failed to load trajectories from {}".format(self.trajectories_SV_path))
        
        try:
            trajectories_TV, tank_list_TV = load_raw_df(self.trajectories_TV_path)
        except Exception as e:
            logger.error("Failed to load trajectories from {}".format(self.trajectories_TV_path))
            logger.error(e)
            raise ValueError("Failed to load trajectories from {}".format(self.trajectories_TV_path))
        
        trajectories_SV, trajectories_TV = couple_df_cleaner(input_df1 = trajectories_SV, 
                                                             input_df2 = trajectories_TV,
                                                             limitation = self.TOTAL_FRAMES)
        
        trajectories_SV = trajectories_SV.astype(float)
        trajectories_TV = trajectories_TV.astype(float)

        # Double-check the balance of 2 trajectories
        if len(trajectories_SV) != len(trajectories_TV):
            logger.error("Number of rows in Side View and Top View are not the same, please check your input.")
            raise ValueError("Number of rows in Side View and Top View are not the same, please check your input.")

        return trajectories_SV, trajectories_TV, tank_list_SV, tank_list_TV

       
    def converter(self, fishes):
        """
            Convert the Z axis of each fish from Side View scale to Top View scale
        """
        for i in range(1, self.FISH_NUM+1):
            # Normalize the Z axis of FISHES[f"Y{i}"]
            fishes[f"Fish {i}"]["Z_SV"] = fishes[f"Fish {i}"]["Z"]
            fishes[f"Fish {i}"]["Z"] = fishes[f"Fish {i}"]["Z"] * self.NORMALIZE_RATIO
        return fishes


    def rearranger(self):
        """
            Rearrange the trajectories based on the correlation of Y coordinates between Side View and Top View
        """
        columns = ["TopView"] + [f"SV Y{i}" for i in range(1, 7)]
        score_df = pd.DataFrame(columns=columns)
        score_df['TopView'] = [f"TV Y{i}" for i in range(1, 7)]

        # Prepare an empty cost matrix
        cost_matrix = np.empty((self.FISH_NUM, self.FISH_NUM))

        # Compute Pearson correlation for each pair and fill the cost matrix
        for i in range(self.FISH_NUM):
            TV_list = self.tj_TV[f'Y{i+1}'].tolist()
            for j in range(self.FISH_NUM):
                SV_list = self.tj_SV[f'Y{j+1}'].tolist()
                correlation_coeff = self.correlation_calculation(TV_list, SV_list)
                if np.isnan(correlation_coeff):
                    logger.warning(f"correlation_coeff of Fish {i+1} and Fish {j+1} is NaN, set to negative infinity")
                    cost_matrix[i, j] = POS_INF
                else:
                    cost_matrix[i, j] = 1 - correlation_coeff  # Using 1 - correlation as the cost

        self.cost_matrix = cost_matrix

        # Use the Hungarian algorithm to find the best assignment
        try:
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
        except ValueError as e:
            logger.error("Failed to rearrange trajectories, please check your input.")
            logger.debug(f"{cost_matrix=}")
            raise ValueError("Failed to rearrange trajectories, please check your input.") from e
        
        # Rearrange the columns of TopView dataframe based on optimal assignment
        new_tj_SV = pd.DataFrame(columns=self.tj_SV.columns)
        self.arranged_fish_list_SV = [j+1 for j in col_ind]  # Fix the off-by-one error
        for i, j in zip(row_ind, col_ind):
            new_tj_SV[f"X{i+1}"] = self.tj_SV[f"X{j+1}"]
            new_tj_SV[f"Y{i+1}"] = self.tj_SV[f"Y{j+1}"]

        self.tj_SV = new_tj_SV

        # Create X, Y, Z data for each fish
        FISHES = {}
        for i in range(1, self.FISH_NUM+1):
            FISHES[f"Fish {i}"] = pd.DataFrame({
                "X": self.tj_TV[f"X{i}"],
                "Y": self.tj_TV[f"Y{i}"],
                "Z": self.tj_SV[f"X{i}"]  # Assuming you meant SV X as Z
            })

        return FISHES # Each fish would have a dataframe with X,Y,Z columns


    def check_integrity(self):
        """
            Check if the number of tanks in Side View and Top View are the same 
        """   
        if len(self.tanks_list_SV) != len(self.tanks_list_TV):
            logger.error("Number of tanks in Side View and Top View are not the same, please check your input.")
            raise ValueError("Number of tanks in Side View and Top View are not the same, please check your input.")
        else:
            logger.info("Number of tanks in Side View and Top View are the same, continue.")
    

    def SaveTrajectories(self, save_dict = None, save_dir = None):
        """
            Save the rearranged trajectories to .csv files 
        """
        if save_dir == None:
            save_dir = self.trajectories_dir
        if save_dict == None:
            save_dict = self.FISHES
        save_dir.mkdir(parents=True, exist_ok=True)
        for fish_name, fish_df in save_dict.items():
            save_path = save_dir / f"{fish_name}.csv"
            fish_df.to_csv(save_path, index=False)
            logger.info(f"Trajectory of {fish_name} saved to {save_path}")

        # Check if number of .csv file in save_dir is the same as FISH_NUM
        if len(list(save_dir.glob("*.csv"))) != len(save_dict):
            logger.error("Number of .csv files in {} is not the same as FISH_NUM".format(save_dir))
            raise ValueError("Number of .csv files in {} is not the same as FISH_NUM".format(save_dir))
        else:
            logger.info("All trajectories saved to {}".format(save_dir))

    def visualize_cost_matrix(self, title, save_path=None):
        plt.figure()

        sns.heatmap(cost_matrix, annot=True, fmt='.2f', cmap='Blues')
        # set font for number inside heatmap
        # plt.rcParams['font.size'] = 24
        # save fig
        plt.title(title)

        if save_path != None:
            plt.savefig(save_path)
        plt.show()

    def Plot_Y_and_Save(self, file_name):
        """
            Plot the Y coordinates of Side View and Top View and save to .png file 
        """
        save_dir = self.trajectories_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        def plot_trajectories(input_df_1, input_df_2, tanks_list, file_name):
            # create subplots = len(tanks_list)

            fig, axs = plt.subplots(len(tanks_list), 2, figsize=(10, 10))

            for i, tank in enumerate(tanks_list):

                axs[i, 0].plot(input_df_1[f"Y{tank}"])
                axs[i, 0].set_title(tank)
                axs[i, 0].set_xlabel("Frame Number")
                axs[i, 0].set_ylabel("Pixel Value")

                axs[i, 1].plot(input_df_2[f"Y{tank}"])
                axs[i, 1].set_title(tank)
                axs[i, 1].set_xlabel("Frame Number")
                axs[i, 1].set_ylabel("Pixel Value")
                

            plt.tight_layout()

            save_path = save_dir / f"trajectories_Y_{file_name}.png"

            # export to file
            try:
                plt.savefig(save_path)
                print(f"Trajectories {file_name} saved to {save_path}")
            except:
                print(f"Failed to save trajectories {file_name} to {save_path}")

        plot_trajectories(self.tj_TV, self.tj_SV, self.tanks_list_TV, file_name)


    
    

################################################### LOADER ######################################################## 

class Parameters():

    def __init__(self, project_dir=None, batch_num=1, treatment_char="A"):

        if project_dir == None:
            self.project_dir = TEMPLATE_PATH
            logger.warning("No project directory specified. Using template directory instead.")
        else:
            self.project_dir = project_dir

        if treatment_char not in CHARS:
            treatment_char = "A"
            logger.warning("Treatment character not specified. Using A as default.")

        static_dir = get_static_dir(self.project_dir, batch_num, treatment_char)
            
        self.param_path = static_dir / "parameters.json"

        self.LEAST_NUMBER_OF_PARAMS = 10

        self.PARAMS = self.FirstLoad()

    
    def __getitem__(self, key, refresh=False):
        if refresh:
            self.Refresh()
        return self.PARAMS.get(key, None)


    def Refresh(self):
        self.PARAMS = self.Load(self)


    def Update(self, modify_dict):

        PARAMS = self.Load(self)
        
        for key, value in modify_dict.items():
            PARAMS[key] = value

        with open(self.param_path, 'w') as file:
            json.dump(PARAMS, file, indent=4)
        
        logger.info("Parameters updated.")
        self.PARAMS = PARAMS


    def Load(self):

        try:
            with open(self.param_path, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            logger.error(f"parameters.json not found at {self.param_path}, please check your input.")
            return None
        
        # Convert all values to float
        for key, value in data.items():
            if key == "CORR TYPE":
                continue
            data[key] = float(value)

        return data
    

    def FirstLoad(self):

        logger.info("Initializing parameters...")
        data = self.Load()
        if data == None or len(data) < self.LEAST_NUMBER_OF_PARAMS:
            logger.info("parameters.json not found, creating new one.")
            logger.debug("Running ParamsCalculator() to calculate params from user input coordinates")
            _ = ParamsCalculator(self.project_dir)
            data = self.Load()
            if data == None:
                logger.error("parameters.json not found, please check your input.")
                raise FileNotFoundError("parameters.json not found, please check your input.")

        return data




class Loader():
    
    def __init__(self, project_dir, batch_num, treatment_char, fish_num, params):

        self.project_dir = project_dir
        self.batch_num = batch_num
        self.treatment_char = treatment_char
        self.PARAMS = params

        self.fish_name = SAVED_TRAJECTORY_FORMAT.format(fish_num)

        try:
            self.TOTAL_FRAMES = int(self.PARAMS["DURATION"] * self.PARAMS["FRAME RATE"])
        except:
            logger.error("Failed to load 'DURATION' and 'FRAME RATE' from parameters.json")
            raise ValueError("Failed to load 'DURATION' and 'FRAME RATE' from parameters.json")
        
        # CONVERT Z axis from SV to TV scale
        self.NORMALIZE_RATIO = self.PARAMS["CONVERSION TV"] / self.PARAMS["CONVERSION SV"]

        self.trajectories_dir = get_trajectories_dir(self.project_dir, self.batch_num, self.treatment_char)

        self.FISH = self.FishLoader()

        self.Create_Normalized_Trajectories_And_Save(unit="pixel")

        self.Create_Normalized_Trajectories_And_Save(unit="cm")



    ################################# FISH LOADER #################################

    def FishLoader(self):

        fish_path = self.trajectories_dir / self.fish_name
        if not fish_path.exists():
            _ = TrajectoriesLoader(project_dir = self.project_dir,
                                   batch_num = self.batch_num, 
                                   treatment_char=self.treatment_char,
                                   TOTAL_FRAMES = self.TOTAL_FRAMES, 
                                   NORMALIZE_RATIO = self.NORMALIZE_RATIO)
            return self.FishLoader()
        else:
            logger.info("Loading fish {} from {}".format(self.fish_name, fish_path))
            try:
                fish = pd.read_csv(fish_path)
            except Exception as e:
                logger.error("Failed to load fish {} from {}".format(self.fish_name, fish_path))
                logger.error("Something went wrong with the TrajectoriesLoader()")
                raise ValueError("Failed to load fish {} from {}".format(self.fish_name, fish_path))
            return fish
        

    def Create_Normalized_Trajectories_And_Save(self, unit):

        logger.info(f"Creating normalized trajectories for {self.fish_name} with unit={unit}...")

        
        save_dir = get_normalized_trajectories_dir(project_dir = self.project_dir, 
                                                    batch_num = self.batch_num, 
                                                    treatment_char = self.treatment_char,
                                                    unit = unit)
        save_path = save_dir / f"{self.fish_name}"

        if save_dir.exists():
            if save_path.exists():
                logger.debug(f"{self.fish_name} file existed, skip saving")
                return
        else:
            save_dir.mkdir(parents=True, exist_ok=True)

        normalized_df = self.Normalizer(input_fish_df = self.FISH, unit=unit)
        normalized_df.to_csv(save_path, index=False)
        logger.info(f"Trajectory of {self.fish_name} saved to {save_path}")


    def Normalizer(self, input_fish_df, unit="pixel"):

        assert unit in ["pixel", "cm"]

        if unit == "pixel":
            CONVERT_RATIO = 1
        else:
            CONVERT_RATIO = 1 / self.PARAMS["CONVERSION TV"]
            

        normalized_df = pd.DataFrame(columns = ["X", "Y", "Z"])
        for axis in ["X", "Y"]:
            normalized_df[axis] = (input_fish_df[axis] - self.PARAMS[f"{axis} POSITION"]) * CONVERT_RATIO

        normalized_df["Z"] = (self.PARAMS[f"Z POSITION"] - input_fish_df["Z"]) * CONVERT_RATIO
        
        return normalized_df
        

    def distance_to(self, TARGET="CENTER"):

        MARKS = {}
        for axis in ["X", "Y", "Z"]:
            MARKS[axis] = self.PARAMS[f"{TARGET} {axis}"]

        distance_list = []

        for _, row in self.FISH.iterrows():
            distance = 0
            for axis in ["X", "Y", "Z"]:
                distance += (row[axis] - MARKS[axis]) ** 2
            distance = np.sqrt(distance)
            distance = distance/self.PARAMS["CONVERSION TV"]
            distance_list.append(distance)

        return distance_list
    

    def distance_in(self, distance_list, positions, position_name):

        unique_positions = list(set(positions))
        if position_name not in unique_positions:
            logger.debug("Position {} not found in positions list".format(position_name))
            return [0] * len(distance_list)
        else:
            return [x for i, x in enumerate(distance_list) if positions[i] == position_name]

class CustomDisplay():

    def __init__(self):

        pass

    def get_variables(self, magic = False):

        self_dir = [x for x in dir(self) if x not in dir(CustomDisplay)]
        if magic:
            return self_dir
        else:
            return [x for x in self_dir if not x.startswith('__')]

    def __str__(self):

        message = "Variables:\n"
        for variable in self.get_variables():
            message += f'{str(variable)}: {str(getattr(self, variable))}\n'

        return message


class Time(CustomDisplay):

    def __init__(self, time_list):

        self.list = time_list  # [1, 1, 1, 0, 0, 0, 1, 0]

        self.duration = sum(self.list)  # in frames
        # print(f'Duration: {self.duration} / {len(self.list)}')
        self.percentage = self.duration / len(self.list) * 100
        self.not_duration = len(self.list) - self.duration  # in frames
        self.not_percentage = 100 - self.percentage
        self.unit = 's'

    

class Events(CustomDisplay):

    def __init__(self, event_dict, duration):

        self.dict = event_dict

        if '-1' in event_dict.keys():
            self.count = 0
            self.longest = 0
            self.percentage = 0
            # take out this key
            self.dict.pop('-1')
        else:
            self.count = len(self.dict)
            self.longest = max(self.dict.values())
            self.percentage = self.longest / duration * 100

        self.unit = 's'



class Area(CustomDisplay):

    def __init__(self, area_list):

        self.list = area_list
        self.avg = round(mean(self.list), ALLOWED_DECIMALS)
        self.unit = 'cm^2'
    

    def __add__(self, other):

        temp_list = self.list + other.list
        return Area(temp_list, self.hyp)
    


class Distance(CustomDisplay):

    def __init__(self, distance_list):

        self.list = distance_list

        self.total = round(sum(self.list), ALLOWED_DECIMALS)
        self.avg = round(mean(self.list), ALLOWED_DECIMALS)
        self.unit = 'cm'


    def __add__(self, other):

        temp_list = self.list + other.list
        return Distance(temp_list, self.hyp)
    


class Speed(CustomDisplay):

    def __init__(self, speed_list, total_frames):

        self.list = speed_list
        self.total_frames = total_frames

        self.max = round(max(self.list), ALLOWED_DECIMALS)
        self.min = round(min(self.list), ALLOWED_DECIMALS)
        self.avg = round(mean(self.list), ALLOWED_DECIMALS)
        self.unit = 'cm/s'

        self.Classifier()

    
    def __add__(self, other):

        # Check if other has list and total_frames
        if not hasattr(other, 'list') or not hasattr(other, 'total_frames'):
            raise AttributeError("Other object doesn't have 'list' or 'total_frames' attribute")

        temp_list = self.list + other.list

        if self.total_frames != other.total_frames:
            raise ValueError(f"Total frames of self and other are not the same, {self.total_frames=} != {other.total_frames=}")
        else:
            return Speed(temp_list, self.total_frames)

    def Classifier(self, 
                   THRESHOLD_1 = 1,
                   THRESHOLD_2 = 10):

        slow_count = 0
        medium_count = 0
        fast_count = 0

        for speed in self.list:
            if speed < THRESHOLD_1:
                slow_count += 1
            elif speed < THRESHOLD_2:
                medium_count += 1
            else:
                fast_count += 1

        self.slow = round(slow_count / self.total_frames * 100, ALLOWED_DECIMALS)
        self.medium = round(medium_count / self.total_frames * 100, ALLOWED_DECIMALS)
        self.fast = round(fast_count / self.total_frames * 100, ALLOWED_DECIMALS)

        

class Angle(CustomDisplay):

    def __init__(self, angle_class, frame_rate, interval=1):

        self.angle_class = angle_class
        self.frame_rate = frame_rate

        self.interval = -1
        self.set_interval(interval=interval)


    def calculate_velocity(self):

        def chunk_calc(input_list : list[float], chunk_size : int) -> list[float]:
            logger.debug(f"Calculated angular velocity using chunk_calc(), {chunk_size=}")
            return [abs(sum(input_list[i:i+chunk_size]))%180 for i in range(0, len(input_list), chunk_size)]
        
        # angular_velocity_list = []
        # for i in range(len(self.list)):
        #     # Angular velocity = Turning angle/Time
        #     angular_velocity = self.list[i]
        #     angular_velocity_list.append(angular_velocity)
        #     # UNIT: degree/s
        chunk_size = int(self.frame_rate/self.interval)
        print(f"{chunk_size=}, {self.frame_rate=} {self.interval=}")
        angular_velocity_list = chunk_calc(input_list=self.list, chunk_size=chunk_size)

        # [NOTE] Used same name for the class and the variablwe to save memory, but they are different
            
        angular_velocity = Speed_A(speed_a_list = angular_velocity_list)

        return angular_velocity
    

    def set_interval(self, interval):
        
        if self.interval == interval:
            logger.warning(f"Interval is already {self.interval}, no need to set again.")
        else:
            logger.info(f"Setting interval to {interval}")
            self.interval = interval
            
            self.list = self.angle_class.turning_angles(interval=self.interval)
            self.absolute = [abs(x) for x in self.list]
            self.total = round(sum(self.absolute), ALLOWED_DECIMALS)
            self.avg = round(mean(self.absolute), ALLOWED_DECIMALS)
            self.unit = 'degree'

            self.velocity = self.calculate_velocity()



class Speed_A(CustomDisplay):

    def __init__(self, speed_a_list):

        self.list = speed_a_list
        self.total_instances = len(self.list)

        self.max = round(max(self.list), ALLOWED_DECIMALS)
        self.min = round(min(self.list), ALLOWED_DECIMALS)
        self.avg = round(mean(self.list), ALLOWED_DECIMALS)
        self.unit = 'degree/s'

        self.Classifier()


    def Classifier(self, THRESHOLD = 90):

        slow_count = 0
        fast_count = 0

        for i, speed in enumerate(self.list):
            if speed < 0:
                raise Exception(f"Negative speed, {speed=} found, please check your input.")
            if speed > 181:
                raise Exception(f"Speed > 180, {speed=} found at position {i}/{len(self.list)} please check your input.")
            
            if speed <= THRESHOLD:
                slow_count += 1
            else:
                fast_count += 1

        self.slow = round(slow_count / self.total_instances * 100, ALLOWED_DECIMALS)
        self.fast = round(fast_count / self.total_instances * 100, ALLOWED_DECIMALS)

    
    def plot_histogram(self, bins=100, DISPLAY=True, save_path=None, excel_path=None, fish_num=None):

        #reset figure
        plt.clf()

        percentile = plt.hist(self.list, bins=bins)
        plt.title('Angular Velocity')
        plt.xlabel('Angular Velocity (degree/s)')
        plt.ylabel('Frequency')
        if save_path:
            # if save_path file existed, overwrite
            if os.path.exists(save_path):
                os.unlink(save_path)
            plt.savefig(save_path)

        if excel_path and fish_num:
            if fish_num == 1:
                os.unlink(excel_path)
            if os.path.exists(excel_path):
                index=False
            else:
                index=True
            df = pd.DataFrame({f'Fish {fish_num}': self.list})
            append_df_to_excel(filename=excel_path,
                                df=df,
                                sheet_name='Angular Velocity',
                                startrow=0,
                                index=index)

        if DISPLAY:
            plt.show()

        thresholds = percentile[1]
        percentile = percentile[0]
        percentile = percentile.tolist()
        percentile = [i/sum(percentile) for i in percentile]

        print(f"Percentile: {percentile}")
        print(f"Thresholds: {thresholds}")
        