import tkinter
import tkinter.messagebox
import tkinter.ttk as ttk
import customtkinter

import os
from pathlib import Path

import pandas as pd
import json

import shutil
import time

import logging
from colorlog import ColoredFormatter

import threading

from Libs import BIN_PATH, HISTORY_PATH, CHARS
from Libs.misc import *
from Libs.customwidgets import *
from Libs.project import CreateProject
from Libs.executor import Executor
from Libs.plotShoaling import AnimatedPlot

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

######################################################## TODO #########################################################

#       [1] Add an L ruler to the Measurer class in Libs\customwidgets.py to define the orientation of the tank
#       [2] Add a resize step to the Measurer but remember to multiple the Measuring results by the resize factor
# DONE  [3] Change foreground color of all widgets to black 
# DONE  [4] BUG - Right after Measuring the Parameters can not be loaded, need to reset the program?!?
#       [5] Add the manual selection after general.TrajectoriesLoader.rearranger, 
#           set the rearranger to selecting the second best SV Y if the best matched SV Y has been matched by another TV Y
#       [6] Add something to the GUI to show how to make the Measurer reappear
#       [7] Add a list of treatments to the copy to other treatment button


# [WHAT I'M DOING] finishing the 3D convex hull plotting, put it on the right side of the GUI


########################################### SETUP LOGGING CONFIGURATION ###############################################
logger = logging.getLogger(__name__)

Path('Log').mkdir(parents=True, exist_ok=True)
log_file = 'Log/log.txt'

initiator()

class ContextFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.
    """

    def filter(self, record):
        record.pathname = os.path.basename(record.pathname)  # Modify this line if you want to alter the path
        return True

# Define the log format with colors
log_format = "%(asctime)s %(log_color)s%(levelname)-8s%(reset)s [%(pathname)s] %(message)s"

# Create a formatter with colored output
formatter = ColoredFormatter(log_format)

# Get the root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create a filter
f = ContextFilter()

# Create a file handler to save logs to the file
file_handler = logging.FileHandler(log_file, mode='a')  # Set the mode to 'a' for append
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s [%(pathname)s] %(message)s"))
file_handler.addFilter(f)  # Add the filter to the file handler
file_handler.setLevel(logging.DEBUG)

# Create a stream handler to display logs on the console with colored output
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.addFilter(f)  # Add the filter to the stream handler
stream_handler.setLevel(logging.DEBUG)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

########################################################################################################################

THE_HISTORY = HISTORY()


class App(customtkinter.CTk):

    def __init__(self):

        super().__init__()

        # PREDEFINED VARIABLES
        self.PROJECT_CREATED = False
        self.CURRENT_PROJECT = ""
        self.PREVIOUS_BATCH = ""
        self.PREVIOUS_TREATMENT = ""
        self.TREATMENTLIST = ["Treatment A", "Treatment B", "Treatment C"]
        self.EPA = True

        # configure window
        APP_TITLE = "Locomotion Analyzer 3D"
        self.title(APP_TITLE)
        self.geometry(f"{1500}x{900}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=0) 
        self.grid_columnconfigure((2, 3), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        ### COLUMN 0 ###

        TEXT_COLOR = "#000000"
        TINY_SIZE = 14
        SMALL_SIZE = TINY_SIZE + 2
        MEDIUM_SIZE = SMALL_SIZE + 2
        LARGE_SIZE = MEDIUM_SIZE + 4
        UNIVERSAL_FONT = 'Microsoft Sans Serif'
        HOVER_COLOR = "Yellow"

        LOGO_CONFIG = {
                        "font": (UNIVERSAL_FONT, LARGE_SIZE, "bold"),
                        "text_color": TEXT_COLOR
        }

        LABEL_CONFIG = {
                        "font": (UNIVERSAL_FONT, SMALL_SIZE),
                        "text_color": TEXT_COLOR
        }

        BOLD_LABEL_CONFIG = {
                        "font": (UNIVERSAL_FONT, MEDIUM_SIZE, "bold"),
                        "text_color": TEXT_COLOR
        }

        BUTTON_CONFIG = {"font": (UNIVERSAL_FONT, SMALL_SIZE), 
                         "text_color": TEXT_COLOR,
                         "hover_color": HOVER_COLOR
        }

        PANEL_BUTTON_CONFIG = {"font": (UNIVERSAL_FONT, SMALL_SIZE), 
                         "width": 150, 
                         "height": 40,
                         "text_color": TEXT_COLOR,
                         "hover_color": HOVER_COLOR
        }

        OPTION_MENU_CONFIG = {"font": (UNIVERSAL_FONT, TINY_SIZE),
                            "text_color": TEXT_COLOR,
        }

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        SIDEBAR_ROW = 0
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text=APP_TITLE)
        self.logo_label.configure(**LOGO_CONFIG)
        self.logo_label.grid(row=SIDEBAR_ROW, column=0, columnspan=2, padx=20, pady=(20, 10))
        
        SIDEBAR_ROW += 1
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, 
                                                        text="Create Project", 
                                                        command=self.create_project
                                                        )
        self.sidebar_button_1.configure(**PANEL_BUTTON_CONFIG)
        self.sidebar_button_1.grid(row=SIDEBAR_ROW, column=0, columnspan=2, padx=20, pady=20)

        SIDEBAR_ROW += 1
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, 
                                                        text="Load Project", 
                                                        command=self.load_project
                                                        )
        self.sidebar_button_2.configure(**PANEL_BUTTON_CONFIG)
        self.sidebar_button_2.grid(row=SIDEBAR_ROW, column=0, columnspan=2, padx=20, pady=20)
        
        SIDEBAR_ROW += 1
        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, 
                                                        text="Delete Project", 
                                                        command=self.delete_project
                                                        )
        self.sidebar_button_3.configure(**PANEL_BUTTON_CONFIG)
        self.sidebar_button_3.grid(row=SIDEBAR_ROW, column=0, columnspan=2, padx=20, pady=20)

        SIDEBAR_ROW += 1
        self.ReMeasureButton = customtkinter.CTkButton(self.sidebar_frame, 
                                                         text="Re-Measure Params",
                                                         command=self.params_remeasure
                                                         )
        self.ReMeasureButton.configure(**PANEL_BUTTON_CONFIG)
        self.ReMeasureButton.grid(row=SIDEBAR_ROW, column=0, columnspan = 2, padx=20, pady=20)

        SIDEBAR_ROW += 1
        self.ImportButton = customtkinter.CTkButton(self.sidebar_frame, 
                                                         text="Import Trajectories",
                                                         command=self.import_trajectories
                                                         )
        self.ImportButton.configure(**PANEL_BUTTON_CONFIG)
        self.ImportButton.grid(row=SIDEBAR_ROW, column=0, columnspan = 2, padx=20, pady=20)

        SIDEBAR_ROW += 1
        self.sidebar_button_4 = customtkinter.CTkButton(self.sidebar_frame, 
                                                        text="Export Trajectories", 
                                                        command=self.export_trajectories_THREADED
                                                        )
        self.sidebar_button_4.configure(**PANEL_BUTTON_CONFIG)
        self.sidebar_button_4.grid(row=SIDEBAR_ROW, column=0, columnspan=2, padx=20, pady=20)

        SIDEBAR_ROW += 1
        self.sidebar_button_5 = customtkinter.CTkButton(self.sidebar_frame, 
                                                        text="Analyze", 
                                                        command=self.analyze_project_THREADED
                                                        )
        self.sidebar_button_5.configure(**PANEL_BUTTON_CONFIG)
        self.sidebar_button_5.grid(row=SIDEBAR_ROW, column=0, columnspan=2, padx=20, pady=20)

        SIDEBAR_ROW += 1
        self.ShoalingPlotButton = customtkinter.CTkButton(self.sidebar_frame,
                                                            text="Plot Shoaling",
                                                            command=self.plot_shoaling
                                                            )
        self.ShoalingPlotButton.configure(**PANEL_BUTTON_CONFIG)
        self.ShoalingPlotButton.grid(row=SIDEBAR_ROW, column=0, columnspan = 2, padx=20, pady=20)

        SIDEBAR_ROW += 1
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.configure(**LABEL_CONFIG)
        self.appearance_mode_label.grid(row=SIDEBAR_ROW, 
                                        column=0, 
                                        # columnspan=2, 
                                        padx=20, 
                                        pady=(10, 0))
        
        # SIDEBAR_ROW += 1
        self.appearance_mode_optionmenu = customtkinter.CTkOptionMenu(self.sidebar_frame, 
                                                                       values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionmenu.configure(**OPTION_MENU_CONFIG)
        self.appearance_mode_optionmenu.grid(row=SIDEBAR_ROW, 
                                             column=1,
                                            #  column=0, 
                                            #  columnspan=2, 
                                             padx=20, 
                                             pady=(10, 10))
        
        SIDEBAR_ROW += 1
        self.corr_type_label = customtkinter.CTkLabel(self.sidebar_frame, text="Correlation Type:", anchor="w")
        self.corr_type_label.configure(**LABEL_CONFIG)
        self.corr_type_label.grid(row=SIDEBAR_ROW,
                                    column=0,
                                    padx=20,
                                    pady=(10, 0))
        
        self.corr_type = "pearson"
        self.corr_type_optionmenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                                values=['pearson', 
                                                                        'dCor', 
                                                                        'MIC'],
                                                                command=self.change_corr_type)
        self.corr_type_optionmenu.configure(**OPTION_MENU_CONFIG)
        self.corr_type_optionmenu.grid(row=SIDEBAR_ROW,
                                        column=1,
                                        padx=20,
                                        pady=(10, 10))
        
        SIDEBAR_ROW += 1
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.configure(**LABEL_CONFIG)
        self.scaling_label.grid(row=SIDEBAR_ROW, 
                                column=0, 
                                # columnspan=2, 
                                padx=20, 
                                pady=(10, 0))

        # SIDEBAR_ROW += 1
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, 
                                                               values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.configure(**OPTION_MENU_CONFIG)
        self.scaling_optionemenu.grid(row=SIDEBAR_ROW, 
                                      column=1,
                                    #   column=0, 
                                    #   columnspan=2, 
                                      padx=20, 
                                      pady=(10, 20))

        ## COLUMN 1 ###

        container_1 = customtkinter.CTkFrame(self)
        container_1.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")

        container_1.grid_rowconfigure(0, weight=0)
        container_1.grid_rowconfigure(1, weight=1)
        container_1.grid_columnconfigure(0, weight=0)

        # Top part
        container_2_top = customtkinter.CTkFrame(container_1)
        container_2_top.grid(row=0, column=0, sticky="nsew")

        project_previews_label = customtkinter.CTkLabel(container_2_top, text="Project List", font=customtkinter.CTkFont(size=20, weight="bold"))
        project_previews_label.configure(**BOLD_LABEL_CONFIG)
        project_previews_label.grid(row=0, column=0)

        # Bottom part
        bottom_part = customtkinter.CTkFrame(container_1)
        bottom_part.grid(row=1, column=0, sticky="nsew")

        bottom_part.grid_rowconfigure(0, weight=1)
        bottom_part.grid_rowconfigure(1, weight=0)

        self.scrollable_frame = ScrollableProjectList(bottom_part)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")

        refresh_button = customtkinter.CTkButton(bottom_part, text="Refresh", command=self.refresh_projects)
        refresh_button.configure(**BUTTON_CONFIG)
        refresh_button.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        # Initial refresh to populate the list
        self.refresh_projects()

        self.project_detail_container = ProjectDetailFrame(self, self.CURRENT_PROJECT, width = 400)
        self.project_detail_container.grid(row=1, column = 1, columnspan=3, padx=20, pady=20, sticky="nsew")

        ### COLUMN 2 ###

        column2_padx = 20
        column2_pady = (10,5)

        # Create a canvas to hold the project parameters
        container_2 = customtkinter.CTkFrame(self, width = 400)
        container_2.grid(row=0, column=2, columnspan = 2, padx=(20, 0), pady=column2_pady, sticky="nsew")

        # ROW 0
        # Top part is a dropdown menu to select type of test
        container_2_top = customtkinter.CTkFrame(container_2)
        container_2_top.grid(row=0, column=0, columnspan=3, sticky="nsew")

        Header = customtkinter.CTkLabel(container_2_top, text="Loaded Project:", anchor="w")
        Header.configure(**BOLD_LABEL_CONFIG)
        Header.grid(row=0, column=0, padx=column2_padx, pady=column2_pady, sticky="nsew")

        self.LoadedProject = customtkinter.CTkLabel(container_2_top, text="None", anchor="w")
        self.LoadedProject.configure(**BOLD_LABEL_CONFIG)
        self.LoadedProject.grid(row=0, column=1, columnspan=2, padx=column2_padx, pady=column2_pady, sticky="nsew")

        # ROW 1
        self.BATCHLIST = ["Batch 1"]

        self.container_2_mid = customtkinter.CTkFrame(container_2)
        self.container_2_mid.grid(row=1, column=0, columnspan=3, sticky="nsew")

        
        self.BatchOptions = customtkinter.CTkOptionMenu(self.container_2_mid, dynamic_resizing=False,
                                                        width = 105, values=self.BATCHLIST)
        self.BatchOptions.configure(**OPTION_MENU_CONFIG)
        self.BatchOptions.grid(row=0, column=0, padx=column2_padx, pady=column2_pady, sticky="nsew")

        self.BatchAddButton = customtkinter.CTkButton(self.container_2_mid, text="Add Batch", width = 40,
                                                        command=self.add_batch)
        self.BatchAddButton.configure(**BUTTON_CONFIG)
        self.BatchAddButton.grid(row=0, column=1, padx=column2_padx, pady=column2_pady, sticky="nsew")

        self.BatchRemoveButton = customtkinter.CTkButton(self.container_2_mid, text="Remove Batch", width = 40,
                                                        command=self.remove_batch)
        self.BatchRemoveButton.configure(**BUTTON_CONFIG)
        self.BatchRemoveButton.grid(row=0, column=2, padx=column2_padx, pady=column2_pady, sticky="nsew")
        
        # self.TestOptions = customtkinter.CTkOptionMenu(self.container_2_mid, dynamic_resizing=False, 
        #                                           width=210, values=self.TESTLIST)
        # self.TestOptions.grid(row=1, column=0, columnspan = 2, padx=20, pady=(20, 10), sticky="nsew")

        # self.save_button = customtkinter.CTkButton(self.container_2_mid, text="Save", width = 50,
        #                                            command=self.save_parameters)
        # self.save_button.configure(**BUTTON_CONFIG)
        # self.save_button.grid(row=1, column=2, padx=20, pady=20, sticky="nsew")

        self.TreatmentOptions = customtkinter.CTkOptionMenu(self.container_2_mid, dynamic_resizing=False,
                                                                width=210, values=self.TREATMENTLIST)
        self.TreatmentOptions.configure(**OPTION_MENU_CONFIG)
        self.TreatmentOptions.grid(row=2, column=0, columnspan=2, padx=column2_padx, pady=column2_pady, sticky="nsew")


        # create a Cloner button to copy current treatment's parameters to other treatment
        self.Cloner = customtkinter.CTkButton(self.container_2_mid, text="Copy to other treatment", width = 50,
                                              command=self.copy_to_other_treatment)
        self.Cloner.grid(row=2, column=2, padx=column2_padx, pady=column2_pady, sticky="nsew")


        # Row 2
        self.container_2_bot = customtkinter.CTkFrame(container_2)
        self.container_2_bot.grid(row=2, column=0, columnspan=3, sticky="nsew")

        project_dir = THE_HISTORY.get_project_dir(self.CURRENT_PROJECT)

        self.parameters_frame = WidgetParameters(self.container_2_bot, project_dir, height = 500, width = 400)
        self.parameters_frame.grid(row=0, columnspan=3, padx=20, pady=20, sticky="nsew")

        # Config
        self.BatchOptions.configure(command=self.update_param_display)
        # self.TestOptions.configure(command=self.update_param_display)
        self.TreatmentOptions.configure(command=self.update_param_display)


        self.protocol("WM_DELETE_WINDOW", self.close_app)


    def refresh(self):
        self.update_param_display(load_type = "refresh")
    

    def access_history(self, command_type, project_name = None, batch_name=None, edit_command=None):
        logger.debug("Accessing history file")

        # load the history file
        try:
            with open(HISTORY_PATH, "r") as file:
                projects_data = json.load(file)
        except:
            ErrorType = f"Empty history file at path {HISTORY_PATH}"
            logger.warning(ErrorType)
            return None, ErrorType

        # current project name
        if project_name == None:
            logger.debug(f"No given project name, using {self.CURRENT_PROJECT=}")
            cp = self.CURRENT_PROJECT
        else:
            logger.debug(f"Use given project name: {project_name=}")
            cp = project_name

        # Check if the project exists
        if cp not in projects_data.keys():
            ErrorType = f"Project {cp} doesn't exist"
            logger.warning(ErrorType)
            return None, ErrorType
    
        # How many batch files are there?
        batch_quantity = 0
        batch_list = []
        for key in projects_data[cp].keys():
            if "Batch" in key:
                batch_quantity += 1
                batch_list.append(key)

        if batch_quantity == 0:
            ErrorType = "No batches"
            logger.warning(ErrorType)
            return None, ErrorType

        # Modify the history file
        if command_type == "add":
            logger.debug("Command = add")
            if batch_name in projects_data[cp].keys():
                ErrorType = f"Batch {batch_name=} already exists, can't add"
                logger.warning(ErrorType)
                return None, ErrorType
            else:
                example_key = list(projects_data[cp].keys())[0]
                projects_data[cp][batch_name] = projects_data[cp][example_key]
                with open(HISTORY_PATH, "w") as file:
                    json.dump(projects_data, file, indent=4)
                return None, None
            
        elif command_type == "remove":
            logger.debug("Command = remove")
            if batch_quantity == 1:
                ErrorType = "Last batch, can't remove"
                logger.warning(ErrorType)
                return None, ErrorType
            elif batch_name not in projects_data[cp].keys():
                ErrorType = f"{batch_name} doesn't exist"
                logger.warning(ErrorType)
                return None, ErrorType
            else:
                # Remove the batch
                projects_data[cp].pop(batch_name)
                with open(HISTORY_PATH, "w") as file:
                    json.dump(projects_data, file, indent=4)
                return None, None
            
        elif command_type == "edit":
            logger.debug("Command = edit")
            if edit_command == None:
                ErrorType = "No edit command given"
                logger.warning(ErrorType)
                return None, ErrorType
            else:
                treatment = edit_command[0]
                value_pos = edit_command[1]
                new_value = edit_command[2]
                try:
                    projects_data[cp][batch_name][treatment][value_pos] = new_value
                    with open(HISTORY_PATH, "w") as file:
                        json.dump(projects_data, file, indent=4)
                    return None, None
                except:
                    logger.error("Invalid edit command")
                    raise Exception("Invalid edit command")

        elif command_type == "load batch list":
            logger.debug("Command = load batch list")
            return batch_list, None
        
        elif command_type == "load treatment list":
            logger.debug("Command = load treatment list")
            logger.debug(f"CP: {cp} ,Batch name: {batch_name}")
            treatments = []
            key_list = list(projects_data[cp][batch_name].keys())
            if key_list == 0:
                logger.warning(f"cp = {cp}, batch_name = {batch_name}, no treatments found")
            for treatment_key in projects_data[cp][batch_name].keys():
                _name = projects_data[cp][batch_name][treatment_key][0]
                _dose = projects_data[cp][batch_name][treatment_key][1]
                _unit = projects_data[cp][batch_name][treatment_key][2]
                if _unit == "":
                    treatments.append(_name)
                else:
                    treatments.append(f"{_name} {_dose} {_unit}")
            logger.debug(f"Treatments: {treatments}")
            return treatments, None
        
        else:
            logger.error("Invalid command type")
            raise Exception("Invalid command type")
        

    def change_corr_type(self, new_corr_type: str):
        self.corr_type = new_corr_type
        logger.debug(f"Correlation type changed to {self.corr_type=}")


    def params_remeasure(self):

        project_dir = THE_HISTORY.get_project_dir(self.CURRENT_PROJECT)
        batch_num = self.get_batch_num()
        treatment_char = self.get_treatment_char()

        logger.debug(f"User clicked Re-Measure Params button")
        logger.debug(f"Current status: project = {self.CURRENT_PROJECT}, batch = {batch_num}, treatment = {treatment_char}")
        
        self.parameters_frame.MeasureAndCalculate(project_dir = project_dir,
                                                  batch_num = batch_num,
                                                  treatment_char = treatment_char)
        

    def plot_shoaling(self):

        # Check EndPoints.xlsx existence
        project_dir = THE_HISTORY.get_project_dir(self.CURRENT_PROJECT)
        batch_dir = get_working_dir(project_dir, self.get_batch_num())
        end_points_path = batch_dir / "EndPoints.xlsx"
        static_dir = get_static_dir(project_dir, 
                                        batch_num=self.get_batch_num(),
                                        treatment_char=self.get_treatment_char()
                                        )

        if not end_points_path.exists():
            _message = "EndPoints.xlsx not found"
            _message += "\nPlease make sure you have imported trajectories and analyzed them"
            tkinter.messagebox.showerror("Error", _message)
            return
        
        def load_volume_list():
            # open EndPoints.xlsx, sheet_name = "Shoaling"
            df = pd.read_excel(end_points_path, sheet_name="Shoaling")
            # get the volume list, column_name = f"Shoaling Volume {self.get_treatment_char}"
            try:
                volume_list = df[f"Shoaling Volume {self.get_treatment_char()}"].tolist()
            except KeyError:
                _message = f"Shoaling Volume {self.get_treatment_char()} not found"
                tkinter.messagebox.showerror("Error", _message)
                return None
            
            if len(volume_list) == 0:
                _message = f"Shoaling Volume {self.get_treatment_char()} empty"
                tkinter.messagebox.showerror("Error", _message)
                return None

            return volume_list
        

        def get_fish_dict():
            trajectories_n_p = {}

            trajectories_n_p_dir = static_dir / 'trajectories_normalized_cm'
            for csv_path in list(trajectories_n_p_dir.iterdir()):
                csv_stem = csv_path.stem
                logger.debug(f"{csv_stem=}")
                df = pd.read_csv(csv_path)
                try:
                    df.drop("Z_SV", axis=1, inplace=True)
                except:
                    pass

                trajectories_n_p[csv_stem] = df

            return trajectories_n_p
        

        def calculate_limit_dict():
            ec_path = static_dir / 'essential_coords.json'

            if not ec_path.exists():
                logger.info(f"essential_coords.json of {self.get_treatment_char()} not found")
                logger.info(f"Try to find essential_coords.json of other treatments")
                # find static_dir of other treatments
                other_treatments = [treatment for treatment in self.TREATMENTLIST if treatment != self.TreatmentOptions.get()]
                other_treatments_char = [self.treatment_to_treatment_char(treatment) for treatment in other_treatments]
                while len(other_treatments_char) > 0:
                    other_char = other_treatments_char.pop()
                    logger.info(f"Try {other_char}")
                    other_static_dir = get_static_dir(project_dir,
                                                        batch_num=self.get_batch_num(),
                                                        treatment_char=other_char)
                    other_ec_path = other_static_dir / 'essential_coords.json'
                    if other_ec_path.exists():
                        break
                else:
                    _message = "No available essential_coords.json found"
                    logger.error(_message)
                    raise Exception(_message)
            
            with open(ec_path) as f:
                ec = json.load(f)

            Conversion = (ec['A']['pixel'][1][0] - ec['A']['pixel'][0][0]) / ec['A']['real']
            
            limit_dict = {
                        "X": (ec['A']['pixel'][1][0] - ec['A']['pixel'][0][0])/Conversion,
                        "Y": (ec['B']['pixel'][1][1] - ec['B']['pixel'][0][1])/Conversion,
                        "Z": (ec['D']['pixel'][1][0] - ec['D']['pixel'][0][0])/Conversion
                    }
            
            return limit_dict
        
        given_fish_dict = get_fish_dict()
        limit_dict = calculate_limit_dict()
        volume_list = load_volume_list()

        self.visualize_window = AnimatedPlot(given_fish_dict, 
                                        master=self, 
                                        limit_dict=limit_dict,
                                        volume_list=volume_list)


    def add_batch(self):
        logger.debug("Adding batch")
        new_batch_num = len(self.BATCHLIST) + 1
        self.BATCHLIST.append("Batch " + str(new_batch_num))

        # Update the batch options
        self.BatchOptions.configure(values=self.BATCHLIST)

        # Set the batch to the last batch
        self.BatchOptions.set(self.BATCHLIST[-1])

        # Modify history file
        _, ErrorType = self.access_history("add", batch_name=f"Batch {new_batch_num}")

        if ErrorType != None:
            logger.error(ErrorType)
            tkinter.messagebox.showerror("Error", ErrorType)
            return

        # Create new batch directories and hyp files
        self.save_project(batch_num = new_batch_num, subsequent_save = True)

        self.refresh()


    def remove_batch(self):
        logger.debug("Removing batch")
        selected_batch = self.BatchOptions.get()

        # Pop-up window to confirm deletion
        if not tkinter.messagebox.askokcancel("Delete Batch", f"Are you sure you want to delete {selected_batch}?"):
            return

        # Modify history file
        _, ErrorType = self.access_history("remove", batch_name=selected_batch)

        if ErrorType != None:
            logger.error(ErrorType)
            tkinter.messagebox.showerror("Error", ErrorType)
            return

        self.BATCHLIST, _ = self.access_history("load batch list")

        # Update the batch options
        self.BatchOptions.configure(values=self.BATCHLIST)

        # Set the batch to the last batch
        self.BatchOptions.set(self.BATCHLIST[-1])

        # Remove the batch directories and hyp files
        self.delete_batch(selected_batch)

    
    def delete_batch(self, batch_name):
        logger.debug("Deleting batch")

        batch_num = batch_name.split(" ")[1]

        project_dir = Path(THE_HISTORY.get_project_dir(self.CURRENT_PROJECT))

        # Find all directory in project_dir, at any level, that contain batch_ord, use shutil.rmtree to delete them
        batch_dir = project_dir / f"Batch {batch_num}"
        shutil.rmtree(batch_dir)


    def treatment_to_treatment_char(self, treatment):
        treatment_index = self.TREATMENTLIST.index(treatment)
        treatment_char = CHARS[treatment_index]
        return treatment_char
    
    def get_treatment_char(self, current_treatment = None):
        if current_treatment == None:
            current_treatment = self.TreatmentOptions.get()
        return self.treatment_to_treatment_char(current_treatment)
    
    
    def get_batch_num(self):
        batch_num = self.BatchOptions.get().split()[1]
        return batch_num
    

    def OpenTickBoxWindow(self, current_treatment):

        self.TickedTreatmentBoxes = []

        other_treatments = [treatment for treatment in self.TREATMENTLIST if treatment != current_treatment]

        self.Tickbox = TickBoxWindow(self, other_treatments)

        def on_close():
            self.Tickbox.destroy()
            self.master.focus_set()

        self.Tickbox.protocol("WM_DELETE_WINDOW", on_close)
        self.Tickbox.wait_window()

        ticked_char = [self.treatment_to_treatment_char(treatment) for treatment in self.Tickbox.TickedTreatmentBoxes]
        logger.debug(f"{self.TickedTreatmentBoxes=}")
        logger.debug(f"{ticked_char=}")

        return ticked_char
    

    def copy_to_other_treatment(self):
        current_treatment = self.TreatmentOptions.get() #OK - just for display

        message_ = f"You are going to copy current treatment parameters to other treatments'"
        message_ += f"\nThis is an irreversible action, do you want to continue?"
        confirm = tkinter.messagebox.askyesno("Confirmation", message_)
        if not confirm:
            return

        logger.debug(f"Copying parameters from {current_treatment} to other treatment")

        ticked_char = self.OpenTickBoxWindow(current_treatment)

        # save current treatment parameters to other treatments
        self.save_parameters(mode="current", save_target=ticked_char)

        # # count current entries in available parameters
        # target_amount = self.nested_key_1_frame.get_current_entry_quantity()
        # # mimic the folder change of the current treatment to other treatment
        # self.folder_changer(target_amount, treatment_mode=treatment_mode)

        # Notification
        message_ = "Copied the parameters settings to all other treatments and Saved!"
        tkinter.messagebox.showinfo("Action Completed", message_)
        logger.debug(message_)


    def save_parameters(self, mode = "current", save_target="self"):
        assert mode in ["current", "previous"]

        if mode == "current":
            logger.debug("Save button pressed, save the current parameters")
            # Get the selected test type
            batch_num = self.get_batch_num()
            treatment_char = self.get_treatment_char()
            logger.debug(f"batch num: {batch_num}")
            logger.debug(f"treatment: {treatment_char}")
        else:
            logger.debug("Other option selected, save the previous parameters")
            batch_num = self.PREVIOUS_BATCH
            treatment_char = self.PREVIOUS_TREATMENT
            logger.debug(f"batch num: {batch_num}")
            logger.debug(f"treatment: {treatment_char}")

        # Save the parameters
        # save_parameters(self, project_name, selected_task, treatment, batch_num, mode = 'single'):
        project_dir = THE_HISTORY.get_project_dir(self.CURRENT_PROJECT)
        self.parameters_frame.save_parameters(project_dir = project_dir, 
                                              batch_num = batch_num,
                                              treatment_char = treatment_char,
                                              save_target=save_target)



    def param_display(self, batch_num = 1, treatment_char = "A"):

        project_dir = THE_HISTORY.get_project_dir(self.CURRENT_PROJECT)
        logger.debug(f"Current project dir: {project_dir}")
        self.parameters_frame.load_parameters(project_dir=project_dir, 
                                              batch_num=batch_num, 
                                              treatment_char=treatment_char)

        self.LoadedProject.configure(text=self.CURRENT_PROJECT)

        self.PREVIOUS_BATCH = batch_num
        logger.debug(f"Set PREVIOUS_BATCH to {batch_num}")
        self.PREVIOUS_TREATMENT = treatment_char
        logger.debug(f"Set PREVIOUS_TREATMENT to {treatment_char}")

        # # Set corr_type_optionmenu value to self.parameters_frame.entries['CORR TYPE']
        # self.corr_type_optionmenu.set(self.parameters_frame.entries['CORR TYPE'].get())
        # logger.debug(f"Set corr_type_optionmenu to {self.parameters_frame.entries['CORR TYPE'].get()}")


    def update_param_display(self, event=None, load_type="not_first_load"):
        assert load_type in ["not_first_load", "first_load", "refresh"]

        if load_type == "first_load":
            logger.info("Loading the abitrary numbers used for initial display")

            #set TreatmentOptions to the first treatment
            self.TreatmentOptions.set(self.TREATMENTLIST[0])
            #set BatchOptions to the first batch
            self.BatchOptions.set(self.BATCHLIST[0])

            self.param_display()
            return
        
        if load_type == "refresh":
            logger.info("Refreshing the parameters display")
            batch_num = self.BatchOptions.get().split()[1]
            current_treatment_char = self.get_treatment_char()

            self.param_display(batch_num=batch_num,
                               treatment_char=current_treatment_char)
            return
        
        self.save_parameters(mode = "previous")
        logger.debug("Saved the previous parameters")

        batch_num = self.BatchOptions.get().split()[1]
        logger.debug(f"Batch DropDown: {self.PREVIOUS_BATCH} -> {batch_num}")
        
        treatment = self.TreatmentOptions.get() #OK - just for log
        logger.debug(f"treatment DropDown: {self.PREVIOUS_TREATMENT} -> {treatment}")
        # convert treatment_index to letter 1 -> A
        current_treatment_char = self.get_treatment_char()

        self.param_display(batch_num = batch_num, 
                           treatment_char = current_treatment_char)


    def refresh_projects_detail(self):
        
        logger.debug("Refresh projects detail")

        # Clear existing project details labels
        self.project_detail_container.clear()

        # Reload the project details
        self.project_detail_container.load_project_details(self.CURRENT_PROJECT)



    def create_project(self):

        logger.debug("Create project button pressed")

        self.PROJECT_CREATED = False
        ProjectsInputWindow = InputWindow(self, project_name = "", project_created=False)

        self.CURRENT_PROJECT = ProjectsInputWindow.CURRENT_PROJECT
        self.PROJECT_CREATED = ProjectsInputWindow.PROJECT_CREATED

        if self.PROJECT_CREATED:

            self.refresh_projects()
            # select the newly created project in the list
            self.scrollable_frame.select_project(self.CURRENT_PROJECT)

            self.save_project()

            self.load_project(custom_project=self.CURRENT_PROJECT)

        else:
            print("Project not created")



    def load_project(self, custom_project=None):

        logger.debug("Load project button pressed")

        if custom_project == None:
            selected_project = self.scrollable_frame.get_selected_project()
        else:
            selected_project = custom_project
            # set the current project to the custom project
            self.scrollable_frame.set_selected_project(custom_project)

        self.CURRENT_PROJECT = selected_project

        logger.info(f"Current project: {self.CURRENT_PROJECT}")

        # Update the batch options
        self.BATCHLIST, ErrorType = self.access_history("load batch list")
        if ErrorType != None:
            tkinter.messagebox.showerror("Error", ErrorType)
            return
        
        
        self.BatchOptions.configure(values=self.BATCHLIST)

        retry = 0 
        while retry<3:
            try:
                self.TREATMENTLIST, ErrorType = self.access_history("load treatment list", batch_name = self.BatchOptions.get())
                logger.debug("Loaded treatment list")
                logger.debug(f"Possible warning: {ErrorType}")
                break
            except:
                logger.warning(f"Batch {self.BatchOptions.get()} does not exist in this project, try another batch")
                self.BatchOptions.set(self.BATCHLIST[0])
                retry += 1
                logger.debug(f"Retried {retry} times")
        else:
            logger.error("Failed to load treatment list, please check the project directory")
            tkinter.messagebox.showerror("Error", "Failed to load treatment list, please check the project directory")
            return

        if ErrorType != None:
            tkinter.messagebox.showerror("Error", ErrorType)
            return
        
        #set values of TreatmentOptions
        self.TreatmentOptions.configure(values=self.TREATMENTLIST)
        #set current value to first choice
        self.TreatmentOptions.set(self.TREATMENTLIST[0])

        self.refresh_projects_detail()

        self.update_param_display(load_type = "first_load")



    def save_project(self, batch_num = 1, subsequent_save = False):
        logger.info(f"Save project {self.CURRENT_PROJECT}")

        if not subsequent_save:
            save_dir = tkinter.filedialog.askdirectory()
            save_dir = Path(save_dir)
            project_dir = save_dir / self.CURRENT_PROJECT
        else:
            project_dir = Path(THE_HISTORY.get_project_dir(self.CURRENT_PROJECT))

        treatment_info, _ = self.access_history(command_type = "load treatment list", 
                                             batch_name = f"Batch {batch_num}")

        CreateProject(project_dir, treatment_info = treatment_info, batch_num = batch_num)

        with open(HISTORY_PATH, "r") as file:
            projects_data = json.load(file)
        
        # save the directory of the project to the projects_data
        projects_data[self.CURRENT_PROJECT]["DIRECTORY"] = str(project_dir)

        with open(HISTORY_PATH, "w") as file:
            json.dump(projects_data, file, indent=4)



    def delete_project(self):

        # create confirmation box
        choice = tkinter.messagebox.askquestion("Delete Project", "Are you sure you want to delete this project?")
        if choice == "no":
            return

        # Get the selected project
        selected_project = self.scrollable_frame.get_selected_project()

        if selected_project == "":
            tkinter.messagebox.showerror("Error", "Please select a project")
            return

        # Delete the project from the history file
        with open(HISTORY_PATH, "r") as file:
            projects_data = json.load(file)

        # Delete the project directory
        try:
            project_dir = projects_data[selected_project]["DIRECTORY"]
            shutil.rmtree(project_dir)
            logger.info("Deleted project directory: ", project_dir)
        except:
            logger.debug("Project directory does not exist: , just remove from History")

        del projects_data[selected_project]

        with open(HISTORY_PATH, "w") as file:
            json.dump(projects_data, file, indent=4)

        self.CURRENT_PROJECT = ""

        logger.info("Set current project to blank")

        # Refresh the project list
        logger.debug("Refresh projects")
        self.refresh_projects()

        # Refresh the project details
        self.refresh_projects_detail()



    def refresh_projects(self):
        logger.debug("Refresh projects")

        # Clear existing project labels
        self.scrollable_frame.clear_projects()

        # Read the projects.json file and add project names to the list
        try:
            with open(HISTORY_PATH, "r") as file:
                projects_data = json.load(file)
        except:
            print("No projects found or no record of projects")
            return

        for project_name in projects_data.keys():
            self.scrollable_frame.add_project(project_name)


    def import_trajectories(self):
        logger.debug("Start importing trajectories")

        import_project_dir = tkinter.filedialog.askdirectory()
        if not import_project_dir:
            logger.debug("No directory selected")
            return
        
        importer = Importer(import_project_dir = import_project_dir,
                            target_project_dir=THE_HISTORY.get_project_dir(self.CURRENT_PROJECT),
                            trajectories_format="trajectories_nogaps.txt")
        
        importer.import_trajectories()

        treatments_to_be_added = importer.new_treatments 
        
        for treatment_info in treatments_to_be_added:
            # _info = {
            #     "char": treatment_char,
            #     "name": self.import_treatment_names[treatment_char],
            #     "batch_num": batch_num
            # }
            treatment_char = treatment_info['char']
            treatment_name = treatment_info['name']
            batch_num = treatment_info['batch_num']

            substance, dose, unit = substance_dose_unit_finder(treatment_name)

            #update the projects.json
            THE_HISTORY.add_treatment(project_name = self.CURRENT_PROJECT,
                                    batch_name = f"Batch {batch_num}",
                                    treatment_char = treatment_char,
                                    substance = substance,
                                    dose = dose,
                                    dose_unit = unit)


        

    def pre_analyze_check(self):
        logger.debug("Start pre-analyze check")

        if self.CURRENT_PROJECT == "":
            tkinter.messagebox.showerror("Error", "Please select a project")
            return False

        if self.BatchOptions.get() == "":
            tkinter.messagebox.showerror("Error", "Please select a batch")
            return False
        
        if self.TreatmentOptions.get() == "":
            tkinter.messagebox.showerror("Error", "Please select a treatment")
            return False
        
        return True

    def analyze_treatment(self, PROGRESS_WINDOW, treatment_char = None):

        if self.CURRENT_PROJECT == "":
            tkinter.messagebox.showerror("Error", "Please select a project")
            return
        
        project_dir = Path(THE_HISTORY.get_project_dir(self.CURRENT_PROJECT))

        try:
            batch_num = int(self.get_batch_num())
        except ValueError:
            batch_num = 1

        if treatment_char == None:
            treatment_char = self.get_treatment_char()
        else:
            treatment_char = treatment_char

        logger.info(f"Start analyzing treatment: {treatment_char}")

        static_path = get_static_dir(project_dir, batch_num, treatment_char)

        #######################################################################

        EXECUTOR = Executor(project_dir=project_dir, 
                            batch_num=batch_num, 
                            treatment_char=treatment_char, 
                            EndPointsAnalyze=self.EPA,
                            progress_window=PROGRESS_WINDOW)
        
        #######################################################################
        PROGRESS_WINDOW.lift()
        PROGRESS_WINDOW.step_update(0, text = "Loading parameters...")
        
        while True:
            ERROR = EXECUTOR.PARAMS_LOADING()
            if ERROR == None:
                logger.debug("Parameters loaded successfully")
                break
            else:
                tkinter.messagebox.showerror("ERROR", ERROR)
                logger.error(ERROR)
                PROGRESS_WINDOW.destroy()
                return
            
        time.sleep(1)
        #######################################################################

        PROGRESS_WINDOW.step_update(30, text = "Loading trajectories...")

        EXECUTOR.TRAJECTORIES_LOADING(corr_type = self.corr_type)

        logger.debug("Trajectories loaded successfully")

        time.sleep(1)

        #######################################################################

        PROGRESS_WINDOW.step_update(60, text = "Analyzing...")
        # Lift the window to the front

        OVERWRITE = False
        while True:
            PROGRESS_WINDOW.lift()
            REPORT, EPA_path = EXECUTOR.ENDPOINTS_ANALYSIS(OVERWRITE=OVERWRITE, AV_interval=50)
            if REPORT == "Completed":
                logger.debug("Analysis completed successfully")

                # replace the current value of self.parameters_frame.entries['CORR TYPE'] with self.corr_type_optionmenu.get()
                self.parameters_frame.entries['CORR TYPE'].delete(0, 'end')
                self.parameters_frame.entries['CORR TYPE'].insert(0, self.corr_type_optionmenu.get())
                # save the current parameters
                self.save_parameters(mode='current')
                
                break
            elif REPORT == "Existed":
                choice = tkinter.messagebox.askyesno("Error",  f"Sheet name {treatment_char} existed.\nDo you want to overwrite? Y/N?")
                if choice:
                    logger.debug("User chose to overwrite")
                    OVERWRITE = True
                else:
                    logger.debug("User chose not to overwrite")
                    return EPA_path, static_path
            elif REPORT == "Skip":
                _message = f"Skip analysis of {treatment_char}"
                tkinter.messagebox.showinfo(REPORT, _message)
                logger.debug(_message)
                return EPA_path, static_path
            
        PROGRESS_WINDOW.step_update(100, text = "Completed")

        #######################################################################

        return EPA_path, static_path

    def analyze_project(self):

        PROGRESS_WINDOW = ProgressWindow(self)

        time00 = time.time()
        time0 = time.time()

        time_for_treatment = {}

        TREATMENT_LIST_CHAR = [self.treatment_to_treatment_char(treatment) for treatment in self.TREATMENTLIST]

        for i, treatment_char in enumerate(TREATMENT_LIST_CHAR):
            _message = f"Analyzing treatment {treatment_char}"
            _progress = (i+1) / len(TREATMENT_LIST_CHAR) * 100
            PROGRESS_WINDOW.group_update(_progress, text = _message)
            logger.info(_message)

            # set TreatmentOptions to the analyzing treatment
            self.TreatmentOptions.set(self.TREATMENTLIST[i])
            # apply changes to the parameters
            self.refresh()

            # ANALYZE TREATMENT
            EPA_path, _ = self.analyze_treatment(PROGRESS_WINDOW, treatment_char=treatment_char)

            time_for_treatment[treatment_char] = time.time() - time0
            time0 = time.time()

        # Destroy the progress window
        logger.debug("Destroying the progress window")
        PROGRESS_WINDOW.destroy()

        _message = f"Time taken: {round(time.time() - time00, 2)} seconds"
        _message += f"\nTime taken for each treatment:"
        for treatment_char in TREATMENT_LIST_CHAR:
            _message += f"\n  {treatment_char}: {round(time_for_treatment[treatment_char], 2)} seconds"
        tkinter.messagebox.showinfo("Completion time", _message)

        # # set value of self.parameters_frame.entries['CORR TYPE'] to corr_type_optionmenu
        # self.parameters_frame.entries['CORR TYPE'].insert(0, self.corr_type_optionmenu.get())
        # # save the current parameters
        # self.save_parameters(mode='current')

        logger.debug("EPA_path is not None")
        if EPA_path.exists():
            logger.debug("EPA_path exists")
            open_path = EPA_path.parent
            _ = CustomDialog(self, title = "Analysis Complete",
                                message =  "Click GO button to go to the saved directory of EndPoints.xlsx", 
                                button_text = "GO",
                                button_command = lambda : open_explorer(path=open_path))
            logger.info("Analysis complete")
        else:
            logger.debug("EPA_path does not exist")
            message = "Something went wrong during the analysis, no exported EndPoints.xlsx found"
            tkinter.messagebox.showerror("Error", message)
            logger.info(message)


    def analyze_project_THREADED(self):
        logger.debug("Open a new thread to analyze project")

        # save the current parameters
        self.save_parameters(mode='current')

        self.EPA = True        

        analyze_thread = threading.Thread(target=self.analyze_project)
        analyze_thread.start()


    def export_trajectories(self):

        PROGRESS_WINDOW = ProgressWindow(self)
        
        _, static_path = self.analyze_treatment(PROGRESS_WINDOW)

        _ = CustomDialog(self, title = "Trajectories Exported",
                                message =  "All 3D trajectories, normalized to pixel and cm are exported.\nClick GO button to go to the saved directory", 
                                button_text = "GO",
                                button_command = lambda : open_explorer(path=static_path))
        logger.info("Analysis skipped, only trajectories are loaded and saved")


    def export_trajectories_THREADED(self):
        logger.debug("Open a new thread to export trajectories project")

        self.EPA = False

        analyze_thread = threading.Thread(target=self.export_trajectories)
        analyze_thread.start()


    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        logger.debug(f"New UI appearance mode: {new_appearance_mode}")

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        logger.debug(f"New UI scaling: {new_scaling_float}")
        customtkinter.set_widget_scaling(new_scaling_float)

    
    def close_app(self):
        self.quit()


if __name__ == "__main__":
    app = App()
    app.mainloop()