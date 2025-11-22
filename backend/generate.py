
import os
import tempfile
import uuid
from pydub import AudioSegment

from typing import List, Dict, Tuple, Any

from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, VideoClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.fx import FadeIn
import json

VIDEO_W, VIDEO_H = 704, 1248                # your video resolution
MAX_LINE_WIDTH_PX = 500                     # max width of a *line* in px
FONTSIZE = 44
COLOR_INACTIVE = "white"                    # colour of words that have not appeared yet
COLOR_ACTIVE   = "#ffdd00"                # colour of the word that is currently sung
BORDER_COLOR   = None                       # optional outline
STROKE_COLOR   = "black"                    # outline colour (None = no outline)
STROKE_WIDTH   = 8
ALIGN = "center"                            # alignment inside the 500 px box
VALIGN = "bottom"                           # vertical alignment of the whole block
POS_Y = 800                                 # top coordinate of the *first* line
LINE_SPACING = 10
FADE_IN_DURATION = 0.2
DROP_DURATION = 0.2
DROP_OFFSET = -20
# FONT = 'backend/static/default/fonts/bahnschrift.ttf'
FONT = 'static/default/fonts/DMSerifText-Regular.ttf'
WORD_GAP_PX = 8
BG_MUSIC_PATH = 'static/default/sounds/'


def word_pixel_size(word: str) -> Tuple[int, int]:
    """Return (width, height) of a single word rendered with the global settings."""
    tmp = TextClip(
        text=word,
        font=FONT,
        font_size=FONTSIZE,
        color=COLOR_INACTIVE,
        stroke_color=STROKE_COLOR,
        stroke_width=STROKE_WIDTH,
        method='label',
    )
    w, h = tmp.size
    tmp.close()

    return w, h


# replace every TextClip creation with this helper
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
        stroke_color=STROKE_COLOR,
        stroke_width=STROKE_WIDTH,
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

    clip = clip.with_opacity(1.0)

    # keep the clip inside the video frame
    x = max(0, min(pos[0], VIDEO_W - w))
    y = max(0, min(pos[1], VIDEO_H - h))


    def make_drop_position(t):
        if t < DROP_DURATION:
            progress = t / DROP_DURATION
            # Ease-out quadratic for smooth landing
            eased = 1 - (1 - progress) ** 2
            y_offset = DROP_OFFSET * (1 - eased)
        else:
            y_offset = 0
        return (x, y + y_offset)

    clip = clip.with_position(make_drop_position).with_start(start).with_duration(end - start).with_effects([FadeIn(FADE_IN_DURATION)])
    return clip


def prepare_segments(timestamps: List[Dict[str, Any]], text_with_pauses: str, segment_start_time: float = None) -> List[Dict[str, Any]]:
    """
    Prepares segments with words and timing based on timestamps and text with pauses ('|').
    
    Args:
        timestamps: List of dicts with {"word": str, "time": float}
        text_with_pauses: String with words and '|' separating segments
        segment_start_time: Not used in logic (kept for compatibility), can be ignored
    
    Returns:
        List of segments with start_time, end_time, and words with times
    """
    SYMBOLS = [",", ".", "?", ":"]
    
    # Step 1: Normalize and split the text_with_pauses
    normalized_text = text_with_pauses
    normalized_text = normalized_text.replace("|", " | ").replace("'", " ' ")
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
                time_between = max(last_word_time + 0.25, (new_segment_start_time + last_word_time) / 2 - 0.1)
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


def add_karaoke_subtitles(
    background: VideoClip,
    segments,
) -> VideoClip:
    """
    background : your original MoviePy clip (or CompositeVideoClip)
    segments   : list of dicts exactly as you described

    Returns a new clip with the karaoke subtitles composited on top.
    """

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

            if current_width + WORD_GAP_PX + ww > MAX_LINE_WIDTH_PX and current_line:
                lines.append(current_line)
                current_line = [w]
                current_width = ww
            else:
                current_line.append(w)
                current_width += WORD_GAP_PX + ww

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
            line_w += (len(line_words) - 1) * WORD_GAP_PX

            # centre the line inside the 500 px box
            line_x_start = (VIDEO_W - MAX_LINE_WIDTH_PX) // 2 + \
                           (MAX_LINE_WIDTH_PX - line_w) // 2

            x = line_x_start
            for i, w in enumerate(line_words):
                ww, _ = word_pixel_size(w["word"])
                if i > 0:
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
                word_clip = make_word_clip(
                    txt=word_obj["word"],
                    width=word_width,
                    color=COLOR_INACTIVE,
                    start=appear_at,
                    end=seg_end,
                    pos=(final_x, final_y)
                )
                
                clips.append(word_clip)

            except Exception as e:
                print(f"Failed to create TextClip for word: '{word}' | Error: {e}")
                continue

    # ------------------------------------------------------------------
    # 4. Composite everything on top of the original video
    # ------------------------------------------------------------------
    final = CompositeVideoClip([background] + clips)
    return final


def make_background_sound(project_duration: float, sound_name) -> AudioSegment:
    """Create background music AudioSegment of specified duration by looping/trimming a base track."""
    bg_path = os.path.join(BG_MUSIC_PATH, sound_name)

    if not os.path.exists(bg_path):
        raise FileNotFoundError(f"Background music not found: {bg_path}")

    bg = AudioSegment.from_file(bg_path)          # load once
    bg_ms = len(bg)                               # length in ms
    target_ms = int(project_duration * 1000)

    if bg_ms >= target_ms:
        return bg[:target_ms]                     # trim if longer

    # repeat full copies
    repeats = target_ms // bg_ms
    remainder = target_ms % bg_ms
    background = bg * repeats
    if remainder:
        background += bg[:remainder]
    return background


