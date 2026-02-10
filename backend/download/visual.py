import os
import random
from typing import Any
from backend.generate import make_background_sound
from builder import VideoBuilder
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, VideoClip, ImageClip, concatenate_videoclips
from pydub import AudioSegment

BG_MUSIC_PATH = 'static/default/sounds/'

class VisualGenerator:
    def __init__(self, builder: VideoBuilder):
        self._builder = builder
    def generate(self) -> VideoClip:
        """
        project: dict containing "scenes" and "voiceovers" lists
        Each scene: {"start_time": float, "video_src": "path_or_url", "duration": float}
        Each voiceover: {"start_time": float, "src": "path_or_url", "duration": float, "timestamps": [...], "text_with_pauses": "..."}
        output_path: where to write the final mp4
        """
        project_duration = self._builder.get_project_duration()
        # PHOTODUMP LOGIC
        if self._builder.get_project_type() == "PHOTO_DUMP":
            number_of_images_to_show = int(project_duration / self._builder._pd_duration_per_image)
            # add padding images for start and end
            number_of_images_to_show += int((self._builder._pd_padding[0] + self._builder._pd_padding[1]) / self._builder._pd_duration_per_image)

            images_packages = self._builder._project.get("images_packages", [])
            if(not images_packages or len(images_packages) == 0):
                raise ValueError("No images packages found for PHOTO_DUMP project")
            images_paths = []
            for pkg in images_packages:
                imgs = pkg.get("images", [])
                images_paths.extend([img["src"] for img in imgs if img.get("src")])

            if len(images_paths) == 0:
                raise ValueError("No images found in images packages for PHOTO_DUMP project")
            
            clips = []
            previous_image = None

            for _ in range(number_of_images_to_show ):
                selected_image = random.choice(images_paths)
                while(selected_image == previous_image):
                    selected_image = random.choice(images_paths)
                    clip = ImageClip(selected_image, duration=self._builder._pd_duration_per_image)
                    clip = clip.resized(self._builder._resolution)
                    clips.append(clip)

            composite = concatenate_videoclips(clips, method='compose')
            return composite.with_duration(project_duration)
        else: 
            scenes = self._builder._project.get("scenes", [])
            scenes_sorted = sorted(scenes, key=lambda x: float(x["start_time"]))
            video_clips = []
            
            for s in scenes_sorted:
                src = s["video_src"]
                st = float(s["start_time"])
                dur = float(s.get("duration", None))

                if not src or not str(src).strip():
                    print(f"Skipping scene at {st}s — no video_src: {s}")
                    continue

                try:
                    clip = VideoFileClip(src)
                except Exception as e:
                    raise RuntimeError(f"Cannot load scene video {src}: {e}")

                if dur:
                    clip = clip.subclipped(0, min(dur, clip.duration))

                clip = clip.with_start(st)

                if (clip.w, clip.h) != base_size:
                    clip = clip.resized(self._builder._resolution)

                video_clips.append(clip)

            if not video_clips:
                print("No valid video scenes → using black background")
                base_size = self._builder._resolution
                composite = ColorClip(size=base_size, color=(111, 111, 111)).with_duration(project_duration)
            else:
                composite = CompositeVideoClip(video_clips, size=base_size).with_duration(project_duration)
            return composite



