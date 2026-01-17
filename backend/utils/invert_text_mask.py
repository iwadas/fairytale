import random
import numpy as np
from typing import List, Tuple, Dict, Any
from moviepy import VideoClip, TextClip, CompositeVideoClip, ImageClip
from moviepy import vfx

def generate_invert_mask_text(
    video_size: Tuple[int, int],
    fonts: List[str],
    background: VideoClip,
    words_with_timing: List[Dict[str, Any]],
    add_border: bool = True  # <--- Added Argument
) -> VideoClip:
    """
    background : your original MoviePy clip (or CompositeVideoClip)
    words_with_timing : list of dicts with keys 'word', 'start_time', 'end_time'
    add_border : If True, adds a white stroke on top of the inverted text.

    Returns a new clip with the karaoke subtitles composited on top.
    """

    video = background
    # We will accumulate all clips here (inverted pieces + optional borders)
    all_knocked_clips = []
    
    print("Available fonts:", fonts)

    for item in words_with_timing:
        txt = item["word"]
        t_start = item["start_time"]
        t_end = item["end_time"]
        duration = t_end - t_start

        # --- Dynamic Font Sizing ---
        FONT_SIZE = 120
        if len(txt) >= 10:
            FONT_SIZE = 60
        elif len(txt) >= 7:
            FONT_SIZE = 80
        elif len(txt) >= 5:
            FONT_SIZE = 100
        
        FONT = random.choice(fonts)
        print(f"Processing '{txt}' with Font: {FONT}")

        # 1. Create the Clip used for the MASK (The hole cutter)
        # Note: Stroke here just dilates the mask slightly; we keep it black or remove it.
        mask_text_clip = TextClip(
            text=txt,
            font=FONT,
            font_size=FONT_SIZE,
            color='white',       # The "inside" of the mask needs to be opaque (white for mask)
            stroke_color='white',# Make stroke white to widen the cut-out area slightly
            stroke_width=2,
            method='label',
            margin=(0, 90),
            size=(video.w, None)
        )

        # ─── CREATE FULL-SIZE MASK ────────────────────────────────────
        # Get the alpha channel or luminance of the text clip to use as mask
        # We ensure we get the mask properly from the TextClip
        if mask_text_clip.mask is None:
             # Fallback if mask isn't auto-generated (rare in v2)
             mask_text_clip = mask_text_clip.with_mask()
             
        mask_img = mask_text_clip.mask.get_frame(0)
        h, w = mask_img.shape
        # print("Mask size:", w, "x", h)

        full_mask_array = np.zeros((video.h, video.w), dtype=float)

        # Calculate position (centering)
        pos_x = (video_size[0] - w) // 2
        pos_y = (video_size[1] - h) // 2

        # Place the text mask in the center of the full black frame
        full_mask_array[pos_y:pos_y + h, pos_x:pos_x + w] = mask_img
        # ───────────────────────────────────────────────────────────────

        full_mask_clip = ImageClip(full_mask_array, is_mask=True).with_duration(duration)

        # 2. Create the Inverted Video Piece
        inverted_piece = (
            video.with_effects([vfx.InvertColors()])
            .subclipped(t_start, t_end)
            .with_mask(full_mask_clip)
            .with_start(t_start)
        )
        
        all_knocked_clips.append(inverted_piece)

        # 3. (Optional) Create the White Border Overlay
        if add_border:
            # We create a visual clip that is JUST the stroke
            border_clip = TextClip(
                text=txt,
                font=FONT,
                color='rgba(0,0,0,0)',
                font_size=FONT_SIZE,
                stroke_color='white',   # The actual border color
                stroke_width=1,         # Slightly thicker than mask to be visible
                method='label',
                margin=(0, 90),
                size=(video.w, None)    # Match dimensions of mask clip exactly
            ).with_position(('center', 'center')).with_start(t_start).with_duration(duration)

            all_knocked_clips.append(border_clip)

    # Return original background with the new inverted chunks (and borders) layered on top
    return CompositeVideoClip([background] + all_knocked_clips)