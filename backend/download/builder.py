import os
import random
from typing import List, Any
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips

import tempfile
import uuid

from .audio import AudioGenerator
from .visual import VisualGenerator
from .subtitles import SubtitleGenerator


class VideoBuilder:
    def __init__(self, project: Any, output_filename: str):
        self._project = project
        self._output_filename = output_filename
        # BASE
        self._resolution = (720, 1280) 
        self._fps = 24
        # SUBTITLES
        self._subtitle_type = "border" 
        self._subtitle_color = "white"
        self._subtitle_special_color = "rgb(230, 163, 49)"
        self._fonts = set()
        self._subtitle_shadow = False
        self._subtitle_border = {"width": 0, "color": "white"}
        
        self._vignette = False
        self._pd_padding = (0.5, 1)
        self._pd_duration_per_image = 0.15

    def get_project_type(self) -> str:
        if self._project["type"] == "PHOTO_DUMP" or self._project["name"].lower().find("photo dump") != -1:
            return "PHOTO_DUMP"
        else:
            return "BASIC"
        
    def get_project_duration(self) -> float:
        if self.get_project_type() == "PHOTO_DUMP":
            # Sum durations of all visual 
            voiceover_duration = self._project["voiceovers"][0]["duration"] if self._project.get("voiceovers") else 0.0
            return self._pd_padding[0] + voiceover_duration + self._pd_padding[1]
        else:
            max_end = 0.0
            for v in self._project.get("scenes", []):
                max_end = max(max_end, self.get_element_end_time(v))
            for v in self._project.get("voiceovers", []):
                max_end = max(max_end, self.get_element_end_time(v))
            for m in self._project.get("background_music", []):
                max_end = max(max_end, self.get_element_end_time(m))

            return max_end

    # --- Fluent Interface Setters ---
    def set_resolution(self, width: int, height: int) -> "VideoBuilder":
        self._resolution = (width, height)
        return self

    def add_vignette(self) -> "VideoBuilder":
        self._vignette = True
        return self

    def set_subtitle_style(self, style: str) -> "VideoBuilder":
        if( style not in ["none", "invert_mask", "border", "karaoke", "karaoke_remotion"]):
            raise ValueError(f"Unsupported subtitle style: {style}, must be one of none, invert_mask, border, karaoke")
        self._subtitle_type = style
        return self
    
    def set_subtitle_border(self, width: int, color: str) -> "VideoBuilder":
        self._subtitle_border = {"width": width, "color": color}
        return self

    def set_subtitle_color(self, color: str) -> "VideoBuilder":
        self._subtitle_color = color
        return self

    def set_subtitle_special_color(self, color: str) -> "VideoBuilder":
        self._subtitle_special_color = color
        return self

    def add_subtitle_shadow(self) -> "VideoBuilder":
        self._subtitle_shadow = True
        return self

    def pd_set_duration_per_image(self, duration: float) -> "VideoBuilder":
        self._pd_duration_per_image = duration
        return self
    
    def add_font(self, font_path: str) -> "VideoBuilder":
        self._fonts.add(font_path)
        return self

    def get_element_duration(self, element: dict) -> float:
        return float(element.get("duration", 0.0)) - float(element.get("cut_end", 0.0)) - float(element.get("cut_start", 0.0))
    
    def get_element_end_time(self, element: dict) -> float:
        return float(element.get("start_time", 0.0)) + self.get_element_duration(element)



    def validate(self):
        pass

    def build(self):

        self.validate()

        print(f"Building {self._output_filename}...")

        temp_dir = tempfile.mkdtemp(prefix="proj_render_")
        audio_tmp = os.path.join(temp_dir, f"audio_{uuid.uuid4().hex}.wav")

        if not AudioGenerator(self, temp_dir=audio_tmp).generate():
            raise RuntimeError("Failed to generate audio")

        visuals = VisualGenerator(self).generate()
        visuals_and_subtitles = SubtitleGenerator(builder=self, visuals=visuals).generate()

        # COMBINE VISUALS + SUBTITLES + AUDIO
        final = visuals_and_subtitles\
            .with_audio(AudioFileClip(audio_tmp))\
            .with_duration(self.get_project_duration())\
            .with_fps(self._fps)\

        final.size = self._resolution
        
        final = final

        final.write_videofile(
            self._output_filename, 
            fps=self._fps, 
            codec="libx264", 
            audio_codec="aac",
            threads=4
        ) 


        
        if os.path.exists(audio_tmp):
            os.remove(audio_tmp)


        return self._output_filename
        