import pandas as pd
import time

from Libs.analyzer import GeneralAnalysis, ShoalingAnalysis
from Libs.general import TrajectoriesLoader, Parameters
from Libs.misc import get_trajectories_dir, has_csv_file, append_df_to_excel, excel_polish, get_working_dir, merge_cells
from . import TEMPLATE_PATH, CHARS

import logging

logger = logging.getLogger(__name__)


# class Executor(GeneralAnalysis):

#     def __init__(self, project_dir=None, batch_num=1, treatment_char="A", fish_num=1):

#         super().__init__(project_dir=project_dir, batch_num=batch_num, treatment_char=treatment_char, fish_num=fish_num)

def EndPoints_Adder(object):

    endpoints = {}

    def add_endpoint(name, value, unit):
        endpoints[name] = {"value": value, "unit": unit}

    name = "Total Distance"
    value = object.distance.total
    unit = object.distance.unit
    add_endpoint(name, value, unit)

    name = "Average Speed"
    value = object.speed.avg
    unit = object.speed.unit
    add_endpoint(name, value, unit)

    name = "Total Absolute Turn Angle"
    value = object.turning_angle.total
    unit = object.turning_angle.unit
    add_endpoint(name, value, unit)

    name = "Average Angular Velocity"
    value = object.turning_angle.velocity.avg
    unit = object.turning_angle.velocity.unit
    add_endpoint(name, value, unit)

    name = "Slow Angular Velocity Percentage"
    value = object.turning_angle.velocity.slow
    unit = "%"
    add_endpoint(name, value, unit)

    name = "Fast Angular Velocity Percentage"
    value = object.turning_angle.velocity.fast
    unit = "%"
    add_endpoint(name, value, unit)

    name = "Meandering"
    value = object.meandering
    unit = "degree/m"
    add_endpoint(name, value, unit)

    # name = "Latent Time - Slow"
    # value = object.latent_time_slow
    # unit = "%"
    # add_endpoint(name, value, unit)
    
    # name = "Latent Time - Fast"
    # value = object.latent_time_fast
    # unit = "%"
    # add_endpoint(name, value, unit)

    name = "Freezing Time"
    value = object.speed.slow
    unit = "%"
    add_endpoint(name, value, unit)

    name = "Swimming Time"
    value = object.speed.medium
    unit = "%"
    add_endpoint(name, value, unit)

    name = "Rapid Movement Time"
    value = object.speed.fast
    unit = "%"
    add_endpoint(name, value, unit)

    name = "Time in Top"
    value = object.time_in_top
    unit = "%"
    add_endpoint(name, value, unit)

    name = "Time in Middle"
    value = object.time_in_middle
    unit = "%"
    add_endpoint(name, value, unit)

    name = "Time in Bottom"
    value = object.time_in_bottom
    unit = "%"
    add_endpoint(name, value, unit)

    name = "Average distance to Center of the Tank"
    value = object.distance_to_center.avg
    unit = object.distance_to_center.unit
    add_endpoint(name, value, unit)

    name = "Total distances traveled in Top"
    value = object.distance_in_TOP.total / 100
    unit = "m"
    add_endpoint(name, value, unit)

    name = "Total entries to the Top"
    value = object.travel_in_TOP.count
    unit = "times"
    add_endpoint(name, value, unit)

    name = "Fractal Dimension"
    value = object.fractal_dimension
    unit = ""
    add_endpoint(name, value, unit)

    name = "Entropy"
    value = object.entropy
    unit = ""
    add_endpoint(name, value, unit)

    return endpoints


