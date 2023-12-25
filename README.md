# __F3LA__ 
# __Fish 3D Locomotion Analyzer__

![alt text](https://github.com/ThangLC304/SpiderID_APP/blob/main/bin/support/universities.png?raw=true)


# __Authorship__

## __Author:__

Luong Cao Thang  
PhD candidate, I-Shou University, Kaohsiung, Taiwan.  
Email: [thang.luongcao@gmail.com](mailto:thang.luongcao@gmail.com)  


# Fish Locomotion Assay downstream analyzing application
F3LA is the new software we build to accelerate the analysis process of our 3D Locomotion Assay for zebrafish. It was designed to streamline and automate the arduous data management and organize the processes associated with raw data.

## INSTALLATION GUIDE

1. Download ```.zip``` file of the whole repository by click on ```Code``` button and select ```Download ZIP```

    <img src="https://github.com/ThangLC304/F3LA/blob/main/Bin/support/download_button.png" alt="image" width="450" height="auto">

    <!-- ![download_button](https://github.com/ThangLC304/F3LA/blob/main/Bin/support/download_button.png) -->

2. Unzip the file, within the App Folder, run the ```setup.bat``` (Run as Admistrator) file to install independencies

3. Run the program using ```run.bat```

## APP NAVIGATION

<img src="https://github.com/ThangLC304/F3LA/blob/main/Bin/support/app_screen.png" alt="image" width="450" height="auto">

<!-- ![App_Screen](https://github.com/ThangLC304/F3LA/blob/main/Bin/support/app_screen_with_num.png) -->


1. Create new Project from scratch using ```Create Project``` button

    <img src="https://github.com/ThangLC304/F3LA/blob/main/Bin/support/step01.png" alt="image" width="450" height="auto">

    <br>
    Example of a project detail
    <br>

    <img src="https://github.com/ThangLC304/F3LA/blob/main/Bin/support/create_project.png" alt="image" width="450" height="auto">


2. Copy recorded video files to desired locations for further analysis using tracker (in this example we used idTracker)

    <img src="https://github.com/ThangLC304/F3LA/blob/main/Bin/support/step02.png" alt="image" width="450" height="auto">


3. Select Project from available ones within the Project List -> ```Load Project```

    If a new project is loaded **[1]** (or Re-measure button **[2]** is pressed), you will be redirected to a Measurer window **[3]** to measure the core coordinates, which subsequently help the program to calculate the required parameters.

    <img src="https://github.com/ThangLC304/F3LA/blob/main/Bin/support/step03.png" alt="image" width="450" height="auto">


4. Within the Measurer window, load the image (as first frame of the video, you can create a reference image manually or select the video itself and the program will automatically extract the first frame of the video as reference image)

    <img src="https://github.com/ThangLC304/F3LA/blob/main/Bin/support/step04.png" alt="image" width="450" height="auto">


5. The loaded project is now fully equipped with functional parameters **[3]**. Run analysis on the Data of the current Batch (all treatments within it) using ```Analyze``` button **[4]**. The analysis process is displayed on the progress bars **[5]**.

    <img src="https://github.com/ThangLC304/F3LA/blob/main/Bin/support/step05.png" alt="image" width="450" height="auto">


6. The result will be saved as "EndPoints.xlsx" at the Batch directory (e.g., [project_name]/Batch 1/EndPoints.xlsx) <br>

    <img src="https://github.com/ThangLC304/F3LA/blob/main/Bin/support/step06.png" alt="image" width="450" height="auto">


    The following end-points are included: <br>

    - Total Distance (cm) <br>
    - Average Speed (cm/s) <br>
    - Total Absolute Turn Angle (degree) <br>
    - Average Angular Velocity (degree/s) <br>
    - Slow Angular Velocity Percentage (%) <br>
    - Fast Angular Velocity Percentage (%) <br>
    - Meandering (degree/m) <br>
    - Freezing Time (%) <br>
    - Swimming Time (%) <br>
    - Rapid Movement Time (%) <br>
    - Time spent in Top (cm) <br>
    - Time spent in Mid (%) <br>
    - Time spent in Bot (%) <br>
    - Shoaling Area (cm<sup>2</sup>) <br>
    - Shoaling Volume (cm<sup>3</sup>) <br>


7. Display Shoaling Formation in 3D space

    <img src="https://github.com/ThangLC304/F3LA/blob/main/Bin/support/shoaling_plot.png" alt="image" width="450" height="auto">

    **LEFT SIDE** is Shoaling formation in 3D space <br>

    **RIGHT SIDE** is Shoaling Volume plot


**<!!!>: Please refrain from changing the Project directory name**



## Regular questions:

1. What if I have changed the name of the directory name at the new location?

**A:** If there is no other folder with the name exactly like the old name of the project, when you use the ```Load Project``` button, the App will ask you to select the new location of the project so it can update within its memory. <br>
<br>
If you changed the name of the directory and then you created a new directory with the same exact name, the App will recognize the new empty folder as the valid path for the Project, hence not asking you for relocation -> Mismatching issue.

2. When I want to update the program, do I have to go to your GitHub Repository to download new version and replace the old one?

**A:** Fortunately no, you can use the ```updater.bat``` to check to update the app. Then check the Libs/\_\_about__.json to see if your version is up-to-date!

