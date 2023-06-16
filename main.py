import tkinter
import tkinter.messagebox
import tkinter.ttk as ttk
import customtkinter

import json
from pathlib import Path
import shutil
import os
import logging
import pandas as pd
from colorlog import ColoredFormatter

import threading

from Libs.misc import *
from Libs.customwidgets import *

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

############################################### SETUP GLOBAL VARIABLES ################################################

ROOT = Path(__file__).parent
ORI_HYP_PATH = ROOT / "Bin"
HISTORY_PATH = "History/projects.json"

########################################### SETUP LOGGING CONFIGURATION ###############################################
logger = logging.getLogger(__name__)
Path('Log').mkdir(parents=True, exist_ok=True)
log_file = 'Log/log.txt'

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

class App(customtkinter.CTk):

    def __init__(self):

        super().__init__()

        # PREDEFINED VARIABLES
        self.PROJECT_CREATED = False
        self.CURRENT_PROJECT = ""
        # self.CURRENT_PARAMS = {}
        self.PREVIOUS_BATCH = ""
        self.PREVIOUS_CONDITION = ""
        self.PREVIOUS_DIFFERENCE = 0
        self.CONDITIONLIST = ["Treatment A", "Treatment B", "Treatment C"]

        # configure window
        APP_TITLE = "Locomotion Analyzer 3D"
        self.title(APP_TITLE)
        self.geometry(f"{1500}x{790}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=0) 
        self.grid_columnconfigure((2, 3), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        ### COLUMN 0 ###

        button_config = {"font": ('Helvetica', 16), "width": 150, "height": 40}

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text=APP_TITLE, font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10))
        
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, 
                                                        text="Create Project", 
                                                        command=self.create_project
                                                        )
        self.sidebar_button_1.configure(**button_config)
        self.sidebar_button_1.grid(row=1, column=0, columnspan=2, padx=20, pady=20)

        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, 
                                                        text="Load Project", 
                                                        command=self.load_project
                                                        )
        self.sidebar_button_2.configure(**button_config)
        self.sidebar_button_2.grid(row=2, column=0, columnspan=2, padx=20, pady=20)

        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, 
                                                        text="Delete Project", 
                                                        command=self.delete_project
                                                        )
        self.sidebar_button_3.configure(**button_config)
        self.sidebar_button_3.grid(row=3, column=0, columnspan=2, padx=20, pady=20)

        # self.batch_label = customtkinter.CTkLabel(self.sidebar_frame, text="Batch Number", font=customtkinter.CTkFont(size=16))
        # self.batch_label.grid(row=4, column=0, padx=5, pady=5)
        # self.batch_entry = customtkinter.CTkEntry(self.sidebar_frame, width=50, height=10)
        # self.batch_entry.grid(row=4, column=1, padx=5, pady=5)
        # # set default value = 1
        # self.batch_entry.insert(0, "1")

        self.ImportVideoButton = customtkinter.CTkButton(self.sidebar_frame, 
                                                         text="Import Video",
                                                         command=self.import_video
                                                         )
        self.ImportVideoButton.configure(**button_config)
        self.ImportVideoButton.grid(row=4, column=0, columnspan = 2, padx=20, pady=20)

        # self.sidebar_button_4 = customtkinter.CTkButton(self.sidebar_frame, 
        #                                                 text="Import Trajectories", 
        #                                                 command=self.import_trajectories
        #                                                 )
        # self.sidebar_button_4.configure(**button_config)
        # self.sidebar_button_4.grid(row=5, column=0, columnspan=2, padx=20, pady=20)

        self.sidebar_button_5 = customtkinter.CTkButton(self.sidebar_frame, 
                                                        text="Analyze", 
                                                        command=self.analyze_project_THREADED
                                                        )
        self.sidebar_button_5.configure(**button_config)
        self.sidebar_button_5.grid(row=6, column=0, columnspan=2, padx=20, pady=20)


        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, columnspan=2, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, 
                                                                       values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        
        self.appearance_mode_optionemenu.grid(row=8, column=0, columnspan=2, padx=20, pady=(10, 10))
        
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=9, column=0, columnspan=2, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, 
                                                               values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=10, column=0, columnspan=2, padx=20, pady=(10, 20))

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
        project_previews_label.grid(row=0, column=0)

        # Bottom part
        bottom_part = customtkinter.CTkFrame(container_1)
        bottom_part.grid(row=1, column=0, sticky="nsew")

        bottom_part.grid_rowconfigure(0, weight=1)
        bottom_part.grid_rowconfigure(1, weight=0)

        self.scrollable_frame = ScrollableProjectList(bottom_part)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")

        refresh_button = customtkinter.CTkButton(bottom_part, text="Refresh", command=self.refresh_projects)
        refresh_button.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        # Initial refresh to populate the list
        self.refresh_projects()

        self.project_detail_container = ProjectDetailFrame(self, self.CURRENT_PROJECT, width = 400)
        self.project_detail_container.grid(row=1, column = 1, columnspan=3, padx=20, pady=20, sticky="nsew")

        # ### COLUMN 2 ###

        # # Create a canvas to hold the project parameters
        # container_2 = customtkinter.CTkFrame(self, width = 400)
        # container_2.grid(row=0, column=2, columnspan = 2, padx=(20, 0), pady=(20, 0), sticky="nsew")

        # # ROW 0
        # # Top part is a dropdown menu to select type of test
        # container_2_top = customtkinter.CTkFrame(container_2)
        # container_2_top.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # Header = customtkinter.CTkLabel(container_2_top, text="Loaded Project:", anchor="w", font=customtkinter.CTkFont(size=15, weight="bold"))
        # Header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        # self.LoadedProject = customtkinter.CTkLabel(container_2_top, text="None", anchor="w", font=customtkinter.CTkFont(size=20, weight="bold"))
        # self.LoadedProject.grid(row=0, column=1, columnspan=2, padx=20, pady=(20, 10), sticky="nsew")

        # # ROW 1
        # self.BATCHLIST = ["Batch 1"]

        # self.container_2_mid = customtkinter.CTkFrame(container_2)
        # self.container_2_mid.grid(row=1, column=0, columnspan=3, sticky="nsew")

        
        # self.BatchOptions = customtkinter.CTkOptionMenu(self.container_2_mid, dynamic_resizing=False,
        #                                                 width = 105, values=self.BATCHLIST)
        # self.BatchOptions.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

        # self.BatchAddButton = customtkinter.CTkButton(self.container_2_mid, text="Add Batch", width = 40,
        #                                                 command=self.add_batch)
        # self.BatchAddButton.grid(row=0, column=1, padx=20, pady=(20, 10), sticky="nsew")

        # self.BatchRemoveButton = customtkinter.CTkButton(self.container_2_mid, text="Remove Batch", width = 40,
        #                                                 command=self.remove_batch)
        # self.BatchRemoveButton.grid(row=0, column=2, padx=20, pady=(20, 10), sticky="nsew")
        
        # self.TestOptions = customtkinter.CTkOptionMenu(self.container_2_mid, dynamic_resizing=False, 
        #                                           width=210, values=self.TESTLIST)
        # self.TestOptions.grid(row=1, column=0, columnspan = 2, padx=20, pady=(20, 10), sticky="nsew")

        # self.save_button = customtkinter.CTkButton(self.container_2_mid, text="Save", width = 50,
        #                                            command=self.save_parameters)
        # self.save_button.grid(row=1, column=2, padx=20, pady=20, sticky="nsew")

        # self.TreatmentOptions = customtkinter.CTkOptionMenu(self.container_2_mid, dynamic_resizing=False,
        #                                                         width=210, values=self.CONDITIONLIST)
        # self.TreatmentOptions.grid(row=2, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="nsew")

        # self.parameters_frame = Parameters(self.container_2_mid, self.CURRENT_PROJECT, self.TESTLIST[0], 0)
        # self.parameters_frame.grid(row=3, columnspan=3, padx=20, pady=20, sticky="nsew")

        # # Row 2
        # container_2_bot = customtkinter.CTkFrame(container_2)
        # container_2_bot.grid(row=2, column=0, columnspan=3, sticky="nsew")

        # # create a Cloner button to copy current treatment's parameters to other treatment
        # self.Cloner = customtkinter.CTkButton(container_2_bot, text="Copy to other treatment", width = 50,
        #                                       command=self.copy_to_other_treatment)
        # self.Cloner.grid(row=1, column=0, pady=20, padx=20, sticky="nsew")

        # self.ClonerToolTip = tkinter.Button(container_2_bot, text="?")
        # self.ClonerToolTip.grid(row=1, column=1, pady=20, padx=20)
        # CreateToolTip(self.ClonerToolTip, text = 'Copy all parameters setting above and on the right-side columns\n'
        #          'to other Treatment and save them immediately\n'
        # )

        # self.CheckIntegrity = customtkinter.CTkButton(container_2_bot, text="Trajectories Check", width = 50,
        #                                         command=self.trajectories_check)
        # self.CheckIntegrity.grid(row=1, column=2, pady=20, padx=20)


        # ### COLUMN 3+ ###

        # # ROW 0 #

        # container_3 = customtkinter.CTkScrollableFrame(self, width = 500)
        # container_3.grid(row=0, rowspan=2, column=5, columnspan = 2, padx=(20, 0), pady=(20, 0), sticky="nsew")

        # self.nested_key_1_header = customtkinter.CTkLabel(container_3, text="None", anchor="w", font=customtkinter.CTkFont(size=20, weight="bold"))
        # self.nested_key_1_header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        # self.nested_key_1_frame = Parameters(container_3, self.CURRENT_PROJECT, self.TESTLIST[0], 1)
        # self.nested_key_1_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="nsew")

        # self.nk_add_button = NK_button(container_3, text="Add", width = 20,
        #                                 row = 2, column = 0,
        #                                 command=self.nk_add)
        # self.nk_remove_button = NK_button(container_3, text="Remove", width = 20,
        #                                 row = 2, column = 1,
        #                                 command=self.nk_remove)

        # self.nested_key_2_header = customtkinter.CTkLabel(container_3, text="None", anchor="w", font=customtkinter.CTkFont(size=20, weight="bold"))
        # self.nested_key_2_header.grid(row=0, column=2, padx=20, pady=(20, 10), sticky="nsew")
        # self.nested_key_2_frame = Parameters(container_3, self.CURRENT_PROJECT, self.TESTLIST[0], 2)
        # self.nested_key_2_frame.grid(row=1, column=2, columnspan = 2, padx=20, pady=(10, 20), sticky="nsew")

        # # self.nk2_add_button = NK_button(container_3, text="Add", width = 20,
        # #                                 row = 2, column = 2,
        # #                                 command=self.nk2_add)
        # # self.nk2_remove_button = NK_button(container_3, text="Remove", width = 20,
        # #                                 row = 2, column = 3,
        # #                                 command=self.nk2_remove)

        # # Config
        # self.BatchOptions.configure(command=self.update_param_display)
        # self.TestOptions.configure(command=self.update_param_display)
        # self.TreatmentOptions.configure(command=self.update_param_display)

        # # Load the first test by default
        # self.update_param_display(load_type = "first_load")




    def create_project(self):
        pass

    def load_project(self):
        pass

    def save_project(self):
        pass

    def delete_project(self):
        pass

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

    def import_video(self):
        pass

    def analyze_project_THREADED(self):
        pass


    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        logger.debug(f"New UI appearance mode: {new_appearance_mode}")

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        logger.debug(f"New UI scaling: {new_scaling_float}")
        customtkinter.set_widget_scaling(new_scaling_float)

if __name__ == "__main__":
    app = App()
    app.mainloop()