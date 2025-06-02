"""
"""
import math
import pickle

import dearpygui.dearpygui as dpg
import numpy as np
from shapely.geometry import Point, Polygon

from helpers import get_mouse_pos
from roipoly import RoiPoly


class ROIInterface:
    """Defines useful methods for interacting with (moving, rotating) polygons."""

    def __init__(self, window, frame_width, frame_height, shift=(0, 0)):
        self.rois = []
        self.selected_polygon = None
        self.selected_polygon_vert = None
        self.prev = None
        self.drag_polygon = None
        self.dragging_points = False
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.window = window
        self.allowed_area_min = 0.0
        self.allowed_area_max = self.frame_width*self.frame_height
        self.shift = shift

    def left_mouse_press_callback(self):
        """When mouse clicked, checks if current mouse position is near to a polygon or a polygon vertex."""
        x, y = get_mouse_pos(self.shift)

        if self.drag_polygon is None and self.selected_polygon_vert is None:
            self.check_for_selection((x, y))

    def left_mouse_release_callback(self):
        """Reset all because mouse is no longer down."""
        self.drag_polygon = None

        if self.selected_polygon is not None:
            self.adjust_points_to_in_bounds(self.selected_polygon)
            self.selected_polygon_vert = None
            self.selected_polygon = None
        self.prev = None

    def roi_slider_size_callback_min(self, _, allowed_area):
        """Shows or hides ROIs based on value of allowed area."""
        self.allowed_area_min = allowed_area

        for roi in self.rois:
            if roi.area < allowed_area or roi.area > self.allowed_area_max:
                dpg.hide_item(roi.poly)
            else:
                dpg.show_item(roi.poly)

    def roi_slider_size_callback_max(self, _, allowed_area):
        """Shows or hides ROIs based on value of allowed area."""
        self.allowed_area_max = allowed_area

        for roi in self.rois:
            if roi.area > allowed_area or roi.area < self.allowed_area_min:
                dpg.hide_item(roi.poly)
            else:
                dpg.show_item(roi.poly)

    def motion_notify_callback(self):
        """When mouse moving, if drag polygon, moves, if selected polygon vertex, rotates."""
        x, y = get_mouse_pos(self.shift)

        if self.dragging_points and self.selected_polygon is not None:
            self.drag_points((x,y))
        else:
            if self.drag_polygon is not None:
                self.move()
            elif self.selected_polygon is not None:
                centr = Polygon(self.selected_polygon.lines).centroid

                mouse_pos_on_circle = self.find_future_pos((x, y), (centr.x, centr.y))
                theta = math.atan2(
                    mouse_pos_on_circle[1]-centr.y, mouse_pos_on_circle[0]-centr.x)

                if self.prev is not None:
                    self.rotate(self.prev - theta)

                self.prev = theta

    def toggle_point_drag_callback(self, _, __):
        self.dragging_points = not self.dragging_points

    def save_rois_callback(self, _, app_data: dict):
        """Saves all ROIs to a file."""
        with open(app_data["file_path_name"], 'wb') as filename:
            allowed_rois = []

            for roi in self.rois:
                if self.allowed_area_max > roi.area > self.allowed_area_min:
                    allowed_rois.append(roi)

            lines = self.convert_rois_to_np_array(allowed_rois)
            pickle.dump(lines, filename)

    def load_rois_callback(self, _, app_data: dict):
        """Loads all ROIs into current canvas."""
        with open(app_data["file_path_name"], 'rb') as filename:
            lines = pickle.load(filename)

        self.convert_np_array_to_rois(lines)

    def check_for_selection(self, mouse_pos):
        """Check if mouse down on poly or poly vertex."""

        closest = ()
        mouse_pt = Point(mouse_pos)

        for poly in self.rois:
            n_poly = Polygon(poly.lines)

            if mouse_pt.within(n_poly):
                self.drag_polygon = poly

            for point in poly.lines:
                dist = math.dist(point, mouse_pos)

                if dist < 40:  # if
                    if closest:
                        if dist < closest[1]:
                            closest = ((poly, point), dist)
                    else:
                        closest = ((poly, point), dist)

        if closest:
            self.selected_polygon = closest[0][0]
            self.selected_polygon_vert = closest[0][1]

    def check_for_hover(self):
        """Check if mouse hovering over poly or poly vertex."""
        mouse_pos = get_mouse_pos(self.shift)
        for roi in self.rois:
            mouse_pt = Point(mouse_pos)
            n_poly = Polygon(roi.lines)

            if mouse_pt.within(n_poly):
                return roi
        return None

    def copy(self):
        """Copy hovered ROI."""
        roi = self.check_for_hover()

        if roi is not None:
            new_roi = RoiPoly(self.window, self.frame_width,
                              self.frame_height, lines=roi.lines)
            self.rois.append(new_roi)

    def delete(self):
        """Delete hovered ROI."""
        roi = self.check_for_hover()

        if roi is not None:
            dpg.delete_item(roi.poly)
            self.rois.remove(roi)

    def move(self):
        """Move polygon to current mouse position."""
        x, y = get_mouse_pos(self.shift)
        poly = self.drag_polygon.lines
        centr = Polygon(poly).centroid

        translated_poly = [[p[0] - centr.x + x, p[1] - centr.y + y]
                           for p in poly]

        for point in translated_poly:
            if point[0] > self.shift[0]+self.frame_width or self.shift[0] > point[0]:
                break
            elif point[1] > self.shift[1]+self.frame_height or self.shift[1] > point[1]:
                break
        else:
            self.drag_polygon.lines = translated_poly
            dpg.configure_item(self.drag_polygon.poly,
                               points=self.drag_polygon.lines)

    def rotate(self, angle):
        """Rotate polygon to angle."""
        poly = self.selected_polygon.lines
        centr = Polygon(poly).centroid

        rot_matrix = np.array([[math.cos(angle), -math.sin(angle)],
                      [math.sin(angle), math.cos(angle)]])
        rotated_poly = np.array([(p[0]-centr.x, p[1]-centr.y) for p in poly]).dot(
            rot_matrix) + [(centr.x, centr.y) for _ in range(len(poly))]

        rotated_poly = rotated_poly.tolist()

        self.selected_polygon.lines = rotated_poly
        dpg.configure_item(self.selected_polygon.poly,
                           points=self.selected_polygon.lines)

    def adjust_points_to_in_bounds(self, polygon):
        """Naive algorithm to move points back inside bounds of frame."""
        num_of_points = len(polygon.lines)
        for point in polygon.lines:
            adj_x, adj_y = 0, 0

            if point[0] > self.shift[0] + self.frame_width:
                adj_x = self.shift[0] + self.frame_width - point[0]
            elif self.shift[0] > point[0]:
                adj_x = self.shift[0] + abs(point[0])

            if point[1] > self.shift[1] + self.frame_height:
                adj_y = self.shift[1] + self.frame_height - point[1]
            elif self.shift[1] > point[1]:
                adj_y = self.shift[1] + abs(point[1])

            for i in range(num_of_points):
                polygon.lines[i][0] += adj_x
                polygon.lines[i][1] += adj_y

            dpg.configure_item(polygon.poly,
                               points=polygon.lines)

    def convert_rois_to_np_array(self, rois):
        """Converts all ROIPolys to numpy arrays."""
        lines = []
        for roi in rois:
            l = roi.lines
            poly = []

            for point in l:
                poly.append([point[0]-self.shift[0], point[1]-self.shift[1]])

            lines.append(poly)
        return lines

    def convert_np_array_to_rois(self, lines):
        """Converts numpy arrays to ROIPolys."""
        new_rois = []
        for line in lines:
            poly_lines = []

            for point in line:
                poly_lines.append(
                    [point[0]+self.shift[0], point[1]+self.shift[1]])

            new_rois.append(
                RoiPoly(self.window, self.frame_width, self.frame_height, self.shift, poly_lines))

        self.rois.extend(new_rois)

    def drag_points(self, mouse_pos):
        ind = self.selected_polygon.lines.index(self.selected_polygon_vert)

        # not the most elegant or efficient way to do this (keeping track of index would be better), but it means array of lines in roipoly can be rearranged without issue
        self.selected_polygon.lines[ind] = mouse_pos
        self.selected_polygon_vert = mouse_pos

        dpg.configure_item(self.selected_polygon.poly, points=self.selected_polygon.lines)

    def find_future_pos(self, cursor_pos: tuple[int, int], centr: tuple[float, float]) -> tuple[float, float]:
        """
        Intermediate calculations for finding the next point the shape will
        be rotated to on the circle of positions that the currently selected
        point could go to.

        Parameters
        ----------
        cursor_pos : current mouse position
        centr : center of the polygon being rotated

        Returns
        -------
        future_v : future position on the circle of the selected vertex


        """

        # find closest point on the circle of potential vertex positions
        curr_v = (cursor_pos[0]-centr[0], cursor_pos[1]-centr[1])
        curr_mag_v = math.sqrt(
            curr_v[0]*curr_v[0] + curr_v[1]*curr_v[1])
        radius = math.dist(centr, self.selected_polygon_vert)
        future_v = (centr[0] + curr_v[0] / curr_mag_v * radius,
                    centr[1] + curr_v[1] / curr_mag_v * radius)

        return future_v