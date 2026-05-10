


import tempfile
from PIL import Image, ImageFilter, ImageEnhance
from typing import List, Dict, Any, Optional, Tuple
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, VideoClip, ImageClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.fx import CrossFadeIn
import numpy as np



def generate_karaoke_text(segments: List[Dict[str, Any]], visuals: VideoClip, options: Dict[str, Any] = None) -> VideoClip:
    """
    Generates karaoke-style subtitles based on the provided segments and composits them on top of the visuals.
    Each segments contains:
    ```python
    {
        "words": List[str],  # List of words in the segment
        "start": float,     # Start time of the segment in seconds
        "end": float        # End time of the segment in seconds
    }
    ```    
    Options can include:
    - font: Path to the font file to use for the text
    - color: Color of the text (default: 'white')
    - shadow: Boolean indicating whether to add a shadow effect (default: False)
    - video_size: Tuple (width, height) of the video for proper text positioning (default: (720, 1280))
    - border: Dictionary containing border properties (default: {"width": 0, "color": "white"})
    """

    # PARAMS
    VIDEO_SIZE = options.get("video_size", (720, 1280))
    VIDEO_W, VIDEO_H = VIDEO_SIZE
    FONT = options.get("font", 'DEFAULT_FONT')

    FONTSIZE = int(30 * (VIDEO_H / 720))
    LINE_SPACING = 14 * (VIDEO_H / 720)
    WORD_GAP_PX = int(7 * (VIDEO_W / 720))
    MAX_LINE_WIDTH_PX = int(500 * (VIDEO_W / 720))
    POS_Y = 800 * (VIDEO_H / 1280)  # Adjust Y position based on resolution
    
    COLOR = options.get("color", 'white')
    SPECIAL_COLOR = options.get("special_color", 'yellow')
    ADD_SHADOW = options.get("shadow", False)
    BORDER = options.get("border", {"width": 0, "color": "white"})

    DEFAULT_ANIMATION_DURATION = 0.4
    DROP_OFFSET = 10 * (VIDEO_H / 1280)


    # HELPER FUNCTIONS

    # getting size of the pixel for future use in positioning and styling
    def word_pixel_size(word: str) -> Tuple[int, int]:
        """Return (width, height) of a single word rendered with the global settings."""
        tmp = TextClip(
            text=word,
            font=FONT,
            font_size=FONTSIZE,
            color=COLOR,
            method='label',
        )
        w, h = tmp.size
        tmp.close()
        return w, h
    
    # Creating word with appropriate styling and effects
    def make_word_clip(txt: str,
                    color: str,
                    start: float,
                    end: float,
                    width: int,
                    pos: Tuple[int, int],
                    animation_duration: Optional[float] = None
                ) -> VideoClip:
        """Return a single-word clip that is guaranteed to have w > 0, h > 0."""

        clip = TextClip(
            text=txt,
            font_size=FONTSIZE,
            color=color,
            font=FONT,
            bg_color=(0,0,0,0),
            margin=(0, 30),
            method='label',               # <-- exact bbox
            size=(width, None),  # give some breathing room
        )

        w, h = clip.size

        print('clip size')
        print((w, h))
        if w == 0 or h == 0:               # <-- safety net
            # fallback: draw a tiny coloured rectangle so the mask is not empty
            print("fucking shit")
            clip = ColorClip(size=(width, FONTSIZE+10), color=color).with_duration(end-start)
            w, h = clip.size

        # keep the clip inside the video frame
        x = max(0, min(pos[0], VIDEO_W - w))
        y = max(0, min(pos[1], VIDEO_H - h))



        def make_drop_position(pos_x, pos_y, animation_duration=DEFAULT_ANIMATION_DURATION):
            def position(t):
                if t < animation_duration:
                    progress = t / animation_duration
                    # Ease-out quadratic for smooth landing
                    eased = 1 - (1 - progress) ** 2
                    y_offset = DROP_OFFSET * (1 - eased)
                else:
                    y_offset = 0
                return (pos_x, pos_y + y_offset)
            return position


        def shadow_text_clip(text_clip: TextClip, blur_radius: int, pos: Tuple[int, int], start: float, animation_duration: float, duration: float) -> VideoClip:
            # Convert TextClip to PIL
            temp_file = tempfile.NamedTemporaryFile(suffix=".png").name
            clip.save_frame(temp_file)
            image = Image.open(temp_file)
            pil_img = image

            # === THIS IS THE KEY CHANGE ===
            # Force the text to be bright white (ignoring original color)
            # Convert to grayscale then threshold to pure white text on transparent bg
            pil_img = pil_img.convert("L")                     # grayscale
            pil_img = pil_img.point(lambda p: 255 if p > 50 else 0)  # make text pure white
            pil_img = pil_img.convert("RGBA")
            data = pil_img.getdata()
            new_data = []
            for item in data:
                # Keep white pixels white, make dark pixels transparent
                if item[0] == 255:  # white
                    new_data.append((0, 0, 0, 255))   # bright white
                    # new_data.append((255, 255, 255, 255))   # bright white
                else:
                    new_data.append((0, 0, 0, 0))           # transparent
            pil_img.putdata(new_data)
            # ===============================

            # Offset for centered blur
            offset = int(blur_radius * 0.6)

            # Pad for blur
            pil_img_padded = Image.new("RGBA", (pil_img.width + blur_radius * 3, pil_img.height + blur_radius * 3), (0,0,0,0))
            pil_img_padded.paste(pil_img, (blur_radius + offset, blur_radius + offset), pil_img)

            # Apply strong Gaussian blur → creates bright glow
            pil_img_padded = pil_img_padded.filter(ImageFilter.GaussianBlur(radius=blur_radius))

            # Optional: make it even brighter (boost intensity)
            # enhancer = ImageEnhance.Brightness(pil_img_padded)
            # pil_img_padded = enhancer.enhance(4)  # increase if you want stronger glow

            # Convert back to MoviePy clip
            text_clip = ImageClip(np.array(pil_img_padded))
            final_pos = (pos[0] - 2*offset, pos[1] - 2*offset)
            text_clip = text_clip.with_duration(duration).with_start(start).with_position(make_drop_position(*final_pos, animation_duration=animation_duration)).with_effects([CrossFadeIn(animation_duration / 2)])

            return text_clip

        fade_in_duration = animation_duration / 2 if animation_duration is not None else None


        clip = clip.with_position(make_drop_position(x, y, animation_duration=animation_duration)).with_start(start).with_duration(end - start).with_effects([CrossFadeIn(fade_in_duration)])
        
        if ADD_SHADOW:
            shadow_clip_1 = shadow_text_clip(text_clip = clip.copy(), blur_radius=5, pos=(x, y), start=start, duration = end-start, animation_duration=fade_in_duration)
            shadow_clip_2 = shadow_text_clip(text_clip = clip.copy(), blur_radius=12, pos=(x, y), start=start, duration = end-start, animation_duration=fade_in_duration)

        return (clip, shadow_clip_1, shadow_clip_2)

    clips = []
    for seg in segments:
        seg_start = seg["start"]
        seg_end   = seg["end"]
        words     = seg["words"]
        # --------------------------------------------------------------
        # 1. Build the *full* segment text and split it into lines
        # --------------------------------------------------------------
        # textwrap uses characters, not pixels → we have to iterate
        lines = []
        current_line = []
        current_width = 0

        for w in words:
            print("word")
            print(w)
            ww, wh = word_pixel_size(w["word"])
            print("word width:")
            print(ww)
            print(wh)

            new_word_width = WORD_GAP_PX + ww if current_width > 0 else ww 

            if current_width + new_word_width > MAX_LINE_WIDTH_PX and current_line:
                lines.append(current_line)
                current_line = [w]
                current_width = ww
            else:
                current_line.append(w)
                current_width += new_word_width

        if current_line:
            lines.append(current_line)

        print("lines")
        print(lines)

        # --------------------------------------------------------------
        # 2. Compute the exact (x, y) position of *every* word in the
        #     final layout (so that each word appears exactly where it
        #     will end up when the whole segment is visible)
        # --------------------------------------------------------------
        word_positions = []          # list of (word_obj, x, y)

        y = POS_Y
        for line_words in lines:
            # total width of the line (including spaces)
            line_w = sum(word_pixel_size(w["word"])[0] + WORD_GAP_PX for w in line_words) - WORD_GAP_PX

            line_x_start = (VIDEO_W - MAX_LINE_WIDTH_PX) // 2 + \
                        (MAX_LINE_WIDTH_PX - line_w) // 2

            x = line_x_start
            for i, w in enumerate(line_words):
                ww, _ = word_pixel_size(w["word"])
                word_positions.append((w, x, y, ww))
                x += ww + WORD_GAP_PX

            y += FONTSIZE + LINE_SPACING

        print("word positions")
        print(word_positions)

        # --------------------------------------------------------------
        # 3. Create a TextClip for *every* word
        # --------------------------------------------------------------
        for i, (word_obj, final_x, final_y, word_width) in enumerate(word_positions):
            txt = word_obj["word"]
            appear_at = word_obj["start"]
            animation_duration = word_obj.get("end") - appear_at

            try:

                is_special = word_obj.get("is_special", False)

                word_clip, blurred_clip, shadow_clip = make_word_clip(
                    # if the text is special we make it uppercase
                    txt=txt,
                    width=word_width,
                    start=appear_at,
                    # color=SPECIAL_COLOR if is_special else COLOR,
                    color=COLOR,
                    end=seg_end,
                    animation_duration=animation_duration,
                    pos=(final_x, final_y)
                )
        
                clips.append(shadow_clip)
                clips.append(blurred_clip)
                clips.append(word_clip)


            except Exception as e:
                print(f"Failed to create TextClip for word: '{txt}' | Error: {e}")
                continue

    # ------------------------------------------------------------------
    # 4. Composite everything on top of the original video
    # ------------------------------------------------------------------
    final = CompositeVideoClip([visuals] + clips)
    return final
