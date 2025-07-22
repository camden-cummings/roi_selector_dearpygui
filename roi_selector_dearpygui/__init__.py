import lazy_loader


__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules={
        'gui',
        'roi_generation',
        'statemanager',
        'video_gui',
    },
    submod_attrs={
        'gui': [
            'GUI',
        ],
        'roi_generation': [
            'generate_rois',
            'trim',
        ],
        'statemanager': [
            'StateManager',
        ],
        'video_gui': [
            'VideoGUI',
        ],
    },
)

__all__ = ['GUI', 'StateManager', 'VideoGUI', 'generate_rois', 'gui',
           'roi_generation', 'statemanager', 'trim', 'video_gui']

