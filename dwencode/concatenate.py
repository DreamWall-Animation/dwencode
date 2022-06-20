__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import shlex
import subprocess as sp
from dwencode.ffpath import get_ffmpeg_path


DEFAULT_CONCAT_ENCODING = '-vcodec copy -c:a copy'
DEFAULT_CONCAT_STACK_ENCODING = (
    '-c:v libx264 -crf 26 -preset fast -tune animation -c:a aac -b:a 128k')
STACKED_ARGS = (
    "color=d=0.1[c];[c][0]scale2ref[c][v1];"
    "[c][1]scale2ref='{scale2ref}'[c][v2];"
    "[c][v1]overlay=0:0[ol-vid1];"
    "[ol-vid1][v2]overlay={overlay},setsar=1")


def _get_common_root(paths):
    paths = [os.path.normpath(p).replace('\\', '/') for p in paths]
    root = os.path.commonprefix(paths)
    if not root:
        raise Exception('Videos need to be on the same disk.')
    if not os.path.isdir(root):
        root = os.path.dirname(root)
    if root.endswith('/'):
        root = root[:-1]
    return root


def _get_videos_durations(paths):
    from dwencode.probe import get_duration
    durations = []
    for path in paths:
        try:
            durations.append(get_duration(path))
        except ValueError:
            print('ERROR: Could not get duration of %s' % path)
            raise
    return durations


def _create_list_file(paths, root, index=0, timings=None):
    concat_list = []
    for i, path in enumerate(paths):
        concat_list.append('file %s' % path.replace(root, '.'))
        if timings:
            timing = timings[i]
            concat_list.extend(
                ['duration %s' % timing, 'outpoint %s' % timing])
    concat_list = '\n'.join(concat_list)
    print(concat_list)
    list_path = os.path.join(
        root, 'temp_video_concatenation_list_%i.txt' % index).replace(
            '\\', '/')

    if os.path.exists(list_path):
        os.remove(list_path)
    with open(list_path, 'w') as f:
        f.write(concat_list)

    return list_path


def _get_input_args(
        paths, stack_orientation='horizontal', master_list_index=0):
    input_pattern = '-f concat -safe 0 -i %s '
    if not isinstance(paths[0], list):
        common_root = _get_common_root(paths)
        list_path = _create_list_file(paths, common_root)
        args = input_pattern % list_path
        return [list_path], args, common_root
    common_root = _get_common_root(
        [path for sublist in paths for path in sublist])
    args = ' '
    lists_paths = []
    timings = _get_videos_durations(paths[master_list_index])
    for i, stack in enumerate(paths):
        list_path = _create_list_file(stack, common_root, i, timings)
        lists_paths.append(list_path)
        args += input_pattern % list_path
    if stack_orientation in ('horizontal', 0):
        scale2ref = "w=main_w+iw:h=max(main_h,ih)"
        overlay = "W-w:0"
    else:
        scale2ref = "w=max(main_w,iw):h=main_h+ih"
        overlay = "0:H-h"
    stackarg = STACKED_ARGS.format(scale2ref=scale2ref, overlay=overlay)
    args += '-filter_complex "%s" ' % stackarg
    return lists_paths, args, common_root


def concatenate_videos(
        paths, output_path, verbose=False, ffmpeg_path=None, delete_list=True,
        ffmpeg_codec=DEFAULT_CONCAT_ENCODING, overwrite=False,
        stack_orientation='horizontal', stack_master_list=0):
    """
    Movies are expected to have:
    - a common parent directory
    - same format

    @paths argument can be a list or a list of lists. If there is multiple
    lists, it will encode them side by side (or on top of each other,
    depending on the @stack_orientation argument).

    @stack_master_list is the index of the list which will drive the timing
    of the concatenation.
    """
    ffmpeg = get_ffmpeg_path(ffmpeg_path)
    list_paths, input_args, common_root = _get_input_args(
        paths, stack_orientation, stack_master_list)
    overwrite = '-y' if overwrite else ''

    if isinstance(paths[0], list) and ffmpeg_codec == DEFAULT_CONCAT_ENCODING:
        # => obviously cannot stream copy
        ffmpeg_codec = DEFAULT_CONCAT_STACK_ENCODING

    cmd = '%s %s %s %s %s' % (
        ffmpeg, input_args, ffmpeg_codec, overwrite, output_path)

    print(cmd)
    cmd = shlex.split(cmd)

    try:
        if verbose:
            proc = sp.Popen(
                cmd, cwd=common_root, stdout=sp.PIPE, stderr=sp.PIPE)
            out, err = proc.communicate()
            print(out)
            print(err)
            if proc.returncode != 0:
                raise ValueError(err)
        else:
            sp.call(cmd, cwd=common_root)
    finally:
        if delete_list:
            for list_path in list_paths:
                os.remove(list_path)
