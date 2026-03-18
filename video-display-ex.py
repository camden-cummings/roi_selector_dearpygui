""""""
import os
import argparse

import cv2
import dearpygui.dearpygui as dpg

from roi_selector_dearpygui.interfaces.helpers import get_shape
from roi_selector_dearpygui.video_gui import VideoGUI

def find_all_videos_for_tracking(path=None, dates=None, exts=["avi"]):
    """
    Finds all avi files in current working directory, if path given finds all
    avi files in path that aren't output of the algorithm.

    :param path:
    :param ext:
    :return:
    """

    if path is None:
        path = os.getcwd()

    files_to_read = []
    for ex in os.walk(path):
        for fn in ex[2]:
            fn_ext = fn.split('.')[-1]

            if fn_ext in exts:
                if dates is None:
                    files_to_read.append(ex[0] + "/" + fn)
                else:
                    for d in dates:
                        if d in fn:
                            files_to_read.append(ex[0] + "/" + fn)
                            break

    return files_to_read

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--video_fp",
        action='store',
        type=str,
        required=True
    )

    args = parser.parse_args()
    video_fp = args.video_fp

    if os.path.isdir(video_fp):
        all_files = find_all_videos_for_tracking(video_fp, exts=["avi", "mp4"])
    else:
        all_files = [video_fp]
    print("Running on list of videos:", all_files)

    for filename in all_files:
        dpg.create_context()

        ext = filename.split('.')[-1]
        ext = "." + ext
        vidcap = None

        if cv2.imread(filename) is None:
            vidcap = cv2.VideoCapture(filename)

            frame_width = int(vidcap.get(3))
            frame_height = int(vidcap.get(4))
        else:
            curr_img = cv2.imread(filename)
            shape = curr_img.shape
            frame_width, frame_height = get_shape(shape)

        if frame_width == 0 or frame_height == 0:
            print("Video does not exist, or is formatted incorrectly.")
        else:
            window = dpg.add_window(label="Video player", pos=(50, 50), width=frame_width, height=frame_height)

            m = VideoGUI(window, frame_width, frame_height, filename)

            m.start(window)

        dpg.destroy_context()

