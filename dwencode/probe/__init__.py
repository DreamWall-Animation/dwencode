from dwencode.probe.ffprobe import *
from dwencode.probe import quicktime

try:
    import cv2
except ImportError:
    print('Warning: cannot use opencv => slower movie duration queries.')
    cv2 = None


def get_duration(video_path, frames=False):
    if cv2 is not None:
        video = cv2.VideoCapture(video_path)
        duration = video.get(cv2.CAP_PROP_FRAME_COUNT)
        if not frames:
            duration /= video.get(cv2.CAP_PROP_FPS)
        return duration
    elif video_path.endswith('.mov'):
        return quicktime.get_mov_duration(video_path, frames, framerate=25.0)
    else:
        data = probe(video_path)
        vid_stream = [s for s in data['streams'] if 'nb_frames' in s][0]
        if frames:
            return int(vid_stream['nb_frames'])
        else:
            return int(vid_stream['duration'])
