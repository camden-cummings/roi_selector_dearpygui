"""Redirects callbacks to appropriate class."""
import dearpygui.dearpygui as dpg

from .interfaces import ROIInterface, LineInterface, RoiPoly
from .roi_generation import generate_rois

class StateManager:
    def __init__(self, window, frame_width: int, frame_height: int, shift=(0, 0)):
        """

        :param window:
        :param frame_width:
        :param frame_height:
        :param shift:
        """
        self.inactive = True #TODO name this something more meaningful
        self.disable = False
        self.current_roi = None
        self.ROI_mode_selected = True
        self.ctrl_has_been_pressed = False
        
        self.frame_height = frame_height
        self.frame_width = frame_width

        self.roi_interface = ROIInterface(window, frame_width, frame_height, shift)
        self.line_interface = LineInterface(window, frame_width, frame_height, shift)

        self.shift = shift

        self.window = window

    def left_mouse_press_callback(self):
        """When left mouse pressed, sends to appropriate method."""
        if not self.disable:
            if self.inactive and len(self.roi_interface.rois) > 0 and self.ROI_mode_selected:
                # selecting completed ROIs
                self.roi_interface.left_mouse_press_callback()
            elif not self.ROI_mode_selected:
                # selecting lines
                self.line_interface.left_mouse_press_callback()
            elif not self.inactive:
                # there's an ROI that has not been completed,
                # so the left mouse press means a new vertex for the ROI
                self.current_roi.left_mouse_press_callback()

    def right_mouse_press_callback(self):
        """Finishes the currently unfinished ROI, if there is one. When completed, adds to list of current completed ROIs to be managed by ROI_interface."""
        if not self.disable:
            if not self.inactive:
                self.current_roi.right_mouse_press_callback()
    
                if self.current_roi.completed:
                    self.roi_interface.rois.append(self.current_roi)
                    self.inactive = True
                    self.current_roi = None

    def motion_notify_callback(self):
        """When mouse is moving."""
        if not self.disable:
            if self.inactive and self.ROI_mode_selected and len(self.roi_interface.rois) > 0:
                self.roi_interface.motion_notify_callback()
            elif not self.ROI_mode_selected:
                self.line_interface.motion_notify_callback()
            elif not self.inactive:
                self.current_roi.motion_notify_callback()

    def new_roi(self):
        """Starts new ROI which will only be completed when right mouse press event occurs."""
        if self.current_roi is not None and not self.current_roi.completed:
            dpg.configure_item(self.current_roi, points=[])

        self.current_roi = RoiPoly(
            self.window, self.frame_width, self.frame_height, self.shift)
        self.inactive = False

    def release_callback(self):
        """When mouse is released, send to either ROI or line interface based on mode."""
        if not self.disable:
            if self.inactive and len(self.roi_interface.rois) > 0 and self.ROI_mode_selected:
                self.roi_interface.left_mouse_release_callback()
            elif not self.ROI_mode_selected:
                self.line_interface.left_mouse_release_callback()

    def generate_rois_callback(self):
        """Creates list of ROIs based on lines."""
        shortened_contours = generate_rois(
            self.line_interface.lines, self.frame_height, self.frame_width, self.shift)

        for line in self.line_interface.lines:
            dpg.delete_item(line)

        self.line_interface.lines.clear()

        self.roi_interface.rois.extend(self.roi_interface.make_rois_from_contours(shortened_contours))
        self.ROI_mode_selected = True

    def clear_window(self):
        """Clears window of all ROIs and lines."""
        for line in self.line_interface.lines:
            dpg.delete_item(line)

        self.line_interface.lines.clear()

        for roi in self.roi_interface.rois:
            dpg.delete_item(roi.poly)

        self.roi_interface.rois.clear()
        self.ROI_mode_selected = False

    def copy_callback(self, _, __):
        """Callback from copy (ctrl+c) pressed, decides if a line or ROI should be copied."""
        if self.ROI_mode_selected and self.ctrl_has_been_pressed:
            self.roi_interface.copy_callback()
        else:
            self.line_interface.copy_callback()

        self.ctrl_has_been_pressed = False

    def control_callback(self, _, __):  # janky solution to key press check
        self.ctrl_has_been_pressed = True

    def delete_callback(self, _, __):
        """If delete button pressed, delete either hovered ROI or line, depending on mode."""
        if self.ROI_mode_selected:
            self.roi_interface.delete_callback()
        else:
            self.line_interface.delete_callback()

    def up_callback(self):
        """When up or W key pressed."""
        if self.ROI_mode_selected:
            self.roi_interface.up_callback()
        else:
            self.line_interface.up_callback()

    def left_callback(self):
        """When left or A key pressed."""
        if self.ROI_mode_selected:
            self.roi_interface.left_callback()
        else:
            self.line_interface.left_callback()

    def down_callback(self):
        """When down or D key pressed."""
        if self.ROI_mode_selected:
            self.roi_interface.down_callback()
        else:
            self.line_interface.down_callback()

    def right_callback(self):
        """When right or D key pressed."""
        if self.ROI_mode_selected:
            self.roi_interface.right_callback()
        else:
            self.line_interface.right_callback()