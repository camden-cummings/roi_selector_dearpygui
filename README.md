## About The Project

GUI for selection of ROIs using [DearPyGUI](https://github.com/hoffstadt/DearPyGui) and Python; can be overlayed on top of images, videos, or live camera feeds. Also defines methods for interacting with ROIs (i.e. dragging, rotating). 

<!-- ROI Selection -->

https://github.com/user-attachments/assets/a4717845-e8d7-4570-a40c-18c2082c44ed

<!-- Line Selection -->

Line interface is used to define a set of lines and create ROIs based on them, as shown.

https://github.com/user-attachments/assets/349db09e-6821-4589-9933-36cfc477c680


### Installation

1. Install necessary packages
   ```sh
   pip install requirements.txt
   ```
2. Clone the repo
   ```sh
   git clone https://github.com/camden-cummings/roi_selector_dearpygui
   ```

## Usage
For an example of what a full example without video looks like, please go to: basic-full-ex.py

For an example of what that would look like overlayed on a video: video-display-ex.py

And for an example overlayed onto a live camera: https://github.com/camden-cummings/zebrafish-tracker/gui_tracker.py

## Acknowledgments

* Originally developed in matplotlib as an extension of [this code](https://github.com/jdoepfert/roipoly.py). 
