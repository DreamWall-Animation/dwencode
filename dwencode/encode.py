"""
FFmpeg python wrapper to encode image sequence to movie with overlay text.
"""

__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import datetime
import shlex
import subprocess

from dwencode.ffpath import get_ffmpeg_path


def extract_image_from_video(video_path, time, output_path, ffmpegpath=None):
    ffmpeg = get_ffmpeg_path(path=ffmpegpath)
    subprocess.check_call(shlex.split(
        f'{ffmpeg} -ss {time} -i {video_path} -frames:v 1 -y {output_path}'))


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
    else:
        # black bars on the side instead of top/bottom:
        image_width = round(width * scale)
        x_offset = round((target_width - image_width) / 2)
        y_offset = 0
    return image_width, x_offset, y_offset


def drawtext(
        text, x, y, color=None, font_path=None, size=36, start=None, end=None):
    if text == '{framerange}':
        return draw_framerange(x, y, color, font_path, size, start, end)
    args = []
    if not color:
        # TODO: handle border colors options
        args.append('bordercolor=black@0.4:borderw=%s' % int(size / 18))
    color = color or 'white'
    text = text.replace(':', r'\:')
    text = text.replace('{frame}', '%{frame_num}')
    timetag = datetime.datetime.now().strftime(r'%Y/%m/%d %H\:%M')
    text = text.replace('{datetime}', timetag)
    args.extend([
        None if font_path is None else "fontfile='%s'" % font_path,
        "text='%s'" % text,
        "x=%s" % x,
        "y=%s" % y,
        "start_number=%i" % start,
        "fontcolor=%s" % color,
        "fontsize=%i" % size,
    ])
    args = ':'.join([a for a in args if a])
    return "drawtext=%s" % args


def draw_framerange(
        x, y, color, font_path=None, size=36, start=None, end=None):
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


