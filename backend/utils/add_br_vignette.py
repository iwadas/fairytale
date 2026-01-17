import numpy as np
from moviepy import CompositeVideoClip, ImageClip, VideoClip
from typing import Tuple

def vignette_bottom(
    video_size: Tuple[int, int],
    background: VideoClip,
) -> VideoClip:
    """
    Creates an oval gradient that is transparent inside the oval and 
    darkens as you move further OUTSIDE the oval's border.
    
    Effect is applied only to the area below the oval's vertical center.
    """

    w, h = video_size
    
    # 1. Geometry Setup
    # Center X = Middle of video
    # Center Y = Height - 300px
    c_x = w / 2
    c_y = h - (h * 340 / 1248)

    # Horizontal Radius = Width / 2 (Touches the left/right edges)
    # Vertical Radius = radius argument (300px)
    r_x = w / 2
    r_y = h * 240 / 1248

    # 2. Create Coordinate Grid
    # y_grid: (h, 1) -> Column vector
    # x_grid: (1, w) -> Row vector
    y_grid, x_grid = np.ogrid[:h, :w]

    # 3. Calculate Normalized Distance
    # 0.0 = Center
    # 1.0 = Exactly on the oval border
    # > 1.0 = Outside the oval
    dist_sq = ((x_grid - c_x) / r_x) ** 2 + ((y_grid - c_y) / r_y) ** 2
    distance = np.sqrt(dist_sq)

    # 4. Calculate "Distance from Border"
    # We want darkness to start at the border (1.0) and increase outwards.
    # darkness = distance - 1.0
    mask = distance - 1.0
    
    # 5. Apply Filters
    
    # Filter A: Only keep values > 0 (Outside the oval)
    # Inside the oval (distance < 1.0), the result is negative, so we clip to 0.
    mask = np.maximum(0, mask)

    # Filter B: Only apply to the bottom half (Below the center line)
    # This prevents the gradient from wrapping around the top of the oval.
    # We use broadcasting: (Height x Width) * (Height x 1)
    mask = mask * (y_grid >= c_y)

    # 6. Normalize and Apply Opacity
    # "mask" currently contains raw distance values (e.g., 0.0 to 0.5).
    # We normalize so the darkest pixel in the frame becomes 1.0 (fully black).
    max_val = mask.max()
    if max_val > 0:
        mask = np.minimum(1, mask * 1.5 / max_val)  # Scale to 0.0 - 1.0 range

    # 7. Build RGBA Image
    vignette_array = np.zeros((h, w, 4), dtype=np.uint8)
    
    # Set Alpha Channel
    vignette_array[:, :, 3] = (mask * 255).astype(np.uint8)

    # 8. Composite
    vignette_clip = (ImageClip(vignette_array)
                     .with_duration(background.duration)
                     .with_position((0, 0)))

    return CompositeVideoClip([background, vignette_clip])