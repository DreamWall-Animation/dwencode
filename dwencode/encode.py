"""
FFmpeg python wrapper to encode image sequence to movie with overlay text.
"""

__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import shlex
import datetime
import subprocess


def conform_path(font_path):
    r"""Unix path with escaped semicolon (e.g. 'C\:/WINDOWS/fonts/font.ttf')"""
    if font_path is None:
        return
    return font_path.replace('\\', '/').replace(':', r'\:')


def get_image_format(image_path):
    try:
        from PIL import Image
    except ImportError:
        raise Exception(
            'Install Pillow (PIL) or specify source_width and source_height.')
    with Image.open(image_path) as image:
        return image.size


def get_padding_values(width, height, target_width, target_height):
    scale_x = float(target_width) / width
    scale_y = float(target_height) / height
    scale = min(scale_x, scale_y)
    if scale_x <= scale_y:
        image_width = target_width
        image_height = round(height * scale)
        x_offset = 0
        y_offset = round((target_height - image_height) / 2)
    elif scale_x > scale_y:
        # black bars on the side instead of top/bottom:
        image_width = round(width * scale)
        x_offset = round((target_width - image_width) / 2)
        y_offset = 0
    return image_width, x_offset, y_offset


def drawtext(text, x, y, color, font_path=None, size=36, start=None, end=None):
    if text == '{framerange}':
        print(9, color)
        return draw_framerange(text, x, y, color, font_path, size, start, end)
    color = color or 'white'
    text = text.replace(':', r'\:')
    text = text.replace('{frame}', '%{frame_num}')
    timetag = datetime.datetime.now().strftime(r'%Y/%m/%d %H\:%M')
    text = text.replace('{datetime}', timetag)
    args = [
        None if font_path is None else "fontfile='%s'" % font_path,
        "text='%s'" % text,
        "x=%s" % x,
        "y=%s" % y,
        "start_number=%i" % start,
        "fontcolor=%s" % color,
        "fontsize=%i" % size,
    ]
    args = ':'.join([a for a in args if a])
    return "drawtext=%s" % args


def draw_framerange(
        text, x, y, color, font_path=None, size=36, start=None, end=None):
    # framerange is made of two separate texts:
    left_text, right_text = '{frame}', '[%i-%i]' % (start, end)
    x = str(x)
    if '/2' in x:
        # middle
        left_x = '%s-(tw/2)-3' % x
        right_x = '%s+(tw/2)+3' % x
    elif 'w-' in x.replace('tw-', ''):
        # right
        x = x.replace('tw', 'tw/2')
        # ffmpeg doesnt allow to align text on another text. Offset
        # position by a fixed amount:
        left_x = '%s-%i-(tw/2)-3' % (x, size * 6)
        right_x = '%s-%i+(tw/2)+3' % (x, size * 6)
    else:
        # left
        left_x = '%s+%i-(tw)-3' % (x, size * 3)
        right_x = '%s+%i+3' % (x, size * 3)
    return ','.join((
        drawtext(left_text, left_x, y, color, font_path, size, start),
        drawtext(right_text, right_x, y, color, font_path, size, start)
    ))


def drawbox(x, y, width, height, color, opacity, thickness):
    return 'drawbox=x=%s:y=%s:w=%s:h=%s:color=%s@%s:t=%s' % (
        x, y, width, height, color, opacity, thickness)


def drawimage(path, x, y):
    return '[0:v][1:v]overlay=%i:%i' % (x, y)


