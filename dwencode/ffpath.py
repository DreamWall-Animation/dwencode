import os
import logging
import subprocess
from functools import lru_cache


CREATE_NO_WINDOW = 0x08000000


@lru_cache()
def get_ffmpeg_executable_path(name='ffmpeg', path=None):
    executable_name = f'{name}.exe' if os.name == 'nt' else name
    if path and os.path.isdir(path):
        path = f'{path}/{executable_name}'
    if path and not os.path.exists(path):
        logging.warning(f'"{path}" does not exist.')
    path = path or name
    try:
        subprocess.check_call(
            f'{path} -version', creationflags=CREATE_NO_WINDOW)
    except subprocess.CalledProcessError:
        raise Exception(f'"{name}" not found.')
    return path


def get_ffmpeg_path(path=None):
    return get_ffmpeg_executable_path('ffmpeg', path)


def get_ffprobe_path(path=None):
    return get_ffmpeg_executable_path('ffprobe', path)
