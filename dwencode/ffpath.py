import logging
import os
import subprocess


_ffmpeg_valid_path = None
_ffprobe_valid_path = None


def get_ffmpeg_path(ffmpeg_path=None):
    """
    Series of check up to lookup for a valid ffmpeg path. Cache the result to
    avoid those check each time.
    """
    global _ffmpeg_valid_path
    if _ffmpeg_valid_path:
        return _ffmpeg_valid_path
    if ffmpeg_path:
        if os.path.isdir(ffmpeg_path):
            ffmpeg_path += '/ffmpeg.exe'
        if not os.path.exists(ffmpeg_path):
            msg = '"%s" does not exist. Try with "ffmpeg" command.'
            logging.warning(msg % ffmpeg_path)

    ffmpeg_path = ffmpeg_path or "ffmpeg"
    try:
        subprocess.check_call('%s -version' % ffmpeg_path)
    except subprocess.CalledProcessError:
        raise Exception('FFmpeg not found.')

    _ffmpeg_valid_path = ffmpeg_path
    return _ffmpeg_valid_path


def get_ffprobe_path(ffprobe_path=None):
    """
    Same as 'get_ffmpeg_path' for ffprobe
    """
    global _ffprobe_valid_path
    if _ffprobe_valid_path:
        return _ffprobe_valid_path

    if ffprobe_path:
        if ffprobe_path.lower().endswith('ffmpeg.exe'):
            ffprobe_path = os.path.dirname(ffprobe_path)
        if os.path.isdir(ffprobe_path):
            ffprobe_path += '/ffprobe.exe'
    elif _ffmpeg_valid_path:
        ffprobe_path = os.path.dirname(_ffmpeg_valid_path)
        ffprobe_path += 'ffprobe.exe'

    if ffprobe_path and not os.path.exists(ffprobe_path):
        msg = '"%s" does not exist. Try with "ffprobe" command.'
        logging.warning(msg % ffprobe_path)

    ffprobe_path = ffprobe_path or "ffprobe"
    try:
        subprocess.check_call('%s -version' % ffprobe_path)
    except subprocess.CalledProcessError:
        raise Exception('FFmpeg not found.')

    _ffprobe_valid_path = ffprobe_path
    return _ffprobe_valid_path
