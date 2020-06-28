import time
import subprocess as sp
import json
import six
import quicktime


def probe(vid_file_path):
    '''
    From https://stackoverflow.com/a/36743499/1442895
    Give a json from ffprobe command line
    @vid_file_path : The absolute (full) path of the video file, string.
    '''
    command = [
        "ffprobe", "-loglevel", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", vid_file_path]
    shell = True if six.PY2 else False
    pipe = sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT, shell=shell)
    out = pipe.communicate()[0]
    if not six.PY2:
        out = out.decode('ascii')
    return json.loads(out)


def get_duration(vid_file_path):
    if vid_file_path.endswith('.mov'):
        return quicktime.get_duration(vid_file_path)
    else:
        data = probe(vid_file_path)
        vid_stream = [s for s in data['streams'] if 'nb_frames' in s][0]
        return int(vid_stream['nb_frames'])


def get_format(vid_file_path):
    data = probe(vid_file_path)
    vid_stream = [s for s in data['streams'] if 'coded_width' in s][0]
    return vid_stream['coded_width'], vid_stream['coded_height']


def _get_formats(vid_file_paths):
    processes = dict()
    for path in vid_file_paths:
        command = [
            "ffprobe", "-loglevel", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", path]
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


def chunks(list_, chunk_size):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(list_), chunk_size):
        yield list_[i:i + chunk_size]


def get_formats(vid_file_paths, chunk_size=64):
    # Cannot open infinite number of files at the same time, so cut the list
    # into pieces:
    start_time = time.time()
    formats = dict()
    count = len(vid_file_paths)
    for i, paths_chunk in enumerate(chunks(vid_file_paths, chunk_size)):
        print('Getting movies formats: %i/%i' % ((i + 1) * chunk_size, count))
        formats.update(_get_formats(paths_chunk))
    print(time.time() - start_time)
    return formats
