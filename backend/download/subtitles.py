from typing import List, Tuple, Dict, Any
from moviepy import VideoClip

# MOVIEPY IMPORTS
from moviepy import VideoClip

from .text.border_text_generator import generate_border_text
from .text.invert_text_mask import generate_invert_mask_text
from .text.karaoke_text import generate_karaoke_text

GLUE_PUNCTUATION = {",", ".", "?", "!", ":", ";", "-", "–", "—"}


class SubtitleGenerator:
    def __init__(self, builder: Any, visuals: VideoClip = None):
        self._builder = builder
        self._visuals = visuals

    def generate(self) -> VideoClip:

        subtitle_type = self._builder._subtitle_type

        if subtitle_type == "invert_mask":
            return InvertTextMaskSubtitleGenerator(self._builder, self._visuals).generate()
        elif subtitle_type == "border":
            return BorderSubtitleGenerator(self._builder, self._visuals).generate()
        elif subtitle_type == "karaoke":
            return KaraokeSubtitleGenerator(self._builder, self._visuals).generate()
        else:
            if(subtitle_type != "none"):
                print(f"Unknown subtitle type: {subtitle_type}. Defaulting to 'None'")
            return self._visuals
            
        

class WordFormattingGenerator:
    def __init__(self, type: str, voiceovers: List[Any]):
        self._type = type
        self._voiceovers = voiceovers

    def generate(self):
        if self._type == "single_word":
            def prepare_voiceover(vo_timestamps, vo_start_time: float):
                def normalize(s: str) -> str:
                    s = s.strip().upper()  # You can adjust normalization (e.g. remove punctuation)
                    while s[0] in GLUE_PUNCTUATION:
                        s = s[1:]
                    while s[-1] in GLUE_PUNCTUATION:
                        s = s[:-1]
                    return s
                for i in range(len(vo_timestamps)):
                    vo_timestamps[i]["word"] = normalize(vo_timestamps[i]["word"])
                    vo_timestamps[i]["start"] = float(vo_timestamps[i]["start"]) + vo_start_time
                    vo_timestamps[i]["end"] = vo_timestamps[i]["end"] + vo_start_time
                return vo_timestamps
            
            result = []
            for vo in self._voiceovers:
                prepared_voiceover = prepare_voiceover(vo.get("timestamps", []), float(vo.get("start_time", 0.0)))
                result.extend(prepared_voiceover)
            
            return result

        elif self._type == "karaoke":

            # each 'karaoke_part' contains:
            # 'start' -> when the part appears
            # 'end' -> when the part disappears
            # 'words' -> list of words in the part, each with its own 'start' and 'end' relative to the part's start
            segments = []

            for vo in self._voiceovers:
                # split the text_with_pauses - with the element that has the work "[PAUSE]" as the separator - into segments
                text_with_pauses = vo.get("text_with_pauses", [])
                current_segment = {"words": [], "start": None, "end": None}
                new_segment = True

                vo_start_time = float(vo.get("start_time", 0.0))

                for item in text_with_pauses:
                    if new_segment:
                        current_segment["start"] = float(item.get("time", 0.0)) + vo_start_time
                        new_segment = False

                    if item.get("word") == "[PAUSE]":
                        if current_segment:
                            segments.append(current_segment)
                            current_segment = {"words": [], "start": None, "end": None}
                            new_segment = True
                    else:
                        word_start = float(item.get("start", 0.0)) + vo_start_time
                        word_end = float(item.get("end", 0.0)) + vo_start_time
                        is_special = item.get("is_special", False)
                        word = item.get("word", "")
                        current_segment["words"].append({
                            "word": word.upper() if is_special else word,
                            "is_special": is_special,
                            "start": word_start,
                            "end": word_end
                        })
                        current_segment["end"] = word_end
                if current_segment and current_segment.get("words"):
                        segments.append(current_segment)

            # For karaoke, we will prepare segments with words and timing based on timestamps and text with pauses ('|').
            # This is more complex and will be handled in the KaraokeSubtitleGenerator.
            return segments
    

class InvertTextMaskSubtitleGenerator:
    def __init__(self, builder: Any, visuals: VideoClip = None):
        self._builder = builder
        self._visuals = visuals

    def generate(self) -> VideoClip:
        voiceover_data = WordFormattingGenerator(type="single_word", voiceovers=self._builder._project.get("voiceovers", [])).generate()
        return generate_invert_mask_text(
            video_size=self._builder._resolution,
            voiceover_data=voiceover_data,
            fonts=self._builder._fonts,
            visuals=self._visuals,
            add_border=self._builder._subtitle_border is not None
        )
    
class BorderSubtitleGenerator:
    def __init__(self, builder: Any, visuals: VideoClip = None):
        self._builder = builder
        self._visuals = visuals

    def generate(self) -> VideoClip:
        voiceover_data = WordFormattingGenerator(type="single_word", voiceovers=self._builder._project.get("voiceovers", [])).generate()
        return generate_border_text(
            video_size=self._builder._resolution,
            voiceover_data=voiceover_data,
            fonts=self._builder._fonts,
            visuals=self._visuals,
        )

class KaraokeSubtitleGenerator:
    def __init__(self, builder: Any, visuals: VideoClip = None):
        self._builder = builder
        self._visuals = visuals

    def generate(self) -> VideoClip:
        voiceovers = self._builder._project.get("voiceovers", [])

        """
        visuals : your original MoviePy clip (or CompositeVideoClip)
        segments   : list of dicts exactly as you described
        Returns a new clip with the karaoke subtitles composited on top.
        """

        segments = WordFormattingGenerator(type="karaoke", voiceovers=voiceovers).generate()

        return generate_karaoke_text(
            segments=segments,
            visuals=self._visuals,
            options={
                "font": self._builder._fonts.pop() or 'DEFAULT_FONT',
                "color": self._builder._subtitle_color or 'white',
                "special_color": self._builder._subtitle_special_color or 'rgb(230, 163, 49)',
                "shadow": self._builder._subtitle_shadow,
                "video_size": self._builder._resolution,
                "border": self._builder._subtitle_border
            }
        )