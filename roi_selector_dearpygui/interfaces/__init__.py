import lazy_loader


__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules={
        'helpers',
        'lineinterface',
        'roiinterface',
        'roipoly',
    },
    submod_attrs={
        'helpers': [
            'convert_to_in_bounds',
            'get_mouse_pos',
            'get_shape',
            'update_frame_shape',
        ],
        'lineinterface': [
            'LineInterface',
        ],
        'roiinterface': [
            'ROIInterface',
        ],
        'roipoly': [
            'RoiPoly',
        ],
    },
)

__all__ = ['LineInterface', 'ROIInterface', 'RoiPoly', 'convert_to_in_bounds',
           'get_mouse_pos', 'get_shape', 'helpers', 'lineinterface',
           'roiinterface', 'roipoly', 'update_frame_shape']

