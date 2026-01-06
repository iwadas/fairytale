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
BG_MUSIC_PATH = 'static/default/sounds/'

def make_background_sound(project_duration: float, sound_name: str) -> AudioSegment:
    """Create background music AudioSegment of specified duration by looping/trimming a base track."""
    bg_path = os.path.join(BG_MUSIC_PATH, sound_name)

    if not os.path.exists(bg_path):
        raise FileNotFoundError(f"Background music not found: {bg_path}")

    bg = AudioSegment.from_file(bg_path)          # load once
    bg = bg.apply_gain(-2)
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



def assemble_audio_replace(project_duration: float, voiceovers: List[Dict], background_sound_name: str = "interstallar.mp3") -> AudioSegment:
    """
    Build final audio track by placing voiceovers onto a silent canvas.
    Overlapping rule: voiceover with later start_time should replace earlier audio in overlapping windows.
    voiceover dict fields expected: start_time (float seconds), src (path), duration (float seconds)
    """
    bg_volume_db = 0
    voice_volume_db = 0
    try:
        background = make_background_sound(project_duration, background_sound_name)
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