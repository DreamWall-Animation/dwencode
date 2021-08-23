__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import argparse
import encode


parser = argparse.ArgumentParser()

parser.add_argument('images_path', help='frame number: ####')
parser.add_argument('output_path')

parser.add_argument('-s', '--start', type=int)
parser.add_argument('-e', '--end', type=int)
parser.add_argument('-fps', '--framerate', type=int)

parser.add_argument('-a', '--sound-path', type=int)
parser.add_argument('-ao', '--sound-offset', type=float)

parser.add_argument('-sw', '--source-width', type=int)
parser.add_argument('-sh', '--source-height', type=int)
parser.add_argument('-tw', '--target-width', type=int)
parser.add_argument('-th', '--target-height', type=int)

parser.add_argument('-tl', '--top-left')
parser.add_argument('-tm', '--top-middle')
parser.add_argument('-tr', '--top-right')
parser.add_argument('-bl', '--bottom-left')
parser.add_argument('-bm', '--bottom-middle')
parser.add_argument('-br', '--bottom-right')

parser.add_argument('-tlc', '--top-left-color')
parser.add_argument('-tmc', '--top-middle-color')
parser.add_argument('-trc', '--top-right-color')
parser.add_argument('-blc', '--bottom-left-color')
parser.add_argument('-bmc', '--bottom-middle-color')
parser.add_argument('-brc', '--bottom-right-color')

parser.add_argument('-font', '--font-path')

parser.add_argument('-i', '--overlay-image', help='path-x-y')

parser.add_argument(
    '-box', '--rectangle', action='append',
    help='x-y-width-height-color-opacity-thickness')

parser.add_argument('-c:v', '--video-codec')
parser.add_argument('-c:a', '--audio-codec')
parser.add_argument('-as', '--add-silent-audio')
parser.add_argument('-ss', '--silence_settings')

parser.add_argument('-m', '--metadata', action='append', help='key:value')

parser.add_argument(
    '-ow', '--overwrite', default=False, action='store_true')

parser.add_argument('-ffp', '--ffmpeg-path')

args = parser.parse_args()

# Reformat some args:
images_path = args.images_path
for i in range(8, 0, -1):
    images_path = images_path.replace('#' * i, '%0{}d'.format(i))

rectangles = []
for rectangle in args.rectangle or []:
    try:
        rectangle = rectangle.split('-')
        rectangles.append(dict(
            x=round(float(rectangle[0])),
            y=round(float(rectangle[1])),
            width=round(float(rectangle[2])),
            height=round(float(rectangle[3])),
            color=rectangle[4],
            opacity=float(rectangle[5]),
            thickness=round(float(rectangle[6])),
        ))
    except BaseException as e:
        raise Exception('Wrong rectangle argument\n%s' % e)

if args.overlay_image:
    try:
        path, x, y = args.overlay_image.split('-')
        overlay_image = dict(path=path, x=int(x), y=int(y))
    except BaseException as e:
        raise Exception('Wrong image argument\n%s' % e)

metadata = []
for metadatum in args.metadata:
    if ':' not in metadatum:
        raise Exception(
            'Wrong metadata argument.'
            ' Use ":" separator between key and value')
    try:
        key, value = metadatum.split(':')
        1 / len(key)
        1 / len(value)
        metadata.append((key, value))
    except (ZeroDivisionError, ValueError) as e:
        raise Exception('Wrong metadata argument\n%s' % e)

encode.encode(
    images_path=images_path,
    output_path=args.output_path,

    start=args.start,
    end=args.end,
    frame_rate=args.framerate,

    sound_path=args.sound_path,
    sound_offset=args.sound_offset,

    source_width=args.source_width,
    source_height=args.source_height,
    target_width=args.target_width,
    target_height=args.target_height,

    top_left=args.top_left,
    top_middle=args.top_middle,
    top_right=args.top_right,
    bottom_left=args.bottom_left,
    bottom_middle=args.bottom_middle,
    bottom_right=args.bottom_right,
    top_left_color=args.top_left_color,
    top_middle_color=args.top_middle_color,
    top_right_color=args.top_right_color,
    bottom_left_color=args.bottom_left_color,
    bottom_middle_color=args.bottom_middle_color,
    bottom_right_color=args.bottom_right_color,

    font_path=args.font_path,

    overlay_image=overlay_image,
    rectangles=rectangles,

    video_codec=args.video_codec,
    audio_codec=args.audio_codec,
    add_silent_audio=args.add_silent_audio,
    silence_settings=args.silence_settings,

    ffmpeg_path=args.ffmpeg_path,

    metadata=metadata,

    overwrite=args.overwrite)