def encode(
        images_path,
        output_path,
        start=None,
        end=None,
        frame_rate=None,
        sound_path=None,
        sound_offset=None,
        source_width=None,
        source_height=None,
        target_width=None,
        target_height=None,
        top_left=None,
        top_middle=None,
        top_right=None,
        bottom_left=None,
        bottom_middle=None,
        bottom_right=None,
        top_left_color=None,
        top_middle_color=None,
        top_right_color=None,
        bottom_left_color=None,
        bottom_middle_color=None,
        bottom_right_color=None,
        font_path=None,
        overlay_image=None,
        rectangles=None,
        video_codec=None,
        audio_codec=None,
        add_silent_audio=False,
        silence_settings=None,
        ffmpeg_path=None,
        metadata=None,
        overwrite=False):
    """
    Encode images to movie with text overlays (using ffmpeg).
    """
    frame_rate = frame_rate or 24
    start = start or 0

    font_path = conform_path(font_path)
    if source_width and source_height:
        width, height = source_width, source_height
    else:
        width, height = get_image_format(images_path % start)
    target_width = target_width or width
    target_height = target_height or height

    # Input
    cmd = ffmpeg_path or 'ffmpeg'
    cmd += ' -framerate %i -start_number %i' % (frame_rate, start)
    cmd += ' -i "%s"' % images_path

    # Overlay inputs:
    if overlay_image:
        cmd += ' -i "%s"' % overlay_image['path']

    # Sound
    if sound_path:
        if sound_offset:
            cmd += ' -itsoffset %f' % sound_offset
        cmd += ' -i "%s"' % sound_path
    elif add_silent_audio:
        # Add empty sound in case of concatenate with "-c:a copy"
        silence_settings = silence_settings or 'anullsrc=cl=mono:r=48000'
        cmd += ' -f lavfi -i ' + silence_settings

    # Start filter complex
    filter_complex = []

    # Add overlay images
    if overlay_image:
        filter_complex.append(drawimage(**overlay_image))

    # Scaling and padding
    image_width, x_offset, y_offset = get_padding_values(
        width, height, target_width, target_height)
    filter_complex.append('scale=%i:-1' % image_width)
    filter_complex.append('pad=%i:%i:%i:%i' % (
        target_width, target_height, x_offset, y_offset))

    # Overlay text
    font_size = round(target_width / 53.0)
    margin_size = left_pos = top_pos = round(target_width / 240.0)
    right_pos = 'w-%i-(tw)' % margin_size
    bottom_pos = target_height - font_size - margin_size
    middle_pos = '(w-tw)/2'

    args = dict(font_path=font_path, size=font_size, start=start, end=end)
    filter_complex.append(drawtext(
        top_left, left_pos, top_pos, top_left_color, **args))
    filter_complex.append(drawtext(
        top_middle, middle_pos, top_pos, top_middle_color, **args))
    filter_complex.append(drawtext(
        top_right, right_pos, top_pos, top_right_color, **args))
    filter_complex.append(drawtext(
        bottom_left, top_pos, bottom_pos, bottom_left_color, **args))
    filter_complex.append(drawtext(
        bottom_middle, middle_pos, bottom_pos, bottom_middle_color, **args))
    filter_complex.append(drawtext(
        bottom_right, right_pos, bottom_pos, bottom_right_color, **args))

    # Add boxes (rectangles/safe-frames)
    for rectangle in rectangles or []:
        filter_complex.append(drawbox(**rectangle))

    # Format filter complex
    cmd += ' -filter_complex "%s"' % ','.join(filter_complex)

    # Metadata
    for key, value in metadata or []:
        cmd += ' -metadata %s="%s"' % (key, value)

    # Force duration to video length (in case audio is longer)
    duration = (end - start + 1) / float(frame_rate)
    cmd += ' -t %s' % duration

    # Video codec
    if not video_codec:
        cmd += ' -pix_fmt yuvj420p -vcodec mjpeg -q:v 3'
    else:
        if not video_codec.startswith(' '):
            video_codec = ' ' + video_codec
        cmd += video_codec

    # Sound
    if audio_codec and sound_path:
        cmd += ' -c:a ' + audio_codec
    else:
        if sound_path:
            cmd += ' -c:a copy'
        if add_silent_audio:
            cmd += ' -c:a pcm_s16le'

    # Output
    if overwrite:
        cmd += ' -y'
    cmd += ' "%s"' % output_path

    # Launch ffmpeg
    print(cmd)
    if os.name == 'nt':
        cmd = shlex.split(cmd)
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if proc.returncode != 0:
        print(out)
        raise Exception(err)


if __name__ == '__main__':
    directory = '~'
    if os.name == 'nt':
        directory = 'd:/_tmp'
    output_path = directory + '/encode_test.mov'
    images_path = (
        directory + '/playblast_example/dwencode_playblast_scene.%04d.jpg')
    focal = 'f:%.1fmm' % 35
    metadata = (
        ('author', 'John Doe'),
        ('title', 'seq10_sh...'))
    username = 'John Doe'
    site = 'DreamWall'
    version = 'proj_ep010_sq120_sh0170_spline_v002_tk001'

    start = 15
    end = 60
    target_width = 1920 / 1.5
    target_height = 1200 / 1.5
    rectangle1 = dict(
        x=int(target_width * .1),
        y=int(target_height * .1),
        width=int(target_width * .8),
        height=int(target_height * .8),
        color='#FFEE55',
        opacity=.2,
        thickness=2)
    rectangle2 = dict(
        x=int(target_width * .15),
        y=int(target_height * .15),
        width=int(target_width * .7),
        height=int(target_height * .7),
        color='#909090',
        opacity=.3,
        thickness=1)
    image = dict(path=directory + '/dw_transp.png', x=10, y=10)

    encode(
        images_path=images_path,
        start=15,
        end=60,
        output_path=output_path,
        target_width=target_width,
        target_height=target_height,
        top_left='{datetime}',
        top_middle=version,
        top_middle_color='#FFEE55',
        top_right=site,
        bottom_left=focal,
        bottom_middle='{framerange}',
        bottom_right='username',
        font_path=directory + '/luxisr_0.ttf',
        rectangles=[rectangle1, rectangle2],
        overlay_image=image,
        video_codec='-c:v libx264 -profile:v baseline -level 3.0',
        metadata=metadata,
        overwrite=True)

    os.startfile(output_path)