def imagepos(x, y):
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
        crop=False,
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
        font_scale=1.0,
        overlay_image=None,
        rectangles=None,
        input_args=None,
        video_codec=None,
        audio_codec=None,
        add_silent_audio=False,
        silence_settings=None,
        ffmpeg_path=None,
        metadata=None,
        overwrite=False,
        verbose=False):
    """
    Encode images to movie with text overlays (using FFmpeg).

    - images_path (str) Use patterns such as "/path/to/image.%04d.jpg"
    - output_path (str) With any FFmpeg supported extensions
    - start (int) First frame. Default is 0
    - end (int) Last frame
    - frame_rate (float) Default is 24
    - sound_path (str) Optional
    - sound_offset (float) Default is 0
    - source_width (int) Optional if you have Pillow (PIL)
    - source_height (int) Optional if you have Pillow (PIL)
    - target_width (str) Different ratio than source will add black bars.
    - target_height (str) Different ratio than source will add black bars.
    - crop (bool) Crop the image if source is different than target
    - top_left (str) Text to display
    - top_middle (str) Text to display
    - top_right (str) Text to display
    - bottom_left (str) Text to display
    - bottom_middle (str) Text to display
    - bottom_right (str) Text to display
    - top_left_color (str) Text color. Format: #RRGGBB@A
    - top_middle_color (str) Text color. Format: #RRGGBB@A
    - top_right_color (str) Text color. Format: #RRGGBB@A
    - bottom_left_color (str) Text color. Format: #RRGGBB@A
    - bottom_middle_color (str) Text color. Format: #RRGGBB@A
    - bottom_right_color (str) Text color. Format: #RRGGBB@A
    - font_path (str) FFmpeg supported font for all texts
    - overlay_image (dict) needs {path, x, y}
    - rectangles (dicts) need {x,y,width,height,color,opacity,thickness}
    - video_codec (str) FFmpeg video codec arguments
    - audio_codec (str) FFmpeg audio codec arguments
    - add_silent_audio (str) add silent audio if no audio is provided
    - silence_settings (str) FFmpeg sound codec settings
    - ffmpeg_path (str) Default: searches for 'ffmpeg' in PATH env
    - metadata (str) Movie metadata
    - overwrite (str) Default is False

    You can use the following text expressions:
    - {frame}: current frame
    - {framerange}: current frame + first and last frame.
        e.g. `130 [40-153]`
    - {datetime}: date in YYYY/MM/DD HH:MM format.

    The default codec is `libx264` and can be used with `.mov`
    container.

    Image ratio is preserved. Input a different target ratio to add black bars.

    Font size is automatically adapted to target size.
    """
    # Check ffmpeg is found:
    ffmpeg_path = get_ffmpeg_path(ffmpeg_path)

    frame_rate = frame_rate or 24
    start = start or 0

    font_path = conform_path(font_path)
    if source_width and source_height:
        width, height = source_width, source_height
    else:
        width, height = get_image_format(images_path % start)
    target_width = target_width or width
    target_height = target_height or height

    # Command start
    cmd = ffmpeg_path or 'ffmpeg'
    if not verbose:
        cmd += ' -hide_banner -loglevel error -nostats'

    # Input
    cmd += ' -framerate %i -f image2 -start_number %i' % (frame_rate, start)
    if input_args:
        cmd += ' %s ' % input_args
    cmd += ' -i "%s"' % images_path

    # Overlay inputs
    if overlay_image:
        cmd += ' -i "%s"' % overlay_image['path']

    # Audio codec
    if audio_codec and (sound_path or add_silent_audio):
        audio_codec = ' ' + audio_codec
    elif sound_path:
        audio_codec = ' -c:a copy'
    else:
        audio_codec = ' '

    # Sound
    if sound_path:
        if sound_offset:
            cmd += ' -itsoffset %f' % sound_offset
        cmd += ' -i "%s"' % sound_path
        if end:
            duration = (end - start + 1) / frame_rate
            cmd += ' -t %s' % duration
        if '-c:a copy' not in audio_codec:
            cmd += ' -af apad -shortest'  # make sure audio is as long as vid
    elif add_silent_audio:
        # Add empty sound in case of concatenate with "-c:a copy"
        silence_settings = silence_settings or 'anullsrc=cl=mono:r=48000'
        cmd += ' -f lavfi -i %s -shortest' % silence_settings

    # Start filter complex
    filter_complex = []

    # Add overlay images
    if overlay_image:
        filter_complex.append(imagepos(overlay_image['x'], overlay_image['y']))

    # Scaling and padding
    image_width, x_offset, y_offset = get_padding_values(
        width, height, target_width, target_height)
    if not crop:
        filter_complex.append('scale=%i:-1' % image_width)
        filter_complex.append('pad=%i:%i:%i:%i' % (
            target_width, target_height, x_offset, y_offset))
    else:
        filter_complex.append(
            'crop=%i:%i:0:100' % (target_width, target_height))

    # Overlay text
    font_size = round(target_width / 53.0 * font_scale)
    margin_size = left_pos = top_pos = round(target_width / 240.0)
    right_pos = 'w-%i-(tw)' % margin_size
    bottom_pos = target_height - font_size - margin_size
    middle_pos = '(w-tw)/2'

    kwargs = dict(font_path=font_path, size=font_size, start=start, end=end)
    filters_args = (
        (top_left, left_pos, top_pos, top_left_color),
        (top_middle, middle_pos, top_pos, top_middle_color),
        (top_right, right_pos, top_pos, top_right_color),
        (bottom_left, top_pos, bottom_pos, bottom_left_color),
        (bottom_middle, middle_pos, bottom_pos, bottom_middle_color),
        (bottom_right, right_pos, bottom_pos, bottom_right_color))

    for text, left, top, color in filters_args:
        if not text:
            continue
        filter_complex.append(drawtext(text, left, top, color, **kwargs))

    # Add boxes (rectangles/safe-frames)
    for rectangle in rectangles or []:
        filter_complex.append(drawbox(**rectangle))

    # Format filter complex
    cmd += ' -filter_complex "%s"' % ','.join(filter_complex)

    # Metadata
    for key, value in metadata or []:
        cmd += ' -metadata %s="%s"' % (key, value)

    # Video codec
    if not video_codec:
        cmd += ' -vcodec libx264'
    else:
        if not video_codec.startswith(' '):
            video_codec = ' ' + video_codec
        cmd += video_codec

    # Sound
    cmd += audio_codec + ' -fflags +genpts'

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
