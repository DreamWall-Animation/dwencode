import os
import time
import json
import locale
import subprocess as sp
from dwencode.ffpath import get_ffprobe_path


CREATE_NO_WINDOW = 0x08000000


def probe(vid_file_path, ffprobe_path=None):
    ffprobe_path = get_ffprobe_path(ffprobe_path)
    command = [
        ffprobe_path, '-loglevel', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', vid_file_path]
    proc = sp.Popen(
        command, stdout=sp.PIPE, stderr=sp.STDOUT,
        cwd=os.path.expanduser('~'),  # fix for Windows msg about UNC paths
        creationflags=CREATE_NO_WINDOW)
    out = proc.communicate()[0].decode(locale.getpreferredencoding())
    try:
        return json.loads(out)
    except ValueError:
        print('Could not load output as json: \n%s' % out)
        raise


def get_video_duration(video_path, frames=False, ffprobe_path=None):
    data = probe(video_path, ffprobe_path)
    vid_stream = [s for s in data['streams'] if 'nb_frames' in s][0]
    if frames:
        return int(vid_stream['nb_frames'])
    return float(vid_stream['duration'])


def get_audio_duration(video_path, ffprobe_path=None):
    data = probe(video_path, ffprobe_path)
    stream = [s for s in data['streams'] if s['codec_type'] == 'audio'][0]
    return float(stream['duration'])


def get_format(vid_file_path, ffprobe_path=None):
    ffprobe_path = get_ffprobe_path(ffprobe_path)
    data = probe(vid_file_path, ffprobe_path)
    vid_stream = [s for s in data['streams'] if 'coded_width' in s][0]
    return vid_stream['coded_width'], vid_stream['coded_height']


def _get_formats(vid_file_paths, ffprobe_path):
    processes = dict()
    for path in vid_file_paths:
        command = [
            ffprobe_path, '-loglevel', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', path]
        p = sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
        processes[path] = p

    formats = dict()
    for path, p in processes.items():
        try:
            data = json.loads(p.communicate()[0])
            vid_stream = [s for s in data['streams'] if 'coded_width' in s][0]
            format_ = vid_stream['coded_width'], vid_stream['coded_height']
            formats[path] = format_
        except BaseException:
            formats[path] = (0, 0)

    return formats


def _chunks(list_, chunk_size):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(list_), chunk_size):
        yield list_[i:i + chunk_size]


def get_formats(vid_file_paths, chunk_size=64, ffprobe_path=None):
    # Cannot open infinite number of files at the same time, so cut the list
    # into pieces:
    ffprobe_path = get_ffprobe_path(ffprobe_path)
    start_time = time.time()
    formats = dict()
    count = len(vid_file_paths)
    for i, paths_chunk in enumerate(_chunks(vid_file_paths, chunk_size)):
        print('Getting movies formats: %i/%i' % ((i + 1) * chunk_size, count))
        formats.update(_get_formats(paths_chunk, ffprobe_path=ffprobe_path))
    print(time.time() - start_time)
    return formats


def get_streams_durations(file_path, ffprobe_path=None):
    data = probe(file_path, ffprobe_path)
    if len(data['streams']) != 2:
        raise ValueError('This only handles one video and one audio stream.')
    durations = {s['codec_type']: s['duration'] for s in data['streams']}
    if len(durations) != 2:
        raise ValueError('This only handles one video and one audio stream.')
    return durations


def are_streams_of_same_duration(file_path, ffprobe_path=None):
    durations = get_streams_durations(file_path, ffprobe_path)
    return durations['video'] == durations['audio']


def is_audio_shorter_than_video(file_path, ffprobe_path=None):
    durations = get_streams_durations(file_path, ffprobe_path)
    return durations['video'] > durations['audio']
