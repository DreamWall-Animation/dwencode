import os
import fractions

import av
import av.container
import numpy as np


def concatenate_videos(
        paths,
        output_path,
        fps=None,
        width=None,
        height=None,
        audio_sample_rate=None,
        video_codec='libx264',
        audio_codec='aac',
        pix_fmt='yuv420p',
        audio_format=None,
        audio_layout=None):

    output = av.open(output_path, mode='w')
    try:
        for data in _concatenate_videos(
                paths,
                output,
                fps=fps,
                width=width,
                height=height,
                audio_sample_rate=audio_sample_rate,
                video_codec=video_codec,
                audio_codec=audio_codec,
                pix_fmt=pix_fmt,
                audio_format=audio_format,
                audio_layout=audio_layout):
            yield data
    finally:
        output.close()


def _concatenate_videos(
        paths,
        output: av.container.OutputContainer,
        fps=None,
        width=None,
        height=None,
        audio_sample_rate=None,
        video_codec='libx264',
        video_codec_options=None,
        audio_codec='aac',
        audio_codec_options=None,
        pix_fmt='yuv420p',
        audio_format=None,
        audio_layout=None):

    # Get info from first video
    if not all([
            fps, width, height, audio_sample_rate, audio_layout, audio_format
            ]):
        temp = av.open(paths[0])
        first_video_stream = temp.streams.video[0]
        if not fps:
            fps = int(first_video_stream.base_rate)
        if not width:
            width = first_video_stream.format.width
        if not height:
            height = first_video_stream.format.height
        try:
            first_audio_stream = temp.streams.audio[0]
            if not audio_sample_rate:
                audio_sample_rate = first_audio_stream.time_base.denominator
            if not audio_layout:
                audio_layout = first_audio_stream.layout.name
            if not audio_format:
                audio_format = first_audio_stream.format.name
        except IndexError:
            first_audio_stream = None
        temp.close()
    print(f'Encoding to {width}x{height} {fps} fps')

    # Create a video stream (H.264 codec, 30 fps)
    out_video_stream = output.add_stream(
        video_codec, rate=fps, options=video_codec_options)
    out_video_stream.pix_fmt = pix_fmt
    out_video_stream.width = width
    out_video_stream.height = height
    # Output audio stream
    out_audio_stream = None
    if first_audio_stream is not None:
        out_audio_stream = output.add_stream(
            audio_codec, options=audio_codec_options)
        out_audio_stream.rate = audio_sample_rate
        # out_audio_stream.channels = 2
        out_audio_stream.layout = audio_layout
        audio_time_base = fractions.Fraction(1, audio_sample_rate)

    # Global time counter
    frame_pts = 0  # Monotonically increasing PTS across all videos
    audio_pts = 0
    video_time_base = fractions.Fraction(1, fps)

    # Write each frame
    count = len(paths)
    for i, path in enumerate(paths):
        basename = os.path.basename(path)
        print(f'{i + 1}/{count}: {basename}')
        yield i, count

        # Handle Video
        container = av.open(path, metadata_errors='ignore')
        video_stream = container.streams.video[0]
        # Set output image size
        video_stream.thread_type = 'AUTO'  # Important for performance
        decoder = container.decode(video_stream)
        for frame in decoder:
            frame = frame.reformat(width=width, height=height, format=pix_fmt)
            frame.pts = frame_pts
            frame.time_base = video_time_base
            frame_pts += 1
            for packet in out_video_stream.encode(frame):
                output.mux(packet)

        # Handle Audio
        if first_audio_stream is None:
            continue
        container.seek(0)
        video_duration = video_stream.duration * video_stream.time_base
        expected_audio_samples = int(video_duration * audio_sample_rate)
        raw_samples = av.AudioFifo(
            format=audio_format,
            layout=audio_layout,
            sample_rate=audio_sample_rate)
        try:
            audio_stream = container.streams.audio[0]
        except IndexError:
            # No audio, add silence:
            print('Silent audio')
            raw_samples.write(create_silence(
                audio_format, audio_layout, audio_sample_rate,
                expected_audio_samples))
        else:
            needs_resampling = (
                audio_stream.layout.name != audio_layout
                or audio_stream.time_base.denominator != audio_sample_rate
                or audio_stream.format.name
            )
            audio_stream.thread_type = 'AUTO'  # Important for performance
            samples = []
            for audio_frame in container.decode(audio_stream):
                if needs_resampling:
                    audio_resampler = av.AudioResampler(
                        format=audio_format,
                        layout=audio_layout,
                        rate=audio_sample_rate)
                    for audio_frame in audio_resampler.resample(audio_frame):
                        samples.append(audio_frame)
                else:
                    samples.append(audio_frame)
            # Flatten and rebuild audio frame list
            for audio_frame in samples:
                audio_frame.pts = None
                raw_samples.write(audio_frame)
            total_samples = raw_samples.samples
            sample_diff = expected_audio_samples - total_samples
            # Adjust duration
            if sample_diff > 0:
                print('pad audio')
                # Pad with silence
                silent_frame = av.AudioFrame(
                    audio_format, audio_layout, sample_diff)
                silent_frame.sample_rate = audio_sample_rate
                for plane in silent_frame.planes:
                    plane.update(np.zeros(
                        sample_diff, dtype=np.float32).tobytes())
                raw_samples.write(silent_frame)
            elif sample_diff < 0:
                print('trim audio')
                raw_samples.read(-sample_diff)  # Trim excess

        # Write audio frames
        while raw_samples.samples > 0:
            frame = raw_samples.read(min(1024, raw_samples.samples))
            frame.pts = audio_pts
            frame.time_base = audio_time_base
            audio_pts += frame.samples
            for packet in out_audio_stream.encode(frame):
                output.mux(packet)

    # Flush encoder
    for packet in out_video_stream.encode():
        output.mux(packet)
    if out_audio_stream is not None:
        for packet in out_audio_stream.encode():
            output.mux(packet)


def create_silence(
        audio_format, audio_layout, audio_sample_rate, expected_audio_samples):
    silent_frame = av.AudioFrame(
        audio_format, audio_layout, expected_audio_samples)
    silent_frame.sample_rate = audio_sample_rate
    for plane in silent_frame.planes:
        plane.update(np.zeros(
            expected_audio_samples, dtype=np.float32).tobytes())
    return silent_frame
