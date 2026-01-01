from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ImageClip
# from moviepy.video.io.VideoFileClip import VideoFileClip
# from moviepy.video.VideoClip import TextClip, CompositeVideoClip, ImageClip
from moviepy import vfx
import numpy as np

# ───────────────────────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────────────────────
VIDEO_PATH = "static/videos/scenes/scene_f0b06d04-ce99-4f8e-9107-7aa6864ecb34.mp4"
OUTPUT_PATH = "static/videos/scenes/ZZZZnewfuckingnigger.mp4"

words_with_timing = [
    {"word": "TEST",             "start": 0.0,  "end": 0.5},
    {"word": "WORDS",            "start": 0.5,  "end": 1.0},
    {"word": "BEAUTIFULL",       "start": 1.5,  "end": 2.0},
    {"word": "KOEANIGSEEG",      "start": 2.0,  "end": 2.5},
    {"word": "TEdaST",           "start": 3.0,  "end": 3.5},
    {"word": "WORDS",            "start": 3.5,  "end": 4.0},
    # {"word": "SCREEN", "start": 4.5,  "end": 5.0},
]

FONT_PATH = 'static/default/fonts/bold.woff2'
FONT_SIZE = 100
TEXT_COLOR = 'white'
POSITION = ('center', 'center')

FPS = 30

# ───────────────────────────────────────────────────────────────
# MAIN LOGIC
# ───────────────────────────────────────────────────────────────

video = VideoFileClip(VIDEO_PATH).without_audio()

all_knocked_clips = []

for item in words_with_timing:
    txt = item["word"]
    t_start = item["start"]
    t_end = item["end"]
    duration = t_end - t_start

    text_clip = TextClip(
        text=txt,
        font=FONT_PATH,
        font_size=FONT_SIZE,
        color=TEXT_COLOR,
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
    pos_x = (video.w - w) // 2 if POSITION[0] == 'center' else POSITION[0]
    pos_y = (video.h - h) // 2 if POSITION[1] == 'center' else POSITION[1]

    full_mask_array[pos_y:pos_y + h, pos_x:pos_x + w] = mask_img
    # ───────────────────────────────────────────────────────────────

    full_mask_clip = ImageClip(full_mask_array, is_mask=True).with_duration(duration)

    # Create the inverted piece masked to text area
    inverted_piece = video.with_effects([vfx.InvertColors()]).subclipped(t_start, t_end).with_mask(full_mask_clip).with_start(t_start)

    all_knocked_clips.append(inverted_piece)

# ───────────────────────────────────────────────────────────────
# COMPOSITE EVERYTHING
# ───────────────────────────────────────────────────────────────

final = CompositeVideoClip([video] + all_knocked_clips)

# Restore audio if needed
if video.audio:
    final = final.with_audio(VideoFileClip(VIDEO_PATH).audio)

final.write_videofile(
    OUTPUT_PATH,
    fps=FPS,
    codec='libx264',
    audio_codec='aac',
    preset='medium',
    threads=4
)

print("Done! →", OUTPUT_PATH)