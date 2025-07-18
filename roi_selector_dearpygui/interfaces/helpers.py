import dearpygui.dearpygui as dpg

#TODO: DECIDE IF make both inherited functions

def get_mouse_pos(shift: tuple[int, int]) -> tuple[int, int]:
    """Shifts mouse position by shift to allow canvas to be put anywhere in a window."""
    x, y = dpg.get_mouse_pos()

    return x+shift[0], y+shift[1]

def convert_to_in_bounds(point: tuple[int, int], frame_width: int, frame_height: int, shift: tuple[int, int]) -> list[int]:
    """Return a point that is in bounds based on given point."""
    return [max(min(frame_width+shift[0], point[0]), 0), max(min(frame_height+shift[1], point[1]), 0)]

def update_frame_shape(obj, new_frame_width: int, new_frame_height: int):
    """Changes object's frame shape to given values."""
    obj.frame_width = new_frame_width
    obj.frame_height = new_frame_height

def get_shape(shape):
    return shape[1], shape[0]