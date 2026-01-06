import random
from pydub import AudioSegment

from typing import List, Dict, Tuple, Any

from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, VideoClip, ImageClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.fx import CrossFadeIn
from moviepy import vfx
import json

import numpy as np


def generate_invert_mask_text(
    video_size: Tuple[int, int],
    fonts: List[str],
    background: VideoClip,
    words_with_timing,
) -> VideoClip:
    """
    background : your original MoviePy clip (or CompositeVideoClip)
    segments   : list of dicts exactly as you described

    Returns a new clip with the karaoke subtitles composited on top.
    """

    video = background
    all_knocked_clips = []
    print("Available fonts:")
    print(fonts)

    for item in words_with_timing:
        txt = item["word"]
        t_start = item["start_time"]
        t_end = item["end_time"]
        duration = t_end - t_start

        FONT_SIZE = 120
        if(len(txt) >=10):
            FONT_SIZE = 60
        elif(len(txt) >=7):
            FONT_SIZE = 80
        elif(len(txt) >=5):
            FONT_SIZE = 100
        FONT_SIZE = FONT_SIZE * 2

        FONT = random.choice(fonts)
        print("FONT")
        print(FONT)

        text_clip = TextClip(
            text=txt,
            font=FONT,
            font_size=FONT_SIZE,
            stroke_color='black',
            stroke_width=2,
            method='label',
            margin=(0, 90),
            size=(video.w, None)
        )

        # ─── CREATE FULL-SIZE MASK ────────────────────────────────────
        mask_img = text_clip.mask.get_frame(0)  # numpy array (h, w) float 0-1, 1 at text
        h, w = mask_img.shape
        print("Mask size:", w, "x", h)


        full_mask_array = np.zeros((video.h, video.w), dtype=float)

        # Calculate position (assuming static 'center' for simplicity)
        pos_x = (video_size[0] - w) // 2
        pos_y = (video_size[1] - h) // 2

        full_mask_array[pos_y:pos_y + h, pos_x:pos_x + w] = mask_img
        # ───────────────────────────────────────────────────────────────

        full_mask_clip = ImageClip(full_mask_array, is_mask=True).with_duration(duration)

        # Create the inverted piece masked to text area
        inverted_piece = video.with_effects([vfx.InvertColors()]).subclipped(t_start, t_end).with_mask(full_mask_clip).with_start(t_start)

        all_knocked_clips.append(inverted_piece)
    return CompositeVideoClip([background] + all_knocked_clips)