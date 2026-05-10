import os
from pydub import AudioSegment

BG_MUSIC_PATH = 'static/default/sounds/'

class AudioGenerator:
    def __init__(self, builder, temp_dir: str = "/tmp"):
        self._builder = builder
        self._temp_dir = temp_dir

    def generate(self) -> bool:
        # file to store audio
        project_duration = self._builder.get_project_duration()

        voiceovers = self._builder._project.get("voiceovers", [])
        sorted_voiceovers = sorted(voiceovers, key=lambda x: float(x.get("start_time", 0)))

        music = self._builder._project.get("background_music", [])
        sorted_music = sorted(music, key=lambda x: float(x.get("start_time", 0)))

        audio = AudioSegment.silent(duration=project_duration * 1000) 

        def add_segment(element, current_audio) -> AudioSegment:
            src = element.get("src")
            if not src or not os.path.exists(src):
                return current_audio # Return the unmodified audio instead of None
            
            try:
                seg = AudioSegment.from_file(src)
            except Exception as e:
                raise RuntimeError(f"Cannot load audio {src}: {e}")

            cut_start = int(float(element.get("cut_start", 0)) * 1000)
            cut_end = int(float(element.get("cut_end", 0)) * 1000)
            start_time = int(float(element.get("start_time", 0)) * 1000)

            # Slice the segment based on cuts
            seg_sliced = seg[cut_start:len(seg)-cut_end] if cut_end else seg[cut_start:]
            
            # Overlay onto the main timeline
            return current_audio.overlay(seg_sliced, position=start_time) 

        # Add all elements to the main audio track
        for m in sorted_music:
            audio = add_segment(m, audio)

        for vo in sorted_voiceovers:
            audio = add_segment(vo, audio)

        # Create a specific file path for the export
        # Export the final composite audio
        audio.export(self._temp_dir, format="wav")
        return True