__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import shlex
import subprocess as sp


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


def _create_list_file(paths, root, index=0):
    rel_paths = '\n'.join(['file ' + p.replace(root, '.') for p in paths])
    list_path = os.path.join(
        root, 'temp_video_concatenation_list_%i.txt' % index).replace(
            '\\', '/')
    if os.path.exists(list_path):
        os.remove(list_path)
    with open(list_path, 'w') as f:
        f.write(rel_paths)
    return list_path


def _get_input_args(paths, stack_orientation='horizontal'):
    input_pattern = '-f concat -safe 0 -i %s '
    if isinstance(paths[0], list):
        common_root = _get_common_root(
            [path for sublist in paths for path in sublist])
        args = ' '
        lists_paths = []
        for i, stack in enumerate(paths):
            list_path = _create_list_file(stack, common_root, i)
            lists_paths.append(list_path)
            args += input_pattern % list_path
        if stack_orientation in ('horizontal', 0):
            # stackarg = 'hstack'  # not working with movies of different sizes
            stackarg = (
                "color=d=0.1[c];[c][0]scale2ref[c][v1];"
                "[c][1]scale2ref='w=main_w+iw:h=max(main_h,ih)'[c][v2];"
                "[c][v1]overlay=0:0[ol-vid1];"
                "[ol-vid1][v2]overlay=W-w:0,setsar=1")
        else:
            # stackarg = 'vstack'  # not working with movies of different sizes
            stackarg = (
                "color=d=0.1[c];[c][0]scale2ref[c][v1];"
                "[c][1]scale2ref='w=max(main_w,iw):h=main_h+ih'[c][v2];"
                "[c][v1]overlay=0:0[ol-vid1];"
                "[ol-vid1][v2]overlay=0:H-h,setsar=1")
        args += '-filter_complex "%s" ' % stackarg
        return lists_paths, args, common_root
    else:
        common_root = _get_common_root(paths)
        list_path = _create_list_file(paths, common_root)
        args = input_pattern % list_path
        return [list_path], args, common_root


def concatenate_videos(
        paths, output_path, verbose=False, ffmpeg_path=None, delete_list=True,
        ffmpeg_codec='-vcodec copy -c:a copy', stack_orientation='horizontal'):
    """
    Movies are expected to have:
    - a common parent directory
    - same format
    @paths argument can be a list or a list of lists. If there is multiple
    lists, it will encode them side by side (or on top of each other,
    depending on the @stack_orientation argument).
    """
    ffmpeg = ffmpeg_path or 'ffmpeg'
    list_paths, input_args, common_root = _get_input_args(
        paths, stack_orientation)
    cmd = '%s %s %s %s' % (ffmpeg, input_args, ffmpeg_codec, output_path)
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
