import subprocess
from dwencode.ffpath import get_ffmpeg_path


def create_thumbnail(
        source, output_path, width=256, height=144, time=0, overwrite=False):
    """
    source can be a video or an image.
    """
    cmd = [
        get_ffmpeg_path(),
        '-i', source, '-ss', str(time), '-frames:v', '1', '-vf',
        f'scale={width}:{height}']
    if overwrite:
        cmd.append('-y')
    cmd.append(output_path)
    subprocess.check_call(cmd)
