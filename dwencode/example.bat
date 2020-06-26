py D:\_dev\dwdev\dwencode_public\dwencode ^
    "d:/_tmp/playblast_example/dwencode_playblast_scene.####.jpg" ^
    "d:/_tmp/encode_test.mov" ^
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


start d:/_tmp/encode_test.mov
