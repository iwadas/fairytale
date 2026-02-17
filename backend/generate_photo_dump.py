
import os
import random
import tempfile
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import uuid
from pydub import AudioSegment

from typing import List, Dict, Tuple, Any

from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, VideoClip, ImageClip, concatenate_videoclips
from moviepy.video.VideoClip import ImageClip
from moviepy.video.fx import CrossFadeIn
from moviepy import vfx
import json
from utils.add_sound_to_video import assemble_audio_replace

import numpy as np

from utils.invert_text_mask_color import generate_neon_text_with_border
from utils.invert_text_mask import generate_invert_mask_text
# from services import generate_speech, filename_from_name

GLUE_PUNCTUATION = {",", ".", "?", "!", ":", ";", "-", "–", "—"}

def prepare_word_timings(vo_timestamps, segment_start_time: float):
    def normalize(s: str) -> str:
        return s.strip().upper()  # You can adjust normalization (e.g. remove punctuation)

    # Prepare normalized timestamps for matching
    timestamp_words = [(normalize(ts["word"]), ts["time"]) for ts in vo_timestamps]
    
    # add end time to words
    timestamps_with_end_time = []
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


def generate_photo_dump_mp4(
    images: List[Any],
    voiceover: List[Any],
    title: str,    
):
    # TODO
    # [] Create a project with given title
    # [] Generate voiceover from story
    # [] Parse the voiceover so that we have timestamps for each word
    # [] Get all images from packages
    # -> [] Create video from the images
    # - There should be 4 random images per second
    # [] Add text overlays from the story at the right timestamps
    # [] Text overlays should have changed size and font based
    # [] Add background music
    # [] Export video
    # TEST WITH TIMESTAMPS
    
    vo_timestamps = voiceover.get("timestamps", [])
    words_timings = prepare_word_timings(vo_timestamps, segment_start_time=0.0)

    DURATION_PER_IMAGE = 0.15  # 10 images per second

    total_duration = voiceover.get("duration", 0.0)

    # 20 extra frames for start (.5s) and end (1.5s)
    number_of_images_to_show = int(total_duration / DURATION_PER_IMAGE) + 40

    images_paths = [img.src for img in images if img.src]
    clips = []
    previous_image = None
    for _ in range(number_of_images_to_show):
        # get a random image (not the same as previous)
        selected_image = random.choice(images_paths)
        while(selected_image == previous_image):
            selected_image = random.choice(images_paths)
        clip = ImageClip(selected_image, duration=DURATION_PER_IMAGE)
        # resize for full hd 9:16
        clip = clip.resized(height=1920, width=1080)
        clips.append(clip)

    video = concatenate_videoclips(clips, method='compose')
    
    video = generate_invert_mask_text(
        video_size=(video.w, video.h),
        fonts=[
            'static/default/fonts/bold.woff2',
        ],
        background=video,
        words_with_timing=words_timings,
    )


    temp_dir = tempfile.mkdtemp(prefix="proj_render_")
    audio_tmp = os.path.join(temp_dir, f"audio_{uuid.uuid4().hex}.wav")

    final_audio_segment = assemble_audio_replace(total_duration, [voiceover], background_sound_name="untitled13.mp3")
    final_audio_segment.export(audio_tmp, format="wav")

    final_audio = AudioFileClip(audio_tmp)
    video = video.with_audio(final_audio).with_duration(total_duration)

    # TODO - add title normalization
    output_path = f"videos/{title}.mp4"
    video.write_videofile(
        output_path,
        fps=20,
        codec="libx264",
    )