def assemble_audio_replace(project_duration: float, voiceovers: List[Dict]) -> AudioSegment:
    """
    Build final audio track by placing voiceovers onto a silent canvas.
    Overlapping rule: voiceover with later start_time should replace earlier audio in overlapping windows.
    voiceover dict fields expected: start_time (float seconds), src (path), duration (float seconds)
    """
    bg_volume_db = 0
    voice_volume_db = 0
    try:
        background = make_background_sound(project_duration, "interstallar.mp3")
        background = background + bg_volume_db          # duck the music
    except Exception as e:
        print(f"Warning: could not load background ({e}), proceeding with silence")
        background = AudioSegment.silent(duration=int(project_duration * 1000))

    # 2. Voice-over canvas (same size as background)
    vo_canvas = AudioSegment.silent(duration=len(background))

    # Sort by start_time so later VO overwrites earlier ones
    sorted_vo = sorted(voiceovers, key=lambda v: float(v["start_time"]))

    for vo in sorted_vo:
        start_ms = int(float(vo["start_time"]) * 1000)
        src = vo.get("src")
        if not src or not os.path.exists(src):
            continue

        try:
            seg = AudioSegment.from_file(src)
        except Exception as e:
            raise RuntimeError(f"Cannot load voiceover {src}: {e}")

        # optional: normalise / adjust voice level
        seg = seg + voice_volume_db

        # ---- replace slice in VO canvas (later VO overwrites) ----
        before = vo_canvas[:start_ms]
        after  = vo_canvas[start_ms + len(seg):]
        vo_canvas = before + seg + after

    # 3. Mix voice-over canvas on top of background
    final = background.overlay(vo_canvas)
    return final



def generate_mp4(project: Dict, output_path: str,
    target_size=None, target_fps=24, temp_dir=None):
    """
    project: dict containing "scenes" and "voiceovers" lists
    Each scene: {"start_time": float, "video_src": "path_or_url", "duration": float}
    Each voiceover: {"start_time": float, "src": "path_or_url", "duration": float, "timestamps": [...], "text_with_pauses": "..."}
    output_path: where to write the final mp4
    """

    if temp_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="proj_render_")

    scenes = project.get("scenes", [])
    voiceovers = project.get("voiceovers", [])

    print("project duration")
    # compute project duration as max end among scenes and voiceovers
    max_t = 0.0
    for s in scenes:
        st = float(s["start_time"])
        dur = float(s.get("duration", 0.0))
        max_t = max(max_t, st + dur)
    for v in voiceovers:
        st = float(v["start_time"])
        dur = float(v.get("duration", 0.0))
        max_t = max(max_t, st + dur)
    project_duration = max_t if max_t > 0 else 0.0

    if project_duration <= 0:
        raise ValueError("Project has zero duration")

    # === Build video composite ===
    # For layering precedence: sort scenes by start_time ascending; later start_time will be added to list later -> placed on top
    scenes_sorted = sorted(scenes, key=lambda x: float(x["start_time"]))

    video_clips = []
    base_size = None

    for s in scenes_sorted:
        src = s["video_src"]
        st = float(s["start_time"])
        dur = float(s.get("duration", None))
        # load clip

        if not src or not str(src).strip():
            print(f"Skipping scene at {st}s — no video_src: {s}")
            continue

        try:
            clip = VideoFileClip(src)
        except Exception as e:
            raise RuntimeError(f"Cannot load scene video {src}: {e}")

        # if scene specifies duration, cut to that duration
        if dur:
            clip = clip.subclipped(0, min(dur, clip.duration))

        # set start on timeline
        clip = clip.with_start(st)

        # determine base size if not set
        base_size = (VIDEO_W, VIDEO_H)
        if (clip.w, clip.h) != base_size:
            clip = clip.resize(newsize=base_size)

        # ensure clip duration doesn't exceed project duration unnecessarily
        # but CompositeVideoClip will handle it
        video_clips.append(clip)

    if not video_clips:
        print("No valid video scenes → using black background")
        # Use 1920x1080 as default, or fall back to 1280x720
        base_size = (VIDEO_W, VIDEO_H)
        composite = ColorClip(size=base_size, color=(111, 111, 111)).with_duration(project_duration)
    else:
        composite = CompositeVideoClip(video_clips, size=base_size).with_duration(project_duration)


    segments = []
    for vo in voiceovers:
        timestamps = vo.get("timestamps", [])
        segment_start_time = float(vo.get("start_time", 0.0))
        timestamps = json.loads(timestamps) if isinstance(timestamps, str) else timestamps
        text_with_pauses = vo.get("text_with_pauses", "")
        segs = prepare_segments(timestamps, text_with_pauses, segment_start_time)
        segments.extend(segs)

    print("prepared segments:")
    print(segments)

    composite = add_karaoke_subtitles(background=composite, segments=segments)

    composite = composite.with_fps(target_fps)


    # === Build audio by replacing overlapping voiceovers ===
    # Use pydub to create final audio segment
    final_audio_segment = assemble_audio_replace(project_duration, voiceovers)

    # write audio temporarily
    audio_tmp = os.path.join(temp_dir, f"audio_{uuid.uuid4().hex}.wav")
    final_audio_segment.export(audio_tmp, format="wav")
    # attach audio to video
    final_audio = AudioFileClip(audio_tmp)
    composite = composite.with_audio(final_audio).with_duration(project_duration)


    final = composite


        
    # === Write final file ===
    # Use reasonable codec settings; use audio codec aac, video codec libx264
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=target_fps, threads=4, preset="medium")

    # cleanup temp audio and srt
    try:
        os.remove(audio_tmp)
    except Exception:
        pass

    return output_path
