__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import shlex
import subprocess as sp


def concatenate_videos(
        paths, output_path, verbose=False, ffmpeg_path=None, delete_list=True,
        ffmpeg_codec='-vcodec copy -c:a copy'):
    """
    Movies are expected to have:
    - a common parent directory
    - same format
    """
    # Get common directory:
    paths = [os.path.normpath(p).replace('\\', '/') for p in paths]
    root = os.path.commonprefix(paths)
    if not root:
        raise Exception('Videos need to be on the same disk.')
    if not os.path.isdir(root):
        root = os.path.dirname(root)
    if root.endswith('/'):
        root = root[:-1]

    # Create file list of relative paths for ffmpeg
    rel_paths = '\n'.join(['file ' + p.replace(root, '.') for p in paths])
    list_path = os.path.join(
        root, 'temp_video_concatenation_list.txt').replace('\\', '/')
    if os.path.exists(list_path):
        os.remove(list_path)
    with open(list_path, 'w') as f:
        f.write(rel_paths)

    # FFmpeg command:
    try:
        cmd = '%s -f concat -safe 0 -i %s %s %s' % (
            ffmpeg_path or 'ffmpeg', list_path, ffmpeg_codec, output_path)
        print(cmd)
        cmd = shlex.split(cmd)
        workdir = os.path.dirname(list_path)
        if verbose:
            proc = sp.Popen(cmd, cwd=workdir, stdout=sp.PIPE, stderr=sp.PIPE)
            out, err = proc.communicate()
            print(out)
            print(err)
            if proc.returncode != 0:
                raise ValueError(err)
        else:
            sp.call(cmd, cwd=workdir)
    finally:
        if delete_list:
            os.remove(list_path)
