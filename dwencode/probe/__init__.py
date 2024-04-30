from dwencode.probe import ffprobe
from dwencode.probe import quicktime


try:
    import cv2  # opencv-python
except ImportError:
    print('Warning: cannot use opencv => slower movie duration queries.')
    cv2 = None


def cv2_get_video_duration(video_path, frames=False):
    video = cv2.VideoCapture(video_path)
    duration = video.get(cv2.CAP_PROP_FRAME_COUNT)
    if not frames and duration:
        duration /= video.get(cv2.CAP_PROP_FPS)
    return duration


def get_video_duration(video_path, frames=False, ffprobe_path=None):
    if cv2 is not None:
        return cv2_get_video_duration(video_path, frames)
    elif video_path.endswith('.mov'):
        return quicktime.get_mov_duration(video_path, frames, framerate=25.0)
    else:
        return ffprobe.get_video_duration(video_path, frames, ffprobe_path)