class Executor():
        
    def __init__(self, 
                 project_dir=None, 
                 batch_num=1, 
                 treatment_char="A", 
                 EndPointsAnalyze=True, 
                 progress_window=None):

        self.ERROR = None

        self.timing = {}

        self.EPA = EndPointsAnalyze

        self.progress_window = progress_window



        # FIRST CHECK
        _starttime = time.time()

        if project_dir == None:
            self.project_dir = TEMPLATE_PATH
            logger.warning("No project directory specified. Using template directory instead.")
        else:
            self.project_dir = project_dir

        try:
            _ = int(batch_num)
        except:
            batch_num = 1
        self.batch_num = batch_num

        if treatment_char == None or treatment_char not in CHARS:
            self.treatment_char = "A"
            logger.warning("No treatment index specified. Using 'A' instead.")
        else:
            self.treatment_char = treatment_char

        self.timing["Project structure"] = time.time() - _starttime
        
        self.excel_path = self.get_excel_path()

        # # Load PARAMS
        # self.PARAMS_LOADING()


        # # Load TRAJECTORIES
        # self.TRAJECTORIES_LOADING()

        
        # # ENDPOINTS ANALYSIS
        # self.EPA = EndPointsAnalyze
        # self.ENDPOINTS_ANALYSIS()



    def PARAMS_LOADING(self):

        # SECOND CHECK
        _starttime = time.time()

        logger.info("Loading parameters...")

        self.PARAMS = Parameters(project_dir = self.project_dir, 
                                 batch_num = self.batch_num, 
                                 treatment_char = self.treatment_char)

        try:
            self.TOTAL_FRAMES = int(self.PARAMS["DURATION"] * self.PARAMS["FRAME RATE"])
        except:
            ERROR = "Failed to load 'DURATION' and 'FRAME RATE' from parameters.json"
            logger.error(ERROR)
            return ERROR
        
        # CONVERT Z axis from SV to TV scale
        self.NORMALIZE_RATIO = self.PARAMS["CONVERSION TV"] / self.PARAMS["CONVERSION SV"]
        self.timing["Parameters loading"] = time.time() - _starttime

        return None


    def TRAJECTORIES_LOADING(self):
        # THIRD CHECK
        _starttime = time.time()

        logger.info("Loading trajectories...")

        self.trajectories_dir = get_trajectories_dir(self.project_dir, self.batch_num, self.treatment_char)
        # if self.trajectories_dir not exist or empty:

        NEED_TO_LOAD_TRAJECTORIES = False

        if not self.trajectories_dir.exists():
            NEED_TO_LOAD_TRAJECTORIES = True
        else:
            has_csv = has_csv_file(self.trajectories_dir)
            if has_csv:
                NEED_TO_LOAD_TRAJECTORIES = False
            else:
                NEED_TO_LOAD_TRAJECTORIES = True

        if NEED_TO_LOAD_TRAJECTORIES:
            _ = TrajectoriesLoader(project_dir = self.project_dir,
                                   batch_num = self.batch_num, 
                                   treatment_char=self.treatment_char,
                                   TOTAL_FRAMES = self.TOTAL_FRAMES, 
                                   NORMALIZE_RATIO = self.NORMALIZE_RATIO)
        
        self.timing["Trajectories loading"] = time.time() - _starttime


    def ENDPOINTS_ANALYSIS(self, OVERWRITE=False, AV_interval=None):

        # ENDPOINTS ANALYSIS
        _starttime = time.time()

        logger.info("Loading fish data...")

        if self.EPA:

            ERROR = self.excel_path_check()

            if ERROR == "File Existed" and not OVERWRITE:
                return ERROR, None
            
            if ERROR == "File Existed" and OVERWRITE:
                logger.info("Overwriting existing file...")
                # remove existing file
                self.excel_path.unlink()

        DEFAULT_INTERVAL = self.PARAMS["FRAME RATE"]

        if AV_interval == None:
            AV_interval = DEFAULT_INTERVAL
        else:
            try:
                AV_interval = int(float(AV_interval))
            except:
                AV_interval = DEFAULT_INTERVAL
                logger.error(f"Invalid AV_interval. Using default value = {self.PARAMS['FRAME RATE']} instead.")


        # FishQuantities = count the number of .csv file in self.trajectories_dir
        self.FishQuantities = len(list(self.trajectories_dir.glob("*.csv")))

        self.FISHES = {}
        self.EndPoints = {}
        self.FishCoordinates = {}

        self.Fish_Adder(EPA = self.EPA, AV_interval = AV_interval)

        if self.EPA:
            ShoalingAnalyze = ShoalingAnalysis(self.FishCoordinates)
            self.shoalingarea = ShoalingAnalyze.shoalingarea
            self.shoalingvolume = ShoalingAnalyze.shoalingvolume

            self.Export_To_Excel(excel_path = self.excel_path)
            return_excel_path = self.excel_path
        else:
            return_excel_path = None

        self.timing["EndPoints analysis"] = time.time() - _starttime

        return None, return_excel_path
    
    def update_progress_bar(self, value, text):
        if self.progress_window is not None:
            self.progress_window.task_update(value, text)
    
    def get_excel_path(self):
        working_dir = get_working_dir(self.project_dir, self.batch_num)
        excel_path = working_dir / "EndPoints.xlsx"
        return excel_path


    def excel_path_check(self):
        if self.excel_path.exists():
            return "File Existed"
        
        return None


    def Add_Shoaling_Data_To_Excel(self, excel_path):

        sa = list(self.shoalingarea["ConvexHullVolume"])
        sv = list(self.shoalingvolume["ConvexHullVolume"])

        SA_HEADER = "Shoaling Area"
        SV_HEADER = "Shoaling Volume"

        shoaling_df = pd.DataFrame({SA_HEADER: sa, SV_HEADER: sv})
        shoaling_df.index = list(self.shoalingarea.index)

        sheet_name = "Shoaling"
        append_df_to_excel(filename = excel_path,
                           df = shoaling_df,
                           sheet_name=sheet_name)
        logger.debug(f"Shoaling.xlsx is saved to {excel_path}, sheetname={sheet_name}")

        SA_AVG_HEADER = SA_HEADER + " Average"
        SV_AVG_HEADER = SV_HEADER + " Average"

        sa_avg = shoaling_df[SA_HEADER].mean()
        sv_avg = shoaling_df[SV_HEADER].mean()
        avg_df = pd.DataFrame({SA_AVG_HEADER: [sa_avg], SV_AVG_HEADER: [sv_avg]})

        append_df_to_excel(filename = excel_path,
                           df=avg_df,
                           sheet_name=self.treatment_char,
                           startrow=0,
                           index=False)
        
        merge_cells(file_path=excel_path,
                    input_sheet_name=self.treatment_char,
                    input_column_name=[SA_AVG_HEADER, SV_AVG_HEADER], 
                    cell_step=len(self.FISHES),
                    inplace = True)

        return avg_df
    

    def Export_To_Excel(self, excel_path):
        EndPoints_dict = {}
        for fish_num in self.EndPoints.keys():
            EndPoints_dict[fish_num] = {}
            for key, value in self.EndPoints[fish_num].items():
                if value['unit'] == "":
                    EndPoints_dict[fish_num][f"{key}"] = value["value"]
                else:
                    EndPoints_dict[fish_num][f"{key} ({value['unit']})"] = value["value"]

        df_endpoints = pd.DataFrame(EndPoints_dict).T


        append_df_to_excel(filename = excel_path,
                   df = df_endpoints,
                   sheet_name=self.treatment_char)
        logger.debug(f"EndPoints.xlsx is saved to {excel_path}")

        self.Add_Shoaling_Data_To_Excel(excel_path)

        excel_polish(excel_path)
        logger.debug(f"EndPoints.xlsx is polished.")


    
    def Fish_Adder(self, EPA=True, AV_interval = 1):

        for fish_num in range(1, self.FishQuantities+1):
            _starttime = time.time()
            self.FISHES[fish_num] = GeneralAnalysis(project_dir = self.project_dir, 
                                                    batch_num = self.batch_num, 
                                                    treatment_char = self.treatment_char, 
                                                    fish_num = fish_num,
                                                    params = self.PARAMS)
            if EPA == True:
                logger.info(f"EndPoints analysis for Fish {fish_num} initiated...")
                self.FISHES[fish_num].BasicCalculation(DEFAULT_INTERVAL = AV_interval)
                self.EndPoints[fish_num] = EndPoints_Adder(self.FISHES[fish_num])
                self.FishCoordinates[fish_num] = self.FISHES[fish_num].TJ_df
            else:
                logger.info(f"EndPoints analysis for Fish {fish_num} skipped.")

            self.timing[f"Analyze Fish {fish_num}"] = time.time() - _starttime

            progress = fish_num / self.FishQuantities * 100
            self.update_progress_bar(value=progress, text = f"Analyze Fish {fish_num}")


    def Save_AV_Plots(self, interval=1, bins=100, DISPLAY=True):

        batch_dir = get_working_dir(self.project_dir, self.batch_num) 
        AV_plots_dir = batch_dir / "AV Plots"
        AV_plots_dir = AV_plots_dir / self.treatment_char
        AV_plots_dir.mkdir(exist_ok=True, parents=True)

        for fish_num, fish in self.FISHES.items():
            save_path = AV_plots_dir / f"Fish{fish_num}_i{interval}_b{bins}.png"
            av_excel_path = AV_plots_dir / f"AV_i{interval}_b{bins}.xlsx"
            fish.turning_angle.set_interval(interval=interval)
            fish.turning_angle.velocity.plot_histogram(bins=bins, 
                                                       save_path=save_path,
                                                       excel_path = av_excel_path,
                                                       fish_num=fish_num,
                                                       DISPLAY=DISPLAY)
            
            logger.debug(f"AV plot for Fish {fish_num} saved to {save_path}")
            
                                                    
    
    

    


