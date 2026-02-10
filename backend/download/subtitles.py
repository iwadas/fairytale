from typing import List, Protocol, Tuple, runtime_checkable, Dict, Any
from moviepy import VideoClip
from builder import VideoBuilder
import json

# MOVIEPY IMPORTS
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, VideoClip, ImageClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.fx import CrossFadeIn

import tempfile
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

from text.border_text_generator import generate_border_text


GLUE_PUNCTUATION = {",", ".", "?", "!", ":", ";", "-", "–", "—"}

# 1. Decorate with @runtime_checkable if you want to use isinstance(obj, SubtitleGenerator)
@runtime_checkable
class SubtitleGenerator(Protocol):
    def generate(self) -> Any:
        ...
    
class InvertTextMaskSubtitleGenerator:
    def __init__(self, builder: VideoBuilder):
        self._builder = builder

    def generate(self, background: VideoClip) -> VideoClip:
        # Implementation logic here
        return VideoClip() 
    
class BorderSubtitleGenerator:
    def __init__(self, builder: VideoBuilder):
        self._builder = builder

    def generate(self, background: VideoClip) -> VideoClip:

        def prepare_word_timings(vo_timestamps, segment_start_time: float):
            def normalize(s: str) -> str:
                return s.strip().upper()  # You can adjust normalization (e.g. remove punctuation)

            # Prepare normalized timestamps for matching
            timestamp_words = [(normalize(ts["word"]), ts["time"]) for ts in vo_timestamps]
            
            # add end time to words
            for i in range(len(timestamp_words) - 1):
                # remove punctuation-only words and eleven labs tags "[]"
                if timestamp_words[i][0] in GLUE_PUNCTUATION or timestamp_words[i][0][0] == '[':
                    continue
                timestamps_with_end_time.append({
                    "word": timestamp_words[i][0],
                    "start_time": segment_start_time + timestamp_words[i][1],
                    "end_time": segment_start_time + min(timestamp_words[i + 1][1], timestamp_words[i][1] + 2)
                })

            # append last word
            if timestamp_words[-1][0] not in GLUE_PUNCTUATION:
                timestamps_with_end_time.append({
                    "word": timestamp_words[-1][0],
                    "start_time": segment_start_time + timestamp_words[-1][1],
                    "end_time": segment_start_time + timestamp_words[-1][1] + 0.75
                })
            return timestamps_with_end_time
        
        timestamps_with_end_time = []
        voiceovers = self._builder._project.get("voiceovers", [])
        for vo in voiceovers:
            prepare_word_timings(vo.get("timestamps", []), float(vo.get("start_time", 0.0)))
        
        return generate_border_text(
            video_size=self._builder._resolution,
            fonts=self._builder._fonts,
            background=background
        )
    



    def generate(self) -> VideoClip:
        # Implementation logic here
        return VideoClip()

