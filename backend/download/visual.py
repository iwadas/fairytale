import os
import random
from typing import Any, List
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, VideoClip, ImageClip, concatenate_videoclips
from pydub import AudioSegment

BG_MUSIC_PATH = 'static/default/sounds/'

class VisualGenerator:
    def __init__(self, builder: Any):
        self._builder = builder

    def generate(self) -> VideoClip:
        """
        project: dict containing "scenes" and "voiceovers" lists
        Each scene: {"start_time": float, "video_src": "path_or_url", "duration": float}
        Each voiceover: {"start_time": float, "src": "path_or_url", "duration": float, "timestamps": [...], "text_with_pauses": "..."}
        output_path: where to write the final mp4
        """
        project_duration = self._builder.get_project_duration()

        scenes = self._builder._project.get("scenes", [])
        
        layers = {}
        for s in scenes:
            layer = s.get("layer", 0)
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(s)


        def add_scene(scene, video_clips: List[VideoClip]) -> List[VideoClip]:
            src = scene.get("video_src")
            start_time = float(scene["start_time"])
            cut_start = float(scene.get("cut_start", 0))
            cut_end = float(scene.get("cut_end", 0))
            
            if not src or not str(src).strip():
                print(f"Skipping scene at {start_time}s — no video_src: {scene}")
                return None
            
            try:
                clip = VideoFileClip(src)
            except Exception as e:
                raise RuntimeError(f"Cannot load scene video {src}: {e}")
            
            clip = clip.subclipped(cut_start, self._builder.get_element_duration(scene) + cut_start)
            clip = clip.with_start(start_time)

            target_w, target_h = self._builder._resolution

            if (clip.w, clip.h) != (target_w, target_h):
                width_ratio = target_w / clip.w
                height_ratio = target_h / clip.h
                
                # 2. Pick the smaller ratio so the clip doesn't overflow the screen
                scale_factor = min(width_ratio, height_ratio)
                
                # 3. Apply the scale factor to the original dimensions
                new_w = int(clip.w * scale_factor)
                new_h = int(clip.h * scale_factor)
                
                # 4. Resize the clip using the new proportional dimensions
                clip = clip.resized(new_size=(new_w, new_h))
                
                # 5. Center it! (Crucial if you are compositing)
                clip = clip.with_position("center")

            video_clips.append(clip)

        video_clips = []

        for layer, scenes in sorted(layers.items(), reverse=True):
            scenes_sorted = sorted(scenes, key=lambda x: float(x["start_time"]))
            
            for i, s in enumerate(scenes_sorted):
                add_scene(s, video_clips)
                

        return CompositeVideoClip(video_clips, size=self._builder._resolution).with_duration(project_duration)


