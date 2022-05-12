# dwencode
FFmpeg python wrapper to:
* encode image sequence to movie with overlay text.
* concatenate videos, including side-by-side/stacked concatenation for comparing multiple videos.

## Example:

![image]

[image]: dwencode_example.png "side-by-side input vs overlay"

Python script:
```python
rectangle1 = dict(x=96, y=60, width=768, height=480, color='#FFEE55', opacity=.2, thickness=2)
rectangle2 = dict(x=144, y=90, width=672, height=420, color='#909090', opacity=.3, thickness=1)
image = dict(path='c:/path/to/dw_transp.png', x=10, y=10)
metadata = (('author', 'John Doe'), ('title', 'seq10_sh...'))

encode(
    images_path='c:/path/to/image.%04d.jpg',
    output_path='c:/path/to/encode_test.mov',
    start=15,
    end=60,
    target_width=960,
    target_height=600,
    top_left='{datetime}',
    top_middle='proj_ep010_sq120_sh0170_spline_v002_tk001',
    top_middle_color='#FFEE55',
    top_right='DreamWall',
    bottom_left='f:%.1fmm' % 35,
    bottom_middle='{framerange}',
    bottom_right='John Doe',
    font_path='c:/path/to/luxisr_0.ttf',
    rectangles=[rectangle1, rectangle2],
    overlay_image=image,
    video_codec='-c:v libx264 -profile:v baseline -level 3.0',
    metadata=metadata,
    overwrite=True)
```

Windows commandline example:\
(for Linux just replace `^` by `\` )
```
python c:\path\to\dwencode\dwencode ^
    "c:/path/to/image.####.jpg" ^
    "c:/path/to/encode_test.mov" ^
    --start 15 ^
    --end 60 ^
    --target-width 960 ^
    --target-height 600 ^
    --top-left {datetime} ^
    --top-middle proj_ep010_sq120_sh0170_spline_v002_tk001 ^
    --top-middle-color #FFEE55 ^
    --top-right DreamWall ^
    --bottom-left 35.0mm ^
    --bottom-middle {framerange} ^
    --bottom-right username ^
    --font-path d:/_tmp/luxisr_0.ttf ^
    --rectangle 96-60-768-480-FFEE55-.2-2 ^
    --rectangle 144-90-672-420-909090-.3-1 ^
    --overlay-image d:/_tmp/dw_transp.png-10-10 ^
    --video-codec="-c:v libx264 -profile:v baseline -level 3.0" ^
    --overwrite ^
    --metadata "author:John Doe" ^
    --metadata "title:proj_ep010_sq120_sh0170_spline_v002_tk001"
```

## Documentation:
The default codec is `libx264` and can be used with `.mov` container.

Image ratio is preserved. Input a different target ratio to add `black bars`.\
`Font size` is automatically adapted to target size.

As text, you can use the following expressions:
- `{frame}`: current frame
- `{framerange}`: current frame + first and last frame. e.g. `130 [40-153]`
- `{datetime}`: date in `YYYY/MM/DD HH:MM` format.

### As a python module:
```python
import dwencode
dwencode.encode(
    images_path,         # mandatory
    output_path,         # mandatory
    start=None,          # default is 0
    end=None,            # mandatory        
    frame_rate=None,     # default is 24
    sound_path=None,
    source_width=None,   # optional if you have Pillow (PIL)
    source_height=None,  # optional if you have Pillow (PIL)
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
    ffmpeg_path=None,
    metadata=None,
    overwrite=False)
```


### Commandline arguments:
```
python dwencode input.####.jpg output.mov

-s,    --start                       int
-e,    --end                         int
-fps,  --framerate                   int

-a,    --sound-path                  path

-sw,   --source-width                 
-sh,   --source-height                
-tw,   --target-width                ints
-th,   --target-height                

-tl,   --top-left                     
-tm,   --top-middle                   
-tr,   --top-right                   texts
-bm,   --bottom-middle                
-br,   --bottom-right                 

-tlc,  --top-left-color
-tmc,  --top-middle-color=COLOR
-trc,  --top-right-color=COLOR       colors in RRGGBB format
-blc,  --bottom-left-color=COLOR
-bmc,  --bottom-middle-color=COLOR
-brc,  --bottom-right-color=COLOR

-font, --font-path                   font path

-i,    --overlay-image               image path

-box,  --rectangle                   x-y-width-height-color-opacity-thickness (repeatable)

-c:v,  --video-codec                 ffmpeg arg
-c:a,  --audio-codec                 ffmpeg arg

-p,    --ffmpeg_path                 path

-m,    --metadata                    key:value  (repeatable)

-ow,   --overwrite                   flag

-ffp,  --ffmpeg-path                 ffmpeg path (if ffmpeg not in PATH)