class KaraokeSubtitleGenerator:
    def __init__(self, builder: VideoBuilder):
        self._builder = builder

    def generate(self, background: VideoClip) -> VideoClip:
        add_subtitle_shadow = self._builder._subtitle_shadow
        voiceovers = self._builder._project.get("voiceovers", [])

        """
        background : your original MoviePy clip (or CompositeVideoClip)
        segments   : list of dicts exactly as you described
        Returns a new clip with the karaoke subtitles composited on top.
        """

        VIDEO_W, VIDEO_H = self._builder._resolution
        FONT = self._builder._fonts.pop()
        FONTSIZE = int(34 * (VIDEO_H / 1280))
        COLOR = self._builder._subtitle_color
        SHADOW = self._builder._subtitle_shadow
        
        STROKE_WIDTH = 0
        ALIGN = "center"
        VALIGN = "bottom"
        
        POS_Y = 800 * (VIDEO_H / 1280)  # Adjust Y position based on resolution
        LINE_SPACING = 10 * (VIDEO_H / 1280)
        WORD_GAP_PX = int(6 * (VIDEO_W / 720))
        MAX_LINE_WIDTH_PX = int(500 * (VIDEO_W / 720))
        
        DROP_OFFSET = 10 * (VIDEO_H / 1280)
        DROP_DURATION = 0.4
        FADE_IN_DURATION = 0.4
        DROP_DURATION = 0.4
        
        def prepare_segments(timestamps: List[Dict[str, Any]], text_with_pauses: str, segment_start_time: float = None) -> List[Dict[str, Any]]:
            """
            Prepares segments with words and timing based on timestamps and text with pauses ('|').
            Args:
                timestamps: List of dicts with {"word": str, "time": float}
                text_with_pauses: String with words and '|' separating segments
                segment_start_time: When to start the segment (word persists on the screen)
            Returns:
                List of segments with start_time, end_time, and words with times
            """
            SYMBOLS = [",", ".", "?", ":"]
            
            # Step 1: Normalize and split the text_with_pauses
            normalized_text = text_with_pauses.replace("|", " | ").replace("'", " ' ")
            for symbol in SYMBOLS:
                normalized_text = normalized_text.replace(symbol, f" {symbol}")
            
            words = [w.strip() for w in normalized_text.split() if w.strip() and not w.startswith("[")]
            
            # Normalize function
            def normalize(s: str) -> str:
                return s.strip().lower()  # You can adjust normalization (e.g. remove punctuation)

            # Prepare normalized timestamps for matching
            timestamp_words = [(normalize(ts["word"]), ts["time"]) for ts in timestamps]
            
            segments = []
            current_segment = None
            last_word_time = 0.0
            timestamps_idx = 0
            set_times = False
            new_segment_start_time = segment_start_time

            for word in words:
                if word == "|":
                    # Start new segment
                    if current_segment is not None:
                        # Set end_time for previous segment
                        time_between = max(last_word_time + 0.5, (new_segment_start_time + last_word_time) / 2 - 0.1)
                        current_segment["end_time"] = time_between
                        segments.append(current_segment)
                    
                    current_segment = {"words": []}
                    set_times = True
                    continue

                # Find matching timestamp
                while timestamps_idx < len(timestamp_words):
                    ts_norm_word, ts_time = timestamp_words[timestamps_idx]
                    if ts_norm_word == normalize(word):
                        current_word_time = ts_time + segment_start_time
                        break
                    timestamps_idx += 1
                else:
                    # Word not found in timestamps
                    continue

                # If this is first word of new segment, set start_time and previous end_time
                if set_times and current_segment is not None:
                    new_segment_start_time = current_word_time
                    current_segment["start_time"] = new_segment_start_time
                    set_times = False

                last_word_time = current_word_time

                # Add word to current segment
                if current_segment is None:
                    current_segment = {"words": [], "start_time": current_word_time}
                
                current_segment["words"].append({"word": word, "time": current_word_time})

            # Append the last segment
            if current_segment is not None:
                segments.append(current_segment)

            # Post-process: set start_time of first segment and end_time of last
            if segments and timestamps:
                segments[0]["start_time"] = timestamps[0]["time"]
                last_timestamp_time = timestamps[-1]["time"] + segment_start_time
                if "end_time" not in segments[-1]:
                    segments[-1]["end_time"] = last_timestamp_time + 0.25

            return segments

        segments = []
        for vo in voiceovers:
            timestamps = vo.get("timestamps", [])
            segment_start_time = float(vo.get("start_time", 0.0))
            timestamps = json.loads(timestamps) if isinstance(timestamps, str) else timestamps
            text_with_pauses = vo.get("text_with_pauses", "")
            segs = prepare_segments(timestamps, text_with_pauses, segment_start_time)
            segments.extend(segs)


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
        
        def make_word_clip(txt: str,
                        color: str,
                        start: float,
                        width: int,
                        end: float,
                        pos: Tuple[int, int]) -> VideoClip:
            """Return a single-word clip that is guaranteed to have w > 0, h > 0."""
            clip = TextClip(
                text =txt,
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


            def make_drop_position(pos_x, pos_y):
                def position(t):
                    if t < DROP_DURATION:
                        progress = t / DROP_DURATION
                        # Ease-out quadratic for smooth landing
                        eased = 1 - (1 - progress) ** 2
                        y_offset = DROP_OFFSET * (1 - eased)
                    else:
                        y_offset = 0
                    return (pos_x, pos_y + y_offset)
                return position


            # def make_drop_position(t):
            #     if t < DROP_DURATION:
            #         progress = t / DROP_DURATION
            #         # Ease-out quadratic for smooth landing
            #         eased = 1 - (1 - progress) ** 2
            #         y_offset = DROP_OFFSET * (1 - eased)
            #     else:
            #         y_offset = 0
            #     return (x, y + y_offset)
            
            def shadow_text_clip(text_clip: TextClip, blur_radius: int, pos: Tuple[int, int], start: float, duration: float) -> VideoClip:
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
                        new_data.append((255, 255, 255, 255))   # bright white
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
                enhancer = ImageEnhance.Brightness(pil_img_padded)
                pil_img_padded = enhancer.enhance(4)  # increase if you want stronger glow

                # Convert back to MoviePy clip
                text_clip = ImageClip(np.array(pil_img_padded))
                final_pos = (pos[0] - 2*offset, pos[1] - 2*offset)
                text_clip = text_clip.with_duration(duration).with_start(start).with_position(make_drop_position(final_pos)).with_effects([CrossFadeIn(FADE_IN_DURATION)])

                return text_clip


            clip = clip.with_position(make_drop_position(x, y)).with_start(start).with_duration(end - start).with_effects([CrossFadeIn(FADE_IN_DURATION)])
            shadow_clip_1 = shadow_text_clip(text_clip = clip.copy(), blur_radius=5, pos=(x, y), start=start, duration = end-start)
            shadow_clip_2 = shadow_text_clip(text_clip = clip.copy(), blur_radius=12, pos=(x, y), start=start, duration = end-start)
            # clip = clip.with_start(start).with_position((x, y)).with_duration(end - start).with_effects([CrossFadeIn(FADE_IN_DURATION)])

            return (clip, shadow_clip_1, shadow_clip_2)

        clips = []                     # will hold all individual word TextClips
        for seg in segments:
            seg_start = seg["start_time"]
            seg_end   = seg["end_time"]
            words     = seg["words"]                # [{word: "...", time: ...}, ...]

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

                if w["word"] in GLUE_PUNCTUATION and current_line:
                    gap_addition = 0
                else:
                    gap_addition = WORD_GAP_PX

                if current_width + gap_addition + ww > MAX_LINE_WIDTH_PX and current_line:
                    lines.append(current_line)
                    current_line = [w]
                    current_width = ww
                else:
                    current_line.append(w)
                    current_width += gap_addition + ww

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
            for line_idx, line_words in enumerate(lines):
                # total width of the line (including spaces)


                line_w = sum(word_pixel_size(w["word"])[0] for w in line_words)
                line_w += (len([w for w in line_words if w["word"] in GLUE_PUNCTUATION]) - 1) * WORD_GAP_PX

                # centre the line inside the 500 px box
                line_x_start = (VIDEO_W - MAX_LINE_WIDTH_PX) // 2 + \
                            (MAX_LINE_WIDTH_PX - line_w) // 2

                x = line_x_start
                for i, w in enumerate(line_words):
                    ww, _ = word_pixel_size(w["word"])
                    if i > 0 and w["word"] not in GLUE_PUNCTUATION:
                        x += WORD_GAP_PX
                    word_positions.append((w, x, y, ww))
                    x += ww

                y += FONTSIZE + LINE_SPACING

            print("word positions")
            print(word_positions)

            # --------------------------------------------------------------
            # 3. Create a TextClip for *every* word
            # --------------------------------------------------------------
            for i, (word_obj, final_x, final_y, word_width) in enumerate(word_positions):
                word = word_obj["word"]
                appear_at = word_obj["time"]

                try:
                    word_clip, blurred_clip, shadow_clip = make_word_clip(
                        txt=word_obj["word"],
                        width=word_width,
                        start=appear_at,
                        end=seg_end,
                        pos=(final_x, final_y)
                    )
            
                    clips.append(shadow_clip)
                    clips.append(blurred_clip)
                    clips.append(word_clip)


                except Exception as e:
                    print(f"Failed to create TextClip for word: '{word}' | Error: {e}")
                    continue

        # ------------------------------------------------------------------
        # 4. Composite everything on top of the original video
        # ------------------------------------------------------------------
        final = CompositeVideoClip([background] + clips)
        return final


