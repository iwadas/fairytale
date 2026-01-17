import random
from typing import List, Dict, Tuple, Any, Optional

from moviepy import VideoFileClip, CompositeVideoClip, ColorClip, VideoClip
from moviepy import vfx

def blur_br_corner(
    video_size: Tuple[int, int],
    background: VideoClip,
    cover_area: Tuple[int, int] = (150, 60), # Approx size of watermark
    margin: Tuple[int, int] = (30, 30),     # Distance from bottom-right
    cover_color: Optional[Tuple[int, int, int]] = None
) -> VideoClip:
    """
    Obscures the bottom-right corner of the video where the Gemini logo typically sits.
    
    Args:
        video_size: (width, height) of the video.
        background: The source VideoClip.
        cover_area: (width, height) of the area to obscure.
        margin: (x_margin, y_margin) distance from the bottom-right corner.
        cover_color: If provided (e.g. (0,0,0)), uses a solid block instead of blur.
    """
    w, h = video_size
    lw, lh = cover_area
    mx, my = margin
    
    # Calculate position (Bottom-Right)
    pos_x = w - lw - mx
    pos_y = h - lh - my
    
    # Define the position for MoviePy
    position = (pos_x, pos_y)

    if cover_color:
        # APPROACH 1: Solid Color Mask
        # Create a solid color block
        mask_clip = ColorClip(size=cover_area, color=cover_color).with_duration(background.duration)
        mask_clip = mask_clip.with_position(position)
        
        # Overlay the block
        return CompositeVideoClip([background, mask_clip])
        
    else:
        # APPROACH 2: Blur (using the Resize/Pixelate trick)
        # This is much faster than Gaussian blur in pure Python/MoviePy
        
        # 1. Crop the area where the logo is
        cover_area = background.subclipped(0, background.duration).cropped(
            x1=pos_x, y1=pos_y, width=lw, height=lh
        )
        
        # 2. Blur effect: Resize down to 10% then back up to 100%
        # This destroys high-frequency details (text/sharp logos) effectively
        blurred_area = (cover_area
                        .resized(0.1)  # Shrink to lose detail
                        .resized(lambda t: (lw, lh)) # Scale back up (bilinear interpolation blurs it)
                       )
        
        # 3. Position the blurred clip exactly over the original
        blurred_area = blurred_area.with_position(position)
        
        # 4. Composite it back onto the original
        return CompositeVideoClip([background, blurred_area])