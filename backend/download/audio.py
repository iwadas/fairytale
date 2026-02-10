import os
from typing import Any
import uuid
from backend.generate import make_background_sound
from builder import VideoBuilder
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, VideoClip, ImageClip
from pydub import AudioSegment
import tempfile

BG_MUSIC_PATH = 'static/default/sounds/'

class AudioGenerator:
    def __init__(self, builder: VideoBuilder, temp_dir: str = None):
        self._builder = builder
        self._temp_dir = temp_dir
    def generate(self):
        """
        project: dict containing "scenes" and "voiceovers" lists
        Each scene: {"start_time": float, "video_src": "path_or_url", "duration": float}
        Each voiceover: {"start_time": float, "src": "path_or_url", "duration": float, "timestamps": [...], "text_with_pauses": "..."}
        output_path: where to write the final mp4
        """

        # file to store audio
        project_duration = self._builder.get_project_duration()

        voiceovers = self._builder._project.get("voiceovers", [])
        sorted_voiceovers = sorted(voiceovers, key=lambda x: float(x["start_time"]))

        def make_background_sound(self) -> AudioSegment:
            """Create background music AudioSegment of specified duration by looping/trimming a base track."""
            
            bg_music = self._builder._bg_music
            if not bg_music:
                return AudioSegment.silent(duration=int(project_duration * 1000))

            bg_path = os.path.join(BG_MUSIC_PATH, bg_music)
            if not os.path.exists(bg_path):
                raise FileNotFoundError(f"Background music not found: {bg_path}")

            bg = AudioSegment.from_file(bg_path)          # load once
            # bg = bg.apply_gain(-2)
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

        try:
            background = make_background_sound()
            background = background          # duck the music
        except Exception as e:
            print(f"Warning: could not load background ({e}), proceeding with silence")
            background = AudioSegment.silent(duration=int(project_duration * 1000))

        for vo in sorted_voiceovers:
            src = vo.get("src")
            vo_start = int(float(vo["start_time"]) * 1000)
            if not src or not os.path.exists(src):
                continue
            try:
                seg = AudioSegment.from_file(src)
            except Exception as e:
                raise RuntimeError(f"Cannot load voiceover {src}: {e}")

            before = vo_canvas[:vo_start]
            after  = vo_canvas[vo_start + len(seg):]
            vo_canvas = before + seg + after


        final = background.overlay(vo_canvas)
        final.export(self._temp_dir, format="wav")
       