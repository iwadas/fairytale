
import os
import tempfile
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import uuid
from pydub import AudioSegment

from typing import List, Dict, Tuple, Any

from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, VideoClip, ImageClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.fx import CrossFadeIn
from moviepy import vfx
import json

import numpy as np

VIDEO_W, VIDEO_H = 704, 1248                # your video resolution
# VIDEO_W, VIDEO_H = 720, 1280                # your video resolution
MAX_LINE_WIDTH_PX = 500                     # max width of a *line* in px

COLOR_INACTIVE = "white"                    # colour of words that have not appeared yet
# COLOR_ACTIVE   = "#ffdd00"                # colour of the word that is currently sung
BORDER_COLOR   = None                       # optional outline
STROKE_COLOR   = "black"                    # outline colour (None = no outline)
STROKE_WIDTH   = 0
ALIGN = "center"                            # alignment inside the 500 px box
VALIGN = "bottom"                           # vertical alignment of the whole block
POS_Y = 800                                 # top coordinate of the *first* line
LINE_SPACING = 10
FADE_IN_DURATION = 0.4
DROP_DURATION = 0.4
DROP_OFFSET = 0
# FONT = 'backend/static/default/fonts/bahnschrift.ttf'
# FONT = 'static/default/fonts/DMSerifText-Regular.ttf'
# FONT = 'static/default/fonts/Unna-Regular.ttf'
FONT = 'static/default/fonts/bold.woff2'

WORD_GAP_PX = 6
BG_MUSIC_PATH = 'static/default/sounds/'
GLUE_PUNCTUATION = {",", ".", "?", "!", ":", ";", "-", "–"}


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
    # Normalize function
    def normalize(s: str) -> str:
        return s.strip().upper()  # You can adjust normalization (e.g. remove punctuation)

    # Prepare normalized timestamps for matching
    timestamp_words = [(normalize(ts["word"]), ts["time"]) for ts in timestamps]
    
    # add end time to words
    timestamps_with_end_time = []
    for i in range(len(timestamp_words) - 1):
        if timestamp_words[i][0] in GLUE_PUNCTUATION:
            continue
        timestamps_with_end_time.append({
            "word": timestamp_words[i][0],
            "start_time": segment_start_time + timestamp_words[i][1],
            "end_time": segment_start_time + min(timestamp_words[i + 1][1], timestamp_words[i][1] + 1.5)
        })
    # append last word
    if timestamp_words[-1][0] not in GLUE_PUNCTUATION:
        timestamps_with_end_time.append({
            "word": timestamp_words[-1][0],
            "start_time": segment_start_time + timestamp_words[-1][1],
            "end_time": segment_start_time + timestamp_words[-1][1] + 0.75
        })
    return timestamps_with_end_time


def add_karaoke_subtitles(
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

        text_clip = TextClip(
            text=txt,
            font=FONT,
            font_size=FONT_SIZE,
            stroke_color='black',
            stroke_width=2,
            method='label',
            margin=(0, 60),
            size=(video.w, None)
        )

        # ─── CREATE FULL-SIZE MASK ────────────────────────────────────
        mask_img = text_clip.mask.get_frame(0)  # numpy array (h, w) float 0-1, 1 at text
        h, w = mask_img.shape
        print("Mask size:", w, "x", h)


        full_mask_array = np.zeros((video.h, video.w), dtype=float)

        # Calculate position (assuming static 'center' for simplicity)
        pos_x = (VIDEO_W - w) // 2
        pos_y = (VIDEO_H - h) // 2

        full_mask_array[pos_y:pos_y + h, pos_x:pos_x + w] = mask_img
        # ───────────────────────────────────────────────────────────────

        full_mask_clip = ImageClip(full_mask_array, is_mask=True).with_duration(duration)

        # Create the inverted piece masked to text area
        inverted_piece = video.with_effects([vfx.InvertColors()]).subclipped(t_start, t_end).with_mask(full_mask_clip).with_start(t_start)

        all_knocked_clips.append(inverted_piece)
    return CompositeVideoClip([background] + all_knocked_clips)


def make_background_sound(project_duration: float, sound_name) -> AudioSegment:
    """Create background music AudioSegment of specified duration by looping/trimming a base track."""
    bg_path = os.path.join(BG_MUSIC_PATH, sound_name)

    if not os.path.exists(bg_path):
        raise FileNotFoundError(f"Background music not found: {bg_path}")

    bg = AudioSegment.from_file(bg_path)          # load once
    bg = bg.apply_gain(-4)
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
            clip = clip.resized([VIDEO_W, VIDEO_H])

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

    composite = add_karaoke_subtitles(background=composite, words_with_timing=segments)

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
