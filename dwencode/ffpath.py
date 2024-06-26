import os
from functools import lru_cache


CREATE_NO_WINDOW = 0x08000000


@lru_cache()
def get_ffmpeg_executable_path(name='ffmpeg', path=None):
    executable_name = f'{name}.exe' if os.name == 'nt' else name
    if path:
        if os.path.isdir(path):
            path = f'{path}/{executable_name}'.replace('\\', '/')
        if not os.path.exists(path):
            raise Exception(f'"{name}" not found.')
        return path
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            path = f'{path}/{executable_name}'.replace('\\', '/')
            if os.path.exists(path):
                return path
        raise Exception(f'"{name}" not found.')


def get_ffmpeg_path(path=None):
    return get_ffmpeg_executable_path('ffmpeg', path)


def get_ffprobe_path(path=None):
    return get_ffmpeg_executable_path('ffprobe', path)
