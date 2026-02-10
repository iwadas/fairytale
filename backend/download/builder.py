import os
import random
from typing import List, Any
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips

# Import your legacy effects (keeping them as is for now)
from utils.invert_text_mask import generate_invert_mask_text
from utils.invert_text_mask_color import generate_neon_text_with_border
from utils.add_br_vignette import vignette_bottom

from models import SubtitleConfig, AudioTrack, VisualAsset
from processors import TimestampProcessor, AudioMixer

import tempfile
import uuid

from audio import AudioGenerator
from visual import VisualGenerator


class VideoBuilder:
    def __init__(self, project: Any, output_filename: str):
        self._project = project
        self._output_filename = output_filename
        # BASE
        self._resolution = (720, 1280) 
        self._fps = 24
        # SUBTITLES
        self._subtitle_type = "invert_mask" 
        self._subtitle_color = "white"
        self._fonts = set()
        self._subtitle_shadow = False
        self._subtitle_border = {"width": 2, "color": "white"}
        self._bg_music = None
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
                dur = float(v.get("duration", 5.0)) # Default fallback
                st = float(v.get("start_time", 0.0))
                max_end = max(max_end, st + dur)
            for a in self._project.get("voiceovers", []):
                dur = float(a.get("duration", 5.0))
                st = float(a.get("start_time", 0.0))
                max_end = max(max_end, st + dur)
            return max_end

    # --- Fluent Interface Setters ---
    def set_resolution(self, width: int, height: int) -> "VideoBuilder":
        self._resolution = (width, height)
        return self

    def add_background_music(self, path: str) -> "VideoBuilder":
        self._bg_music = path
        return self

    def add_vignette(self) -> "VideoBuilder":
        self._vignette = True
        return self

    def set_subtitle_style(self, style: str) -> "VideoBuilder":
        if( style not in ["none", "invert_mask", "neon"]):
            raise ValueError(f"Unsupported subtitle style: {style}, must be one of none, invert_mask, neon")
        self._subtitle_type = style
        return self
    
    def set_subtitle_border(self, width: int, color: str) -> "VideoBuilder":
        self._subtitle_border = {"width": width, "color": color}
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

    def validate(self):
        pass

    def build(self):

        self.validate()

        print(f"Building {self.output_filename}...")

        if(self._builder._project.get("type") == "PHOTO_DUMP"):
            self._builder._project.get("voiceovers", [])[0]["start_time"] = self._builder._pd_padding[0]

        # SAVE AUDIO IN TEMP DIR
        temp_dir = tempfile.mkdtemp(prefix="proj_render_")
        audio_tmp = os.path.join(temp_dir, f"audio_{uuid.uuid4().hex}.wav")
        audio_generator = AudioGenerator(self, temp_dir=audio_tmp)
        # COMBINES BACKGROUND MUSIC + VOICEOVERS
        audio_generator.generate()

        # CONSTRUCT VISUALS (SCENES / PHOTO_DUMP)
        vis_gen = VisualGenerator(self)
        raw_video = vis_gen.generate()





        
     
        # 2. Construct Visual Timeline
        clips = []
        for asset in self._visual_assets:
            if asset.asset_type == "video":
                clip = VideoFileClip(asset.file_path)
                if asset.duration:
                    clip = clip.subclip(0, min(asset.duration, clip.duration))
                clip = clip.set_start(asset.start_time)
            elif asset.asset_type == "image":
                clip = ImageClip(asset.file_path).set_duration(asset.duration)
                # For photo dump, we usually concat, but for general builder we might layer
                if self._is_photo_dump:
                    clips.append(clip) # collected for concatenation
                    continue 
                else:
                    clip = clip.set_start(asset.start_time)
            
            # Resize logic (centralized)
            if (clip.w, clip.h) != self.resolution:
                clip = clip.resize(newsize=self.resolution) # or height=...
            
            if not self._is_photo_dump:
                clips.append(clip)

        # 3. Compositing
        if self._is_photo_dump:
            # Photo dump uses concatenation
            base_video = concatenate_videoclips(clips, method="compose")
            base_video = base_video.resize(self.resolution)
        else:
            # Standard uses layering
            base_video = CompositeVideoClip(clips, size=self.resolution).set_duration(self.duration)

        # 4. Apply Subtitles
        # Gather all words from all voiceovers
        all_words = []
        for vo in self._audio_tracks:
            if vo.transcript:
                words = TimestampProcessor.process_timings(vo.transcript, start_offset=vo.start_time)
                all_words.extend(words)

        if all_words and self._subtitle_config.style != "none":
            if self._subtitle_config.style == "neon":
                base_video = generate_neon_text_with_border(
                    video_size=self.resolution,
                    fonts=[self._subtitle_config.font_path],
                    background=base_video,
                    words_with_timing=all_words
                )
            elif self._subtitle_config.style == "invert_mask":
                base_video = generate_invert_mask_text(
                    video_size=self.resolution,
                    fonts=[self._subtitle_config.font_path],
                    background=base_video,
                    words_with_timing=all_words
                )

        # 5. Apply Vignette
        if self._vignette:
            base_video = vignette_bottom(self.resolution, base_video)

        # 6. Audio Mixing
        final_audio_path = AudioMixer.mix_tracks(
            self.duration, 
            self._bg_music_path, 
            self._audio_tracks
        )
        
        final_video = base_video.set_audio(AudioFileClip(final_audio_path))

        # 7. Render
        final_video.write_videofile(
            self.output_filename, 
            fps=self.fps, 
            codec="libx264", 
            audio_codec="aac",
            threads=4
        )
        
        # Cleanup
        if os.path.exists(final_audio_path):
            os.remove(final_audio_path)

        return self.output_filename