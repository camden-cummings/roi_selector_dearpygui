import math
import pickle

import dearpygui.dearpygui as dpg
import numpy as np
from shapely.geometry import Point, Polygon
import cv2

from .helpers import get_mouse_pos
from .roipoly import RoiPoly


class ROIInterface:
    """Defines useful methods for interacting with (moving, rotating) polygons."""

    def __init__(self, window, frame_width: int, frame_height: int, shift=(0, 0)):
        """

        :param window:
        :param frame_width:
        :param frame_height:
        :param shift:
        """
        self.rois = []
        self.selected_polygon = None
        self.selected_polygon_vert = None
        self.prev = None
        self.drag_polygon = None
        self.dragging_points = False
        self.window = window
        self.allowed_area_min = 0.0
        self.shift = shift

        self.frame_width = frame_width
        self.frame_height = frame_height

        self.allowed_area_max = self.frame_width*self.frame_height

        self.hypotenuse = math.sqrt(
            math.pow(self.frame_width, 2) + math.pow(self.frame_height, 2))

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

    def roi_slider_size_callback_min(self, _, allowed_area: int):
        """Shows or hides ROIs based on value of allowed area."""
        self.allowed_area_min = allowed_area

        for roi in self.rois:
            if roi.area < allowed_area or roi.area > self.allowed_area_max:
                dpg.hide_item(roi.poly)
            else:
                dpg.show_item(roi.poly)

    def roi_slider_size_callback_max(self, _, allowed_area: int):
        """Shows or hides ROIs based on value of allowed area."""
        self.allowed_area_max = allowed_area

        for roi in self.rois:
            if roi.area > allowed_area or roi.area < self.allowed_area_min:
                dpg.hide_item(roi.poly)
            else:
                dpg.show_item(roi.poly)

    def motion_notify_callback(self):
        """When mouse moving, if drag_polygon, moves polygon by center, if selected_polygon_vertex, rotates."""
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
        """Toggles allowing individual points on polygons to be dragged or not dragged."""
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

    def check_for_selection(self, mouse_pos: tuple[float, float]):
        """Check if mouse down on poly or poly vertex."""
        closest = ()
        mouse_pt = Point(mouse_pos)

        for poly in self.rois:
            for point in poly.lines:
                dist = math.dist(point, mouse_pos)

                if dist < self.hypotenuse/50:  # if
                    if closest:
                        if dist < closest[1]:
                            closest = ((poly, point), dist)
                    else:
                        closest = ((poly, point), dist)

            if not closest:
                n_poly = Polygon(poly.lines)

                if mouse_pt.within(n_poly):
                    self.drag_polygon = poly

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

    def copy_callback(self):
        """Copy hovered ROI."""
        roi = self.check_for_hover()

        if roi is not None:
            new_roi = RoiPoly(self.window, self.frame_width,
                              self.frame_height, lines=roi.lines)
            self.rois.append(new_roi)

    def delete_callback(self):
        """Delete hovered ROI."""
        roi = self.check_for_hover()

        if roi is not None:
            dpg.delete_item(roi.poly)
            self.rois.remove(roi)

    def up_callback(self):
        for roi in self.rois:
            roi.set_lines([[line[0], line[1]-int(self.hypotenuse/1000)] for line in roi.lines])

    def left_callback(self):
        for roi in self.rois:
            roi.set_lines([[line[0]-int(self.hypotenuse/1000), line[1]] for line in roi.lines])

    def down_callback(self):
        for roi in self.rois:
            roi.set_lines([[line[0], line[1]+int(self.hypotenuse/1000)] for line in roi.lines])

    def right_callback(self):
        for roi in self.rois:
            roi.set_lines([[line[0]+int(self.hypotenuse/1000), line[1]] for line in roi.lines])

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
            self.drag_polygon.set_lines(translated_poly)

    def rotate(self, angle: float):
        """Rotate polygon to angle."""
        poly = self.selected_polygon.lines
        centr = Polygon(poly).centroid

        rot_matrix = np.array([[math.cos(angle), -math.sin(angle)],
                      [math.sin(angle), math.cos(angle)]])
        rotated_poly = np.array([(p[0]-centr.x, p[1]-centr.y) for p in poly]).dot(
            rot_matrix) + [(centr.x, centr.y) for _ in range(len(poly))]

        rotated_poly = rotated_poly.tolist()

        self.selected_polygon.set_lines(rotated_poly)

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

    def convert_rois_to_np_array(self, rois: list[RoiPoly]):
        """Converts all ROIPolys to numpy arrays."""
        sorted_rois = []
        for roi in rois:
            l = roi.lines
            cx, cy = self.find_centroid_of_contour(np.array(l))
            sorted_rois.append([[cx, cy], l])

        # sorting ROIs by X and then Y position, means that if you have ROIs placed like:
        # A    B
        # C    D
        # the sorted order will be:
        # D 0, C 1, B 2, A 3

        sorted_rois.sort(key=lambda tup: tup[0][0])
        sorted_rois.sort(key=lambda tup: tup[0][1])

        lines = []
        for center, l in sorted_rois:
            print(center, l)
            poly = []
            for point in l:
                poly.append([point[0]-self.shift[0], point[1]-self.shift[1]])

            lines.append(poly)
        return lines

    @staticmethod
    def find_centroid_of_contour(contour):
        """Given a contour, finds centroid of it."""
        M = cv2.moments(contour)

        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        return cx, cy

    def convert_np_array_to_rois(self, lines: list[np.ndarray]):
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

    def make_rois_from_contours(self, contours: list[RoiPoly]):
        """Make an ROIPoly object for each contour in contours."""
        rois = []
        for i in range(len(contours)):
            n_l = [[int(j[0]+self.shift[0]), int(j[1]+self.shift[1])]
                   for j in contours[i]]
            roi = RoiPoly(self.window, self.frame_width,
                          self.frame_height, self.shift, lines=n_l)
            roi.finish_roi()
            rois.append(roi)
        return rois

    def drag_points(self, mouse_pos: tuple[int, int]):
        """Moves point being clicked on to mouse position."""
        ind = self.selected_polygon.lines.index(self.selected_polygon_vert)

        # not the most elegant or efficient way to do this (keeping track of index would be better),
        # but it means array of lines in roipoly can be rearranged without issue
        self.selected_polygon.lines[ind] = list(mouse_pos)
        self.selected_polygon_vert = list(mouse_pos)

        dpg.configure_item(self.selected_polygon.poly, points=self.selected_polygon.lines)

    def find_future_pos(self, cursor_pos: tuple[int, int], center: tuple[float, float]) -> tuple[float, float]:
        """
        If you rotate the clicked polygon vertex around the center of the polygon, you get a circle of
        potential positions the polygon could be rotated to. This function finds the closest point
        to the cursor position on that circle.
        """

        curr_v = (cursor_pos[0]-center[0], cursor_pos[1]-center[1])
        curr_mag_v = math.sqrt(
            curr_v[0]*curr_v[0] + curr_v[1]*curr_v[1])
        radius = math.dist(center, self.selected_polygon_vert)
        future_v = (center[0] + curr_v[0] / curr_mag_v * radius,
                    center[1] + curr_v[1] / curr_mag_v * radius)

        return future_v
