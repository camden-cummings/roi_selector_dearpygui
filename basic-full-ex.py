""""""
import dearpygui.dearpygui as dpg
import numpy as np

from roi_selector_dearpygui.gui import GUI

dpg.create_context()

frame_width = 500
frame_height = 500

raw_data = np.zeros((frame_height, frame_width, 3), dtype=np.int32)

window = dpg.add_window(label="Video player", pos=(50, 50), width=frame_width, height=frame_height)
m = GUI(window, frame_width, frame_height)

with dpg.theme(), dpg.theme_component():
    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)

with dpg.texture_registry(show=False):
    dpg.add_raw_texture(frame_width, frame_height, raw_data,
                        format=dpg.mvFormat_Float_rgb, tag="texture_tag")

dpg.add_image("texture_tag", pos=[8, 8], parent=window)

dpg.set_primary_window(window, True)

dpg.create_viewport(width=int(1.5*frame_width), height=int(1.5*frame_height), title="ROI Selector")

dpg.setup_dearpygui()
dpg.show_viewport()

while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()
    
dpg.destroy_context()