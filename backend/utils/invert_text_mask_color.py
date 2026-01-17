import cv2
import numpy as np
import random
from typing import List, Tuple, Dict
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ImageClip, VideoClip

NEON_COLOR_RGB = (242, 228, 124)

# --- UNCHANGED TRANSFORM FUNCTION ---
def make_neon_red(frame):
    """ Transforms video frame into bright Red Neon edges on black. """
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    # ksize=5 for thicker, smoother "neon tube" look
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
    magnitude = np.sqrt(grad_x**2 + grad_y**2)
    # Boost brightness and clip
    magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
    magnitude = np.uint8(np.clip(magnitude * 2.5, 0, 255))
    
    r_ratio = NEON_COLOR_RGB[0] / 255.0
    g_ratio = NEON_COLOR_RGB[1] / 255.0
    b_ratio = NEON_COLOR_RGB[2] / 255.0
    
    # Create the 3 channels
    r_channel = (magnitude * r_ratio).astype(np.uint8)
    g_channel = (magnitude * g_ratio).astype(np.uint8)
    b_channel = (magnitude * b_ratio).astype(np.uint8)


    # Put edges into Red channel only
    neon_frame = np.dstack((r_channel, g_channel, b_channel))
    return neon_frame
# ------------------------------------


def generate_neon_text_with_border(
    video_size: Tuple[int, int],
    fonts: List[str],
    background: VideoClip,
    words_with_timing: List[Dict],
) -> VideoClip:
    
    layers = [background]
    print(f"Generating Neon Edges + Borders for {len(words_with_timing)} segments...")

    for item in words_with_timing:
        txt = item["word"]
        t_start = item["start_time"]
        t_end = item["end_time"]
        duration = t_end - t_start

        # --- Font Sizing ---
        if len(txt) >= 10: FONT_SIZE = 60
        elif len(txt) >= 7: FONT_SIZE = 80
        elif len(txt) >= 5: FONT_SIZE = 100
        else: FONT_SIZE = 120
        FONT = random.choice(fonts)

        # ==============================================================================
        # 1. Shared Text Parameters
        # We define these once to ensure the Fill mask and the Border align perfectly.
        # ==============================================================================
        text_params = {
            "text": txt,
            "font": FONT,
            "font_size": FONT_SIZE,
            "method": 'label',
            # We constrain width to video width, let height auto-scale
            "size": (video_size[0], None), 
            "margin": (0, 90),
        }

        # ==============================================================================
        # 2. Create the Neon Fill Layer (The complex part)
        # ==============================================================================
        
        # A. Create a temporary clip just to generate the mask shape
        mask_provider_clip = TextClip(
            **text_params, 
            color='white' # Solid white for the mask
        )

        # B. Manually extract and center the mask onto a full-frame canvas
        # (This ensures absolute positioning stability)
        mask_frame = mask_provider_clip.mask.get_frame(0)
        h, w = mask_frame.shape
        pos_x = (video_size[0] - w) // 2
        pos_y = (video_size[1] - h) // 2
        
        full_mask_arr = np.zeros((video_size[1], video_size[0]), dtype=float)
        y1, y2 = pos_y, min(pos_y + h, video_size[1])
        x1, x2 = pos_x, min(pos_x + w, video_size[0])
        # Copy the text shape into the black full-frame canvas
        full_mask_arr[y1:y2, x1:x2] = mask_frame[0:(y2-y1), 0:(x2-x1)]
        
        full_mask_clip = ImageClip(full_mask_arr, is_mask=True).with_duration(duration)

        # C. Generate the Neon Video Content
        video_segment = background.subclipped(t_start, t_end)
        neon_segment = video_segment.image_transform(make_neon_red)
        
        # D. Composite the Fill
        final_fill_clip = (
            neon_segment
            .with_mask(full_mask_clip)
            .with_start(t_start)
            # We don't need .with_position because the mask is already full-frame
        )
        
        layers.append(final_fill_clip)

        # ==============================================================================
        # 3. Create the Thin Neon Border Layer (The new part)
        # ==============================================================================
        
        outline_clip = TextClip(
            **text_params,
            # Transparent interior so the neon video shows through
            color='rgba(0,0,0,0)', 
            # Bright Red border
            stroke_color=NEON_COLOR_RGB,    
            # Thin width (try 2 or 3. If too thin, the neon glow eats it).
            stroke_width=2         
        ).with_start(t_start).with_duration(duration)
        
        # CRITICAL: Position the outline exactly where we calculated the mask position.
        # Since the TextClip was created with size=(video.w, None), its X origin is 0.
        # We only need to adjust Y.
        outline_clip = outline_clip.with_position((0, pos_y))
        
        layers.append(outline_clip)

    return CompositeVideoClip(layers)