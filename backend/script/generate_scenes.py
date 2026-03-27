from typing import Dict, List, Callable, Optional, Any
from pydantic import BaseModel, Field
import math
import json
# Assuming AI.llm import exists in your environment
from AI.llm import LLM
import asyncio
import re

# ==========================================
# CONFIGURATION & MODELS
# ==========================================
# (AVAILABLE_STYLES dict remains exactly the same as before)
AVAILABLE_STYLES_DARK_PSYCHOLOGY = {
    # ==============================
    # MACRO (Extreme Close-Ups & Portraits)
    # ==============================
    "macro_literal": {
        "use_case": "Use for extreme close-ups of specific physical actions or biological forms mentioned in the script (e.g., an eye twitching, a hand clenching).",
        "technical_prompt": (
            "Extreme macro photography, tight framing on a specific physical or biological subject from the script. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The subject must be highly recognizable but constructed entirely from non-organic materials. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            "Visual motif: pristine Matte Bone White being slowly overtaken by creeping Iridescent Oil Slick. "
            "Background is blurred deep shadow. "
            ", hyper-realistic 3D render, stark chiaroscuro studio lighting, piercing crimson and cold cyan rim lights (signaling aggression/manipulation), extreme macro photography depth of field, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k. 1:1 aspect ratio."
        )
    },
    "macro_metaphor": {
        "use_case": "Use for extreme close-ups of symbolic objects representing an idea (e.g., a fractured mirror for identity, a heavy chain for addiction).",
        "technical_prompt": (
            "Extreme macro photography, tight framing on a symbolic object representing the script's core theme. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The symbolic object is physically grounded but surreal, fracturing or trapped by sharp geometric forms. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            ", hyper-realistic 3D render, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, flickering sodium yellow rim lights (signaling anxiety/paranoia), engulfing pitch-black shadows, shallow depth of field, Octane render, raytracing, heavy caustics, paranoia aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "macro_portrait": {
        "use_case": "Use to give a 'face' to the emotion without showing a real human. Best for representing the manipulator, the victim, or a shattered ego.",
        "technical_prompt": (
            "Extreme macro portrait photography of a faceless, humanoid feature—like a shattered porcelain mask, a featureless chrome silhouette, or a bone-white hand. "
            "STRICTLY NO literal text, real human skin, or recognizable eyes. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            "Visual motif: A pristine surface fracturing to reveal Vantablack underneath. "
            ", hyper-realistic 3D render, stark chiaroscuro studio lighting, clinical cold white rim light against pure pitch-black shadows (signaling isolation/depression), shallow depth of field, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k. 1:1 aspect ratio."
        )
    },

    # ==============================
    # MEDIUM (Action & Power Dynamics)
    # ==============================
    "medium_dynamic": {
        "use_case": "Use for scenes showing interaction, power struggles, mirroring, or gaslighting between two entities.",
        "technical_prompt": (
            "Medium shot, dynamic composition showing two distinct abstract humanoid figures interacting in a power struggle. "
            "STRICTLY NO literal text or real humans. "
            "Figures must be constructed of contrasting materials: a towering Polished Black Obsidian figure casting a shadow over a fragile Matte Bone White or Smoked Crimson Glass figure. "
            ", hyper-realistic 3D render, striking contrast, stark chiaroscuro studio lighting, piercing crimson rim light against cold cyan fill (signaling conflict and dominance), heavy shadows, cinematic depth of field, Octane render, raytracing, psychological tension aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "kinetic_tethers": {
        "use_case": "Use to visually represent the hidden mechanisms of control, such as trauma bonding, emotional attachments, or manipulation.",
        "technical_prompt": (
            "Medium-close shot focusing entirely on the physical connection between two unseen points. "
            "STRICTLY NO literal text. "
            "Visual focus on kinetic elements of control: heavy Liquid Chrome chains, glowing Smoked Deep Crimson glass threads, or Iridescent Oil Slick bridging a gap. "
            "Background is an infinite dark void. "
            ", hyper-realistic 3D render, glowing internal light transmission, stark chiaroscuro lighting, flickering sodium yellow rim lights, deep focus, Octane render, raytracing, heavy caustics, clinical psychological mood, 8k. 1:1 aspect ratio."
        )
    },

    # ==============================
    # WIDE & TEXTURE (Environments / Pure Mood)
    # ==============================
    "wide_metaphor": {
        "use_case": "Use for themes of feeling trapped, cornered, or navigating a complex psychological issue (e.g., a maze, a cage, a giant monolithic obstacle).",
        "technical_prompt": (
            "Wide-angle monolithic scale, a tiny focal point surrounded by massive, overwhelming, metaphorical architecture (like a cage, labyrinth, or imposing monolith). "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The tiny subject provides emotional scale against architecture entirely constructed from sharp, fractured, and splintered geometric forms. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            ", hyper-realistic 3D render, claustrophobic but vast composition, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, pure clinical white and Vantablack contrast (signaling hopelessness), deep focus, Octane render, raytracing, isolation aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "texture_abstract": {
        "use_case": "Use as b-roll for pure tension, transitions, shifting brain chemistry, or to represent the abstract 'feeling' of an emotional breakdown.",
        "technical_prompt": (
            "Frame completely filled with chaotic abstract fluid dynamics, shifting particles, and fracturing geometry. "
            "STRICTLY NO literal text or recognizable macroscopic/human objects. "
            "A pure study of tension: melting surfaces, warping viscous liquids, or sharp splinters. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            ", hyper-realistic 3D render, fluid simulation, stark chiaroscuro studio lighting, piercing crimson rim lights pulsing through engulfing pitch-black shadows, macro photography depth of field, Octane render, raytracing, heavy caustics, gaslighting aesthetic, 8k. 1:1 aspect ratio."
        )
    }
}

MATERIALS_PALETTE = "Frost-Bitten Carrara Marble, Brushed Champagne Gold / Rhodium, Midnight Blue Silk Satin, Antique Mercury Glass, Chipped Alabaster, Black Mother-of-Pearl"

MATERIALS_PALETTE_DARK_PSYCHOLOGY = "Polished Marble, Obisdian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, Emerald Velvet"

AVAILABLE_STYLES_OLD = {
    # ==============================
    # MACRO (Extreme Close-Ups & Portraits)
    # ==============================
    # "macro_literal": {
    #     "use_case": "Use for extreme close-ups of specific physical actions or biological forms mentioned in the script (e.g., an eye twitching, a hand clenching).",
    #     "technical_prompt": (
    #         "Extreme macro photography, tight framing on a specific physical or biological subject from the script. "
    #         "STRICTLY NO literal text, typography, or spelled-out words. "
    #         "The subject must be highly recognizable but constructed entirely from non-organic materials. "
    #         "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
    #         "Visual motif: pristine Polished Marble being slowly overtaken by fracturing Obsidian and filaments of Distressed Tobacco Leather stitching. "
    #         "Atmosphere: dense suspension of microscopic obsidian dust particles, heavy volumetric mist with floating light orbs catching the light, complex horizontal anamorphic flares. "
    #         ", hyper-realistic 3D render, low-key studio lighting with stark chiaroscuro, deep shadows, and piercing crimson and cold cyan rim accents (signaling aggression/manipulation). "
    #         "Aggressive ultra-shallow depth of field: razor-sharp micro-focus on the central texture with surrounding edges melting into a heavy, creamy bokeh blur to isolate the subject. "
    #         "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, psychological thriller mood, 8k. 1:1 aspect ratio."
    #     )
    # },
    "macro_metaphor": {
        "use_case": "Use for extreme close-ups of symbolic objects representing an idea (e.g., a fractured mirror for identity, a heavy chain for addiction).",
        "technical_prompt": (
            "Extreme macro photography, tight framing on a symbolic object representing the script's core theme. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The symbolic object is physically grounded but surreal, fracturing or trapped by sharp geometric forms. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual motif: Fractured Crystal Glassware trapped by sharp Obsidian geometric forms. "
            "Atmosphere: thousands of floating microscopic sparks, intense optical bloom radiating from crystal and obsidian surfaces, thick shadow haze. "
            ", hyper-realistic 3D render, flawless ultra-reflective surfaces, low-key studio lighting with stark chiaroscuro, engulfing pitch-black shadows and flickering emerald green rim accents (signaling anxiety/paranoia). "
            "Pinpoint selective focus on the core fracture or symbol, with foreground and background elements rendered as a distorting, out-of-focus optical blur. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, paranoia aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "macro_portrait": {
        "use_case": "Use to give a 'face' to the emotion without showing a real human. Best for representing the manipulator, the victim, or a shattered ego.",
        "technical_prompt": (
            "Extreme macro portrait photography of a faceless, humanoid feature—like a shattered skull of Matte Black Metal, a featureless Obsidian profile, or a Polished Marble hand. "
            "STRICTLY NO literal text, real human skin, or recognizable eyes. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual motif: A pristine Polished Marble surface fracturing to reveal Emerald Velvet underneath, held together by tiny, intricate Antique Gold mechanisms. "
            "Atmosphere: atmospheric scattering around the cold rim light, faint ethereal wisps of shadow, suspended dust motes, heavy volumetric fog. "
            ", hyper-realistic 3D render, low-key studio lighting with stark chiaroscuro, clinical cold white rim accents against pure pitch-black shadows (signaling isolation/depression). "
            "Extreme lens compression: sharp focal plane on the 'face's' leading edge, while the rest of the head dissolves into an atmospheric, ghostly background blur. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, psychological thriller mood, 8k. 1:1 aspect ratio."
        )
    },

    # ==============================
    # MEDIUM (Action & Power Dynamics)
    # ==============================
    "medium_dynamic": {
        "use_case": "Use for scenes showing interaction, power struggles, mirroring, or gaslighting between two entities.",
        "technical_prompt": (
            "Medium shot, dynamic composition showing two distinct abstract humanoid figures interacting in a power struggle, set within an boundless, impossible geometric environment constructed from interlinked Polished Marble floors and towering Obsidian structures that fill the entire background frame, creating a disorienting, endless maze feel. "
            "STRICTLY NO literal text, real humans, typography, or spelled-out words. "
            "The environment includes massive floating geometric cubes, fracturing arches, and shifting prisms. "
            "Figures must be constructed of contrasting materials: a towering Matte Black Metal figure casting an oppressive shadow over a fragile, cracking Polished Marble figure. "
            "Visual details: visible internal clockwork mechanisms of Antique Gold and Obsidian within the metal figure's chest, geometric furniture constructed from Antique Gold and Distressed Tobacco Leather. "
            "Atmosphere: rolling volumetric mist swirling around their bases and through the infinite geometric architecture, thousands of floating geometric particles catching the light, complex horizontal anamorphic flares. "
            ", hyper-realistic 3D render, striking contrast, low-key studio lighting with stark chiaroscuro, piercing crimson rim light against cold cyan fill accents (signaling conflict and dominance), heavy shadows, sharp geometric shadows cast by the lighting. "
            "Cinematic rack-focus effect: sharp subject isolation on the fragile marble figure, while the towering metal figure and the extensive, complex geometric background maze loom as an oppressive, heavily blurred mass in the foreground and far background. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, psychological tension aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "kinetic_tethers": {
        "use_case": "Use to visually represent the hidden mechanisms of control, such as trauma bonding, emotional attachments, or manipulation.",
        "technical_prompt": (
            "Medium-close shot focusing entirely on the physical connection between two unseen points. "
            "STRICTLY NO literal text. "
            "Visual focus on kinetic elements of control: heavy chains of Matte Black Metal and Obsidian, cords of Distressed Tobacco Leather with visible wear and Antique Gold buckles, or spilling shards of Crystal Glassware bridging a gap. "
            "Visual details: visible micro-etchings and symbols on gold and leather. "
            "Atmosphere: dense particle fields of glass shards, leather dust, and glowing blue optical lines, heavy volumetric fog revealing rim lights. "
            ", hyper-realistic 3D render, glowing internal light transmission, low-key studio lighting with stark chiaroscuro, flickering emerald green rim accents. "
            "Hypnotic depth of field: the center of the tether is hyper-focused and tactile, fading seamlessly into a soft, ethereal blur and massive overlapping bokeh circles. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, clinical psychological mood, 8k. 1:1 aspect ratio."
        )
    },

    # ==============================
    # WIDE & TEXTURE (Environments / Pure Mood)
    # ==============================
    "wide_metaphor": {
        "use_case": "Use for themes of feeling trapped, cornered, or navigating a complex psychological issue (e.g., a maze, a cage, a giant monolithic obstacle).",
        "technical_prompt": (
            "Wide-angle vast monolithic scale, focusing on a single, tiny focal subject providing emotional scale against a overwhelming, boundless, and inescapable geometric room/landscape that fills the entire frame. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The extensive, claustrophobic environment is a matrix of interlinked, shifting geometric forms: massive Polished Marble cubes, fractured Obsidian prisms, and complex Matte Black Metal girders wrapped in Emerald Velvet and accented with Distressed Tobacco Leather trim and Antique Gold details, extending into an oppressive, endless pattern. "
            "Atmosphere: dense atmospheric scattering obscuring the impossible heights of the architecture, cinematic haze, distant out-of-focus light blooms, thousands of microscopic crystal shards floating in the air. "
            ", hyper-realistic 3D render, claustrophobic but vast composition, flawless ultra-reflective surfaces, low-key studio lighting with stark chiaroscuro, pure clinical white accents against engulfing pitch-black shadows (signaling hopelessness), lights integrated into the geometric architecture casting sharp, conflicting shadows. "
            "Tilt-shift lens effect: a narrow band of sharp focus traps the tiny subject, while the towering, boundless geometric architecture above, below, and behind is blurred out, emphasizing a sense of miniature vulnerability within overwhelming complexity. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, isolation aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "texture_abstract": {
        "use_case": "Use as b-roll for pure tension, transitions, shifting brain chemistry, or to represent the abstract 'feeling' of an emotional breakdown.",
        "technical_prompt": (
            "Frame completely filled with chaotic abstract fluid dynamics, shifting particles, and fracturing geometry. "
            "STRICTLY NO literal text or recognizable macroscopic/human objects. "
            "A pure study of tension: melting surfaces of Emerald Velvet and viscous, swirling Obsidian, warping viscous liquids like Antique Mercury Glass, or sharp splinters of Crystal Glassware and Matte Black Metal. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual details: individual threads of velvet dissolving, micro-shards of crystal and metal fragments colliding. "
            "Atmosphere: thick micro-clutter of floating particulate matter, intense horizontal anamorphic flares from crimson lights, optical bloom bleeding over edges of splinters. "
            ", hyper-realistic 3D render, fluid simulation, low-key studio lighting with stark chiaroscuro, piercing crimson rim accents pulsing through engulfing pitch-black shadows. "
            "Dynamic focal shifts: razor-sharp, hyper-focused Matte Black Metal splinters cutting through a background of heavy motion blur and swirling out-of-focus viscous fluids. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, gaslighting aesthetic, 8k. 1:1 aspect ratio."
        )
    }
}

AVAILABLE_STYLES_PSYCHOLOGY_OLD = {
    # ==============================
    # MACRO (Extreme Close-Ups & Portraits)
    # ==============================
    "macro_literal": {
        "use_case": "Use for extreme close-ups of specific physical actions or biological forms mentioned in the script (e.g., an eye twitching, a hand clenching).",
        "technical_prompt": (
            "Extreme macro photography, tight framing on a specific physical or biological subject from the script. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The subject must be highly recognizable but constructed entirely from non-organic materials. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual motif: pristine Polished Marble being slowly overtaken by fracturing Obsidian and filaments of Distressed Tobacco Leather stitching. "
            "Atmosphere: dense suspension of microscopic obsidian dust particles, heavy volumetric mist with floating light orbs catching the light, complex horizontal anamorphic flares. "
            ", hyper-realistic 3D render, low-key studio lighting with stark chiaroscuro, deep shadows, and glowing amber-orange rim accents against cold cyan fill (signaling simmering manipulation / deceptive warmth). "
            "Aggressive ultra-shallow depth of field: razor-sharp micro-focus on the central texture with surrounding edges melting into a heavy, creamy bokeh blur to isolate the subject. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, psychological thriller mood, 8k. 1:1 aspect ratio."
        )
    },
    "macro_metaphor": {
        "use_case": "Use for extreme close-ups of symbolic objects representing an idea (e.g., a fractured mirror for identity, a heavy chain for addiction).",
        "technical_prompt": (
            "Extreme macro photography, tight framing on a symbolic object representing the script's core theme. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The symbolic object is physically grounded but surreal, fracturing or trapped by sharp geometric forms. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual motif: Fractured Crystal Glassware trapped by sharp Obsidian geometric forms. "
            "Atmosphere: thousands of floating microscopic sparks, intense optical bloom radiating from crystal and obsidian surfaces, thick shadow haze. "
            ", hyper-realistic 3D render, flawless ultra-reflective surfaces, low-key studio lighting with stark chiaroscuro, engulfing pitch-black shadows and flickering emerald green rim accents (signaling anxiety/paranoia). "
            "Pinpoint selective focus on the core fracture or symbol, with foreground and background elements rendered as a distorting, out-of-focus optical blur. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, paranoia aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "macro_portrait": {
        "use_case": "Use to give a 'face' to the emotion without showing a real human. Best for representing the manipulator, the victim, or a shattered ego.",
        "technical_prompt": (
            "Extreme macro portrait photography of a faceless, humanoid feature—like a shattered skull of Matte Black Metal, a featureless Obsidian profile, or a Polished Marble hand. "
            "STRICTLY NO literal text, real human skin, or recognizable eyes. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual motif: A pristine Polished Marble surface fracturing to reveal Emerald Velvet underneath, held together by tiny, intricate Antique Gold mechanisms. "
            "Atmosphere: atmospheric scattering around the cold rim light, faint ethereal wisps of shadow, suspended dust motes, heavy volumetric fog. "
            ", hyper-realistic 3D render, low-key studio lighting with stark chiaroscuro, clinical cold white rim accents against pure pitch-black shadows (signaling isolation/depression). "
            "Extreme lens compression: sharp focal plane on the 'face's' leading edge, while the rest of the head dissolves into an atmospheric, ghostly background blur. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, psychological thriller mood, 8k. 1:1 aspect ratio."
        )
    },

    # ==============================
    # MEDIUM (Action & Power Dynamics)
    # ==============================
    "medium_dynamic": {
        "use_case": "Use for scenes showing interaction, power struggles, mirroring, or gaslighting between two entities.",
        "technical_prompt": (
            "Medium shot, dynamic composition showing two distinct abstract humanoid figures interacting in a power struggle, set within an boundless, impossible geometric environment constructed from interlinked Polished Marble floors and towering Obsidian structures that fill the entire background frame, creating a disorienting, endless maze feel. "
            "STRICTLY NO literal text, real humans, typography, or spelled-out words. "
            "The environment includes massive floating geometric cubes, fracturing arches, and shifting prisms. "
            "Figures must be constructed of contrasting materials: a towering Matte Black Metal figure casting an oppressive shadow over a fragile, cracking Polished Marble figure. "
            "Visual details: visible internal clockwork mechanisms of Antique Gold and Obsidian within the metal figure's chest, geometric furniture constructed from Antique Gold and Distressed Tobacco Leather. "
            "Atmosphere: rolling volumetric mist swirling around their bases and through the infinite geometric architecture, thousands of floating geometric particles catching the light, complex horizontal anamorphic flares. "
            ", hyper-realistic 3D render, striking contrast, low-key studio lighting with stark chiaroscuro, intense warm orange rim light against cold cyan fill accents (signaling simmering power struggle / false intimacy), heavy shadows, sharp geometric shadows cast by the lighting. "
            "Cinematic rack-focus effect: sharp subject isolation on the fragile marble figure, while the towering metal figure and the extensive, complex geometric background maze loom as an oppressive, heavily blurred mass in the foreground and far background. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, psychological tension aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "kinetic_tethers": {
        "use_case": "Use to visually represent the hidden mechanisms of control, such as trauma bonding, emotional attachments, or manipulation.",
        "technical_prompt": (
            "Medium-close shot focusing entirely on the physical connection between two unseen points. "
            "STRICTLY NO literal text. "
            "Visual focus on kinetic elements of control: heavy chains of Matte Black Metal and Obsidian, cords of Distressed Tobacco Leather with visible wear and Antique Gold buckles, or spilling shards of Crystal Glassware bridging a gap. "
            "Visual details: visible micro-etchings and symbols on gold and leather. "
            "Atmosphere: dense particle fields of glass shards, leather dust, and glowing blue optical lines, heavy volumetric fog revealing rim lights. "
            ", hyper-realistic 3D render, glowing internal light transmission, low-key studio lighting with stark chiaroscuro, flickering emerald green rim accents. "
            "Hypnotic depth of field: the center of the tether is hyper-focused and tactile, fading seamlessly into a soft, ethereal blur and massive overlapping bokeh circles. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, clinical psychological mood, 8k. 1:1 aspect ratio."
        )
    },

    # ==============================
    # WIDE & TEXTURE (Environments / Pure Mood)
    # ==============================
    "wide_metaphor": {
        "use_case": "Use for themes of feeling trapped, cornered, or navigating a complex psychological issue (e.g., a maze, a cage, a giant monolithic obstacle).",
        "technical_prompt": (
            "Wide-angle vast monolithic scale, focusing on a single, tiny focal subject providing emotional scale against a overwhelming, boundless, and inescapable geometric room/landscape that fills the entire frame. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The extensive, claustrophobic environment is a matrix of interlinked, shifting geometric forms: massive Polished Marble cubes, fractured Obsidian prisms, and complex Matte Black Metal girders wrapped in Emerald Velvet and accented with Distressed Tobacco Leather trim and Antique Gold details, extending into an oppressive, endless pattern. "
            "Atmosphere: dense atmospheric scattering obscuring the impossible heights of the architecture, cinematic haze, distant out-of-focus light blooms, thousands of microscopic crystal shards floating in the air. "
            ", hyper-realistic 3D render, claustrophobic but vast composition, flawless ultra-reflective surfaces, low-key studio lighting with stark chiaroscuro, pure clinical white accents against engulfing pitch-black shadows (signaling hopelessness), lights integrated into the geometric architecture casting sharp, conflicting shadows. "
            "Tilt-shift lens effect: a narrow band of sharp focus traps the tiny subject, while the towering, boundless geometric architecture above, below, and behind is blurred out, emphasizing a sense of miniature vulnerability within overwhelming complexity. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, isolation aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "texture_abstract": {
        "use_case": "Use as b-roll for pure tension, transitions, shifting brain chemistry, or to represent the abstract 'feeling' of an emotional breakdown.",
        "technical_prompt": (
            "Frame completely filled with chaotic abstract fluid dynamics, shifting particles, and fracturing geometry. "
            "STRICTLY NO literal text or recognizable macroscopic/human objects. "
            "A pure study of tension: melting surfaces of Emerald Velvet and viscous, swirling Obsidian, warping viscous liquids like Antique Mercury Glass, or sharp splinters of Crystal Glassware and Matte Black Metal. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual details: individual threads of velvet dissolving, micro-shards of crystal and metal fragments colliding. "
            ", hyper-realistic 3D render, fluid simulation, low-key studio lighting with stark chiaroscuro, intense molten orange rim accents pulsing through engulfing pitch-black shadows (signaling obsessive unraveling / creeping unease). "
            "Dynamic focal shifts: razor-sharp, hyper-focused Matte Black Metal splinters cutting through a background of heavy motion blur and swirling out-of-focus viscous fluids. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, gaslighting aesthetic, 8k. 1:1 aspect ratio."
        )
    }
}

AVAILABLE_STYLES_DARK_PSYCHOLOGY = {
    # ==============================
    # MACRO (Extreme Close-Ups & Portraits)
    # ==============================
    "macro_literal": {
        "use_case": "Use for extreme close-ups of specific physical actions or biological forms mentioned in the script.",
        "technical_prompt": (
            "Extreme macro photography, tight framing on a specific physical or biological subject from the script. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The subject must be highly recognizable but constructed entirely from non-organic materials. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual motif: pristine Polished Marble being slowly overtaken by fracturing Obsidian and filaments of Distressed Tobacco Leather stitching. "
            "Atmosphere: dense suspension of microscopic obsidian dust and suspended gold particles catching the rim light, heavy volumetric mist, and complex horizontal anamorphic light flares cutting through the frame. "
            ", hyper-realistic 3D render, low-key studio lighting with stark chiaroscuro, deep shadows, and glowing amber-orange rim accents against cold cyan fill (signaling simmering manipulation / deceptive warmth). "
            "Aggressive ultra-shallow depth of field: razor-sharp micro-focus on the central texture with surrounding edges melting into a heavy, creamy bokeh blur to isolate the subject. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, psychological thriller mood, 8k. 1:1 aspect ratio."
        )
    },
    "macro_metaphor": {
        "use_case": "Use for extreme close-ups of symbolic objects representing an idea.",
        "technical_prompt": (
            "Extreme macro photography, tight framing on a symbolic object representing the script's core theme. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The symbolic object is physically grounded but surreal, fracturing or trapped by sharp geometric forms. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual motif: Fractured Crystal Glassware trapped by sharp Obsidian geometric forms. "
            "Atmosphere: a dense suspension of suspended gold particles catching the rim light, intense optical bloom radiating from crystal and obsidian surfaces, thick shadow haze. "
            ", hyper-realistic 3D render, flawless ultra-reflective surfaces. Low-key studio lighting with stark chiaroscuro, engulfing pitch-black shadows. Intense subsurface scattering with smoldering internal embers, and molten gold seeping through hairline fractures (kintsugi style), contrasting with flickering emerald green rim accents (signaling anxiety/paranoia). "
            "Pinpoint selective focus on the core fracture or symbol, with foreground and background elements rendered as a distorting, out-of-focus optical blur. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, paranoia aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "macro_portrait": {
        "use_case": "Use to give a 'face' to the emotion without showing a real human.",
        "technical_prompt": (
            "Extreme macro portrait photography of a faceless, humanoid feature—like a shattered skull of Matte Black Metal, a featureless Obsidian profile, or a Polished Marble hand. "
            "STRICTLY NO literal text, real human skin, or recognizable eyes. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual motif: A pristine Polished Marble surface fracturing to reveal Emerald Velvet underneath, held together by tiny, intricate Antique Gold mechanisms. "
            "Atmosphere: atmospheric scattering around the cold rim light, faint ethereal wisps of shadow, suspended gold particles catching the rim light, heavy volumetric fog. "
            ", hyper-realistic 3D render, low-key studio lighting with stark chiaroscuro. Intense subsurface scattering with smoldering internal embers, and molten gold seeping through hairline fractures (kintsugi style) contrasting sharply against clinical cold white rim accents and pure pitch-black shadows (signaling isolation/depression). "
            "Extreme lens compression: sharp focal plane on the 'face's' leading edge, while the rest of the head dissolves into an atmospheric, ghostly background blur. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, psychological thriller mood, 8k. 1:1 aspect ratio."
        )
    },

    # ==============================
    # MEDIUM (Action & Power Dynamics)
    # ==============================
    "medium_dynamic": {
        "use_case": "Use for scenes showing interaction, power struggles, mirroring, or gaslighting between two entities.",
        "technical_prompt": (
            "Medium shot, dynamic composition showing two distinct abstract humanoid figures interacting in a power struggle, set within an boundless, impossible geometric environment constructed from interlinked Polished Marble floors and towering Obsidian structures that fill the entire background frame, creating a disorienting, endless maze feel. "
            "STRICTLY NO literal text, real humans, typography, or spelled-out words. "
            "The environment includes massive floating geometric cubes, fracturing arches, and shifting prisms. "
            "Figures must be constructed of contrasting materials: a towering Matte Black Metal figure casting an oppressive shadow over a fragile, cracking Polished Marble figure. "
            "Visual details: visible internal clockwork mechanisms of Antique Gold and Obsidian within the metal figure's chest, geometric furniture constructed from Antique Gold and Distressed Tobacco Leather. "
            "Atmosphere: rolling volumetric mist swirling around their bases and through the infinite geometric architecture, thousands of floating geometric particles catching the light, and complex anamorphic light flares cutting through the frame. "
            ", hyper-realistic 3D render, striking contrast, low-key studio lighting with stark chiaroscuro, intense warm orange rim light against cold cyan fill accents (signaling simmering power struggle / false intimacy), heavy shadows, sharp geometric shadows cast by the lighting. "
            "Cinematic rack-focus effect: sharp subject isolation on the fragile marble figure, while the towering metal figure and the extensive background maze loom as an oppressive, heavily blurred mass with a smeared lens effect, heavy chromatic aberration on the edges, and double-exposure phantom reflections to simulate gaslighting and distorted reality. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, psychological tension aesthetic, 8k. 1:1 aspect ratio."
        )
    },

    "kinetic_tethers": {
        "use_case": "Use to visually represent the hidden mechanisms of control, such as trauma bonding, emotional attachments, or manipulation.",
        "technical_prompt": (
            "Medium-close shot focusing entirely on the physical connection between two unseen points. "
            "STRICTLY NO literal text. "
            "Visual focus on kinetic elements of control: heavy chains of Matte Black Metal and Obsidian, cords of Distressed Tobacco Leather with visible wear and Antique Gold buckles, or spilling shards of Crystal Glassware bridging a gap. "
            "Visual details: visible micro-etchings and symbols on gold and leather. "
            "Atmosphere: dense particle fields of glass shards, suspended gold particles catching the rim light, and glowing blue optical lines, heavy volumetric fog revealing rim lights. "
            ", hyper-realistic 3D render, intense subsurface scattering on the materials, glowing internal light transmission, low-key studio lighting with stark chiaroscuro, flickering emerald green rim accents. "
            "Hypnotic depth of field: the center of the tether is hyper-focused and tactile, fading seamlessly into a soft, ethereal blur and massive overlapping bokeh circles, with just a touch of chromatic aberration on the edges to enhance the hypnotic tension. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, clinical psychological mood, 8k. 1:1 aspect ratio."
        )
    },

    # ==============================
    # WIDE & TEXTURE (Environments / Pure Mood)
    # ==============================
    "wide_metaphor": {
        "use_case": "Use for themes of feeling trapped, cornered, or navigating a complex psychological issue (e.g., a maze, a cage, a giant monolithic obstacle).",
        "technical_prompt": (
            "Wide-angle vast monolithic scale, focusing on a single, tiny focal subject providing emotional scale against a overwhelming, boundless, and inescapable geometric room/landscape that fills the entire frame. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The extensive, claustrophobic environment is a matrix of interlinked, shifting geometric forms: massive Polished Marble cubes, fractured Obsidian prisms, and complex Matte Black Metal girders wrapped in Emerald Velvet and accented with Distressed Tobacco Leather trim and Antique Gold details, extending into an oppressive, endless pattern. "
            "Atmosphere: dense atmospheric scattering obscuring the impossible heights of the architecture, cinematic haze, distant out-of-focus light blooms, anamorphic light flares cutting through the frame, and thousands of microscopic crystal shards floating in the air. "
            ", hyper-realistic 3D render, claustrophobic but vast composition, flawless ultra-reflective surfaces, low-key studio lighting with stark chiaroscuro, pure clinical white accents against engulfing pitch-black shadows (signaling hopelessness), lights integrated into the geometric architecture casting sharp, conflicting shadows. "
            "Tilt-shift lens effect: a narrow band of sharp focus traps the tiny subject, while the towering, boundless geometric architecture above, below, and behind is blurred out with a smeared lens effect, heavy chromatic aberration on the edges, and eerie double-exposure phantom reflections, emphasizing a sense of miniature vulnerability and disorientation. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, isolation aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    
    "texture_abstract": {
        "use_case": "Use as b-roll for pure tension, transitions, shifting brain chemistry, or to represent the abstract 'feeling' of an emotional breakdown.",
        "technical_prompt": (
            "Frame completely filled with chaotic abstract fluid dynamics, shifting particles, and fracturing geometry. "
            "STRICTLY NO literal text or recognizable macroscopic/human objects. "
            "A pure study of tension: melting surfaces of Emerald Velvet and viscous, swirling Obsidian, warping viscous liquids like Antique Mercury Glass, or sharp splinters of Crystal Glassware and Matte Black Metal. "
            "Materials strictly limited to: Polished Marble, Obsidian, Crystal Glassware, Antique Gold, Distressed Tobacco Leather, Matte Black Metal, or Emerald Velvet. "
            "Visual details: individual threads of velvet dissolving, micro-shards of crystal and metal fragments colliding. "
            ", hyper-realistic 3D render, fluid simulation, intense subsurface scattering, suspended gold particles catching the rim light. Low-key studio lighting with stark chiaroscuro, intense molten orange rim accents pulsing through engulfing pitch-black shadows (signaling obsessive unraveling / creeping unease). "
            "Dynamic focal shifts: razor-sharp, hyper-focused Matte Black Metal splinters cutting through a background of heavy motion blur, swirling out-of-focus viscous fluids, and a touch of chromatic aberration on the extreme edges. "
            "Framed by a crushed, pure black vignette. Octane render, raytracing, heavy caustics, gaslighting aesthetic, 8k. 1:1 aspect ratio."
        )
    }
}


AVAILABLE_STYLES_ANTIR = {
    # ==============================
    # MICRO (Cellular / Particle Level - based on the "HOW" image)
    # ==============================
    "micro_cellular": {
        "use_case": "Extreme close-ups of abstract biological entities passing through vessels or fibrous tunnels.",
        "technical_prompt": (
            "Abstract cinematic macro photography, extreme close-up. Shot on 100mm macro lens at f/1.2 for massive, creamy background bokeh. "
            "ENVIRONMENT: A dark, deep-sea-like microscopic void. Thick volumetric fog with floating, out-of-focus glowing golden dust particles. "
            "SUBJECT: A glowing, fibrous cellular core traveling through a tunnel of wet, highly refractive, glass-like stringy tendrils. "
            "LIGHTING: Low-key atmospheric lighting with intense internal bioluminescence. Heavy bloom effect on the glowing core, catching the edges of the transparent tendrils. "
            "COLORS: The central core pulses intensely with magma-orange and neon fleshy-pink. The surrounding glassy tendrils and background fog are a deep, dark cinematic cyan. "
            "DETAILS: Subtle futuristic sci-fi HUD elements and thin white analytical data lines floating softly in the background. Photorealistic 3D render, raytracing, high contrast, 8k. 1:1 aspect ratio"
        )
    },

    # ==============================
    # MACRO (See-Through Anatomy - based on the Skeleton/Heart/Brain images)
    # ==============================
    "macro_anatomy": {
        "use_case": "Close-ups of humanoid figures with transparent glossy shells revealing intricate, glowing internal organs and HUD text.",
        "technical_prompt": (
            "Cinematic dark sci-fi medical animation still. Camera tightly framed, extremely shallow depth of field (f/1.4), background melted into a heavy, dark blur with large circular bokeh. "
            "ENVIRONMENT: An empty, pitch-black void with a faint, smoky dark-blue atmosphere and floating golden light particles. "
            "SUBJECT: A humanoid anatomical figure (torso/skull). The outer skin and skeletal structure are made of glossy, highly refractive, transparent dark-cyan glass. Inside, a fractal-like network of capillaries, nerve endings, and solid organs (heart/brain) glow intensely. "
            "LIGHTING: Dramatic chiaroscuro with strong, sharp rim lighting catching the edges of the glass skeleton. The primary light source is the blinding, glowing organs radiating outward through the transparent shell, creating a heavy optical bloom. "
            "COLORS: The outer glass shell is tinted icy dark indigo and cyan. The internal anatomical networks are fiery gold, burning orange, and hot neon pink. "
            "DETAILS: Features futuristic sci-fi HUD elements, thin white annotation lines pointing to organs, and small, crisp white pseudo-medical text floating in the focal plane. Octane render, cinematic color grading, 8k. 1:1 aspect ratio"
        )
    },

    # ==============================
    # LABORATORY MACRO (Specific Organs with HUD - tailored to adrenal gland/heart)
    # ==============================
    "macro_adrenal_gland": {
        "use_case": "Dark, moody, cinematic macro shot of a specific organ with intense internal lighting and analytical HUD overlays.",
        "technical_prompt": (
            "Cinematic sci-fi macro shot of a single glowing adrenal gland. Tightly focused with extreme shallow depth of field (f/1.2), background blurred into a massive, creamy dark bokeh. "
            "ENVIRONMENT: A deep, nebulous dark-cyan void with floating, glowing golden dust motes and murky volumetric haze. "
            "SUBJECT: A highly detailed, anatomical adrenal gland made of a complex, fractal-like network of glowing fibers, encased in a subtle, highly refractive liquid-glass membrane. "
            "LIGHTING: Underexposed background. Pure, powerful internal bioluminescence from the central core provides the main light source, casting deep shadows in the crevices. Strong rim light defines the outer transparent membrane. "
            "COLORS: The organ pulses with blinding magma-orange, fiery gold, and neon pink, contrasting sharply against the deep, dark indigo and cinematic cyan background. "
            "DETAILS: Integrated futuristic medical HUD. Thin white laser lines pointing to specific nodes, accompanied by tiny, crisp white analytical text and faint holographic EKG data graphs floating out of focus in the background. Photorealistic 3D render, raytracing, heavy caustics, 8k. 1:1 aspect ratio"
        )
    },

    # ==============================
    # WIDE (Full Body Hologram & Data - based on the "STARTS" image)
    # ==============================
    "wide_full_body_data": {
        "use_case": "Full-body transparent humanoid figures surrounded by floating data overlays, EKG lines, and HUD elements in a dark void.",
        "technical_prompt": (
            "Abstract cinematic wide shot, sci-fi medical HUD aesthetic. "
            "ENVIRONMENT: An infinite, dark, atmospheric void. A faint, hazy, smoky ground reflection softly anchors the figure. Thick volumetric fog. STRICTLY NO physical room, NO laboratory, NO walls, NO equipment. "
            "SUBJECT: A full-body humanoid figure walking forward. The body is made of an intricate, transparent, refractive cool-cyan glassy shell. Inside, a dense network of anatomy glows fiercely with fiery orange, gold, and pink internal energy. "
            "LIGHTING: Intense internal bioluminescence from the glowing core. Sharp, icy cyan rim lighting outlines the figure's transparent shell against the dark background. "
            "COLORS: Deep navy and dark teal atmosphere, contrasting sharply with the burning warm gold, neon pink, and bright magenta of the figure's core. "
            "DETAILS: Layered transparent graphic overlays. Massive, out-of-focus glowing EKG heartbeat lines span the background in neon cyan and pink. Floating crisp white futuristic HUD elements, thin tech lines, and pseudo-medical annotation text surround the figure in 3D space. Unreal Engine 5 render, cinematic lighting, 8k. 1:1 aspect ratio"
        )
    },
    "bioluminescent_macro_environment": {
        "use_case": "A grand, atmospheric macro view of a complete complex environment (like a globe, an organ forest, or a deep-sea biome) constructed entirely from glowing biological systems and anatomical structures.",
        "technical_prompt": (
            "Cinematic wide-angle macro view. Grand, fantastical perspective of an entire bioluminescent biomorphic landscape or structure, like a biological globe. Shot with a specialized wide-field macro lens with massive depth-of-field-induced bokeh in the foreground and background. "
            "ENVIRONMENT: A vast, complex structure (e.g., a curved globe or an intricate organ forest) made of interlocking transparent cyan-tinted glass cells and skeletal structures. The air is thick with a dark-cyan volumetric fog and countless floating, out-of-focus golden light orbs creating massive, creamy bokeh. No natural physics. "
            "SUBJECT: The entire environment structure is the subject. Complex internal anatomical systems are visible and glowing. For a globe, continents are made of dense networks of fiery orange, gold, and pink vascular systems and neural paths. The oceans are deep, dark indigo and cyan glass. For a forest, 'trees' are intricate, complex organ structures. "
            "LIGHTING: Low-key atmospheric lighting with powerful internal bioluminescence from the anatomical systems, creating a distinct optical bloom on the warm energy centers. Dramatic chiaroscuro with sharp rim lighting defining the edges of the transparent glassy materials. "
            "COLORS: A striking contrast of deep, dark indigo, navy, and cyan blues and teals, offset by intense neon pinks, magentas, fiery golds, and magma-oranges. "
            "DETAILS: Multi-layered data visualizations and holographic HUD overlays. Stylized, out-of-focus EKG heartbeat lines span the deep background. Integrated into the scene are thin-line technical annotations, floating charts, and crisp white sci-fi text (e.g., 'CORE BIOME STATUS', 'NEURAL PATHWAY MAP', 'SYSTEM SYNC'). A prominent stylized organic green-yellow textured text overlay is superimposed (e.g., 'SYSTEMS UNIFIED'). Photorealistic 3D render, raytracing, high contrast, heavy caustics, cinematic color grading, 8k. 1:1 aspect ratio."
        )
    }
}


AVAILABLE_STYLES = {
    # ==============================
    # MACRO (Close-ups, Details, Single Reactions)
    # ==============================
    "alchemy_macro_roots": {
        "use_case": "Use for extreme close-ups of a single alchemical reaction, growing neural roots, or a magical transformation taking place at the micro-level.",
        "technical_prompt": (
            "Extreme macro photography, tight framing. Neural Dreamcore Alchemy style. "
            "A single, hyper-detailed neural root made of obsidian-black ink splitting and weeping luminous liquid gold. "
            "Surreal alchemical transformations occurring at the microscopic level, set in an abyssal, pitch-black void. "
            "Atmosphere: suspended shimmering gold particles, wisps of dissolving ink smoke, and heavy volumetric mist catching the light. "
            "Aggressive ultra-shallow depth of field (f/1.2), macro lens compression focusing sharply on the exact point where gold meets ink, "
            "with the surrounding environment melting into a creamy, swirling dark bokeh background. "
            "Cinematic lighting, glowing internal luminescence from the gold contrasting with harsh, cold rim light on the ink. "
            "Hyper-detailed, 8k, Octane render, raytracing, heavy caustics. 1:1 aspect ratio."
        )
    },

    # ==============================
    # MEDIUM (Entities, Artifacts, Focal Points)
    # ==============================
    "alchemy_entity_medium": {
        "use_case": "Use for medium shots of an abstract entity, a character silhouette, or a central artifact formed by the alchemical process.",
        "technical_prompt": (
            "Medium shot, dynamic composition. Neural Dreamcore Alchemy style. "
            "An abstract, surreal humanoid silhouette or mysterious alchemical artifact forming entirely out of twisting, dense ink neural roots and pulsating veins of flowing liquid gold. "
            "Suspended in an infinite, pitch-black void. Surreal alchemical transformations: the entity appears to be constantly dissolving into ink and reforming from gold. "
            "Atmosphere: heavy particle simulation of dripping gold droplets and evaporating ink ash, sharp volumetric light beams cutting through the dark void. "
            "Cinematic rack-focus effect: the central entity is razor-sharp and hyper-tactile, while the background falls into a deep, dark atmospheric blur "
            "with subtle chromatic aberration on the extreme edges of the frame to give a dreamlike, unstable feel. "
            "Dramatic chiaroscuro lighting, striking contrast between the blinding, warm glowing gold and the matte, light-absorbing black ink. "
            "Hyper-detailed, 8k, Unreal Engine 5 render, raytracing. 1:1 aspect ratio."
        )
    },

    # ==============================
    # WIDE (Mindscapes, Vast Environments)
    # ==============================
    "alchemy_void_wide": {
        "use_case": "Use for establishing shots of a mindscape, vast endless voids, or massive, sprawling alchemical networks.",
        "technical_prompt": (
            "Wide-angle, vast monolithic scale. Neural Dreamcore Alchemy style. "
            "A massive, boundless network of colossal ink neural roots sprawling across an endless, dark void, glowing with pulsating rivers of liquid gold functioning like a cosmic nervous system. "
            "Surreal alchemical transformations: distant geometric monoliths in the void slowly dissolving into golden liquid. "
            "Atmosphere: dense, rolling cosmic fog, thousands of floating golden embers, and complex anamorphic light flares cutting through the cinematic lighting. "
            "Tilt-shift lens effect: a narrow band of sharp focus on a central nexus of roots, while the immense scale of the foreground and deep background "
            "dissolves into a heavy, smeared lens blur and double-exposure phantom reflections, emphasizing the terrifying, infinite scale of the void. "
            "Deep, immersive shadows, hyper-detailed, 8k, Octane render, breathtaking sense of scale and cosmic mystery. 1:1 aspect ratio."
        )
    },

    # ==============================
    # TEXTURE (B-roll, Transitions, Pure Emotion)
    # ==============================
    "alchemy_fluid_abstract": {
        "use_case": "Use as b-roll, scene transitions, mind-bending visual metaphors, or to represent the shifting state of a mind or magic system.",
        "technical_prompt": (
            "Frame completely filled with chaotic, abstract fluid dynamics. Neural Dreamcore Alchemy style. "
            "STRICTLY NO recognizable objects. Pure surreal alchemical transformations: heavy, viscous liquid gold violently colliding, mixing, and marbled with deep, abyssal black ink. "
            "Fragile neural roots flash-freezing and shattering in the void. "
            "Atmosphere: macro particle suspension, intense optical bloom radiating from the liquid gold, heavy shadow haze. "
            "Dynamic focal shifts: razor-sharp, hyper-focused points on the collision of the fluids, fading seamlessly into a soft, hypnotic, swirling motion blur. "
            "Low-key studio lighting with stark chiaroscuro, pure black engulfing shadows pushing the golden highlights to maximum intensity. "
            "Hyper-detailed, 8k, fluid simulation render, heavy liquid caustics, mesmerizing, psychedelic mood. 1:1 aspect ratio."
        )
    }
}


def estimate_duration(text: str) -> float:
    words_per_minute: float = 200.0
    chars_per_minute: float = 200.0 * 5
    words = len(text.split())
    chars = len(text.replace(" ", ""))
    seconds = round((words / words_per_minute * 60) + (chars / chars_per_minute * 60) / 2, 1)
    return seconds

def split_script(script: str) -> list:
    pattern = r'(<br>)'
    parts = re.split(pattern, script)
    sentences = []

    current_time = 0
    for part in parts:
        part = part.strip()
        if part and part != '<br>':
            duration = estimate_duration(part)
            sentences.append({
                "start_time": current_time,
                "text": part,
                "duration": duration,
            })
            current_time += duration
        elif part == '<br>':
            current_time += 2.0
            print("Split script into sentences with timing:")
    for sentence in sentences:
        print(f"Start: {sentence['start_time']}s, Duration: {sentence['duration']}s, Text: {sentence['text']}")
    return sentences


class SceneIdea(BaseModel):
    style: str = Field(
        description="Name of the best suiting style for this generation.",
        json_schema_extra={"enum": list(AVAILABLE_STYLES.keys())}
    )
    idea: str = Field(description="Brief description of the visual scene, concise—focus on the core visual subject and environment")
    reasoning: str = Field(description="Why visual fits the context")

class SceneIdeasResponse(BaseModel):
    scenes: List[SceneIdea]

class ScenePromptsResponse(BaseModel):
    image_prompt: str = Field(description="Highly descriptive image prompt including subject, environment, lighting, and style integration.")
    video_prompt: str = Field(description="Motion-focused video prompt. Format: [Camera Movement], [Subject Movement], [Speed/Vibe]")

class HarmonizedScene(BaseModel):
    scene_id: int = Field(description="The exact ID of the scene.")
    video_prompt: str = Field(description="The harmonized video prompt.")

class HarmonizedSequenceResponse(BaseModel):
    harmonized_scenes: List[HarmonizedScene]


# ==========================================
# ASYNC WORKER FUNCTIONS
# ==========================================
async def _expand_single_prompt(llm_client: 'LLM', local_idx: int, idea_obj: SceneIdea) -> Dict[str, Any]:
    """Agent 2: Expands a single idea into full prompts."""
    chosen_style = idea_obj.style 
    technical_instructions = AVAILABLE_STYLES.get(chosen_style, {}).get('technical_prompt', '')

    agent_2_messages = [
        {
            "role": "system",
            "content": "You are an expert AI Prompt Engineer specializing in Text-to-Image (Nano Banana Pro) and Image-to-Video models (e.g. Veo Pro, Sora Pro, Kling AI, Seedance)."
        },
        {
            "role": "user",
            "content": (
                "I have a raw scene idea:\n"
                f"idea: {idea_obj.idea}\n"
                f"reasoning: {idea_obj.reasoning}\n"
                f"style: {technical_instructions}\n\n"
                "Your task is to take a rough scene idea and its assigned visual styles, and expand it into two specific prompts.\n"
                "1. 'image_prompt': Must be highly descriptive. Include the subject, environment, lighting, atmosphere, and explicitly integrate the provided styles. You should extend the description to enrich the visual representation.\n"
                "2. 'video_prompt': Suitable for the AI image-to-video generator (Format: [Camera Movement], [Subject Movement], [Speed/Vibe]). Keep the video prompt focused on motion. Do not include information about style or lighting since the AI already has an image reference. Keep subject movement micro-focused.\n\n"
                "CRITICAL INSTRUCTION FOR [Camera Movement]:\n"
                "Select EXACTLY ONE camera movement from the list below that best enhances the specific emotion and action of the scene. Match the movement to the scene's intent:\n"
                "- Crane/pedestal: For grand reveals, showing immense scale, or vertical perspective shifts.\n"
                "- Handheld: For tension, gritty intimacy, chaotic action, or documentary realism.\n"
                "- Track/dolly: For pushing in (intensity/realization) or pulling out (isolation/loneliness).\n"
                "- Lateral track: For smoothly following a subject moving sideways across the frame.\n"
                "- Stabilized: For smooth following of dynamic, fast-paced action or a floating sensation.\n"
                "- Static: For intense micro-focus on subtle emotional shifts or pure subject movement.\n"
                "- Nodal Pan: For scanning a wide environment or horizon from a fixed central viewpoint.\n"
                "- Tilt: For revealing extreme height or looking up/down at a subject.\n"
                "- Pan and Tilt: For following complex, unpredictable, or diagonal movement.\n"
                "- Pan: For simply following horizontal action or connecting two subjects in a space."
            )
        }
    ]

    prompts_response = await llm_client.generate(
        messages=agent_2_messages,
        response_format=ScenePromptsResponse,
        temperature=0.5 
    )
    
    return {
        "local_id": local_idx,
        "style": idea_obj.style,
        "idea": idea_obj.idea,
        "reasoning": idea_obj.reasoning,
        "image_prompt": prompts_response.image_prompt,
        "video_prompt": prompts_response.video_prompt
    }


async def _process_script_part(
    i: int, 
    script_part: Dict[str, Any], 
    llm_client: 'LLM', 
    script: str, 
    total_parts: int, 
    semaphore: asyncio.Semaphore,
    progress_callback: Optional[Callable]
) -> Dict[str, Any]:
    """Handles Agent 1, Agent 2, and Agent 3 for a single script part."""
    
    # The semaphore ensures we don't bombard the LLM API and get rate-limited
    async with semaphore:
        num_scenes = math.ceil(script_part['duration'] / 1.5)
        
        if progress_callback:
            await progress_callback(status="in_progress", message=f"🎬 Part {i+1}/{total_parts}: Agent 1 brainstorming...")

        # --- AGENT 1: IDEA GENERATION ---
        agent_1_styles_formatted = "\n".join([f"- {name}: {data['use_case']}" for name, data in AVAILABLE_STYLES.items()])
        
        agent_1_messages = [
            {
                "role": "system",
                "content": (
                    "You are a highly creative Visual Director for a video production pipeline. "
                    "Your job is to brainstorm short, high-impact scene ideas for specific parts of a script. "
                    "CRITICAL INSTRUCTION: You must build your visual concepts AROUND the provided available styles. "
                    "Do not brainstorm an idea and then assign a style. Instead, you must first select an available style, "
                    "read its 'use_case', and let those specific constraints dictate what happens in the scene. "
                    "You do not need to worry about character or location consistency. We are generating many short, "
                    "rapid-fire scenes to cherry-pick the best ones later - so try to use a variety of ideas. "
                    f"Here is the full script just for context:\n\n{script}"
                )
            },
            {
                "role": "user",
                "content": (
                    f"Generate EXACTLY {num_scenes} raw visual concepts for this sentence: \"{script_part['text']}\".\n\n"
                    "Available styles and their use cases:\n"
                    f"{agent_1_styles_formatted}\n\n"
                    "To ensure the style drives the visual, you MUST generate your output in this STRICT ORDER:\n"
                    "- \"style\": FIRST, pick the name of the most appropriate style from the available list.\n"
                    "- \"reasoning\": SECOND, explain why this style's specific 'use_case' fits the emotional or narrative context of the sentence.\n"
                    "- \"idea\": FINALLY, describe the visual scene. This description MUST strictly adhere to the style and use case you just selected. "
                    "Keep it concise—focus on the core visual subject and environment.\n\n"
                    "Diversity Rule: Do not use the same style more than 3 times in a row."
                )
            }
        ]

        ideas_response = await llm_client.generate(messages=agent_1_messages, response_format=SceneIdeasResponse, temperature=0.8)

        # --- AGENT 2: PROMPT EXPANSION (Concurrent) ---
        if progress_callback:
            await progress_callback(status="in_progress", message=f"🎨 Part {i+1}/{total_parts}: Agent 2 expanding prompts...")

        # Run all Agent 2 expansions for this specific part simultaneously
        agent_2_tasks = [
            _expand_single_prompt(llm_client, local_idx, idea_obj)
            for local_idx, idea_obj in enumerate(ideas_response.scenes)
        ]
        local_scenes_for_part = await asyncio.gather(*agent_2_tasks)

        # --- AGENT 3: CAMERA MOVEMENT HARMONIZATION ---
        if progress_callback:
            await progress_callback(status="in_progress", message=f"🎥 Part {i+1}/{total_parts}: Agent 3 harmonizing flow...")

        # minimal_scenes_for_agent_3 = [
        #     {"id": scene["local_id"], "idea": scene["idea"], "video_prompt": scene["video_prompt"]}
        #     for scene in local_scenes_for_part
        # ]

        # agent_3_messages = [
        #     {
        #         "role": "system",
        #         "content": (
        #             "You are a Master Video Editor and Cinematographer. Your goal is to review a short sequence of AI video generation prompts and harmonize their camera movements to create a smooth, hypnotic flow.\n"
        #             "### STRICT CAMERA VOCABULARY\n"
        #             "You MUST select the camera movement from this exact list:\n"
        #             "- Static: No camera movement, focus purely on subject motion.\n"
        #             "- Pan: Horizontal rotation.\n"
        #             "- Nodal Pan: Panning without changing the camera's physical position (great for wide landscapes).\n"
        #             "- Tilt: Vertical rotation.\n"
        #             "- Pan and Tilt: Combined diagonal/sweeping rotation.\n"
        #             "- Track/dolly: Moving forward or backward through space.\n"
        #             "- Lateral track: Moving perfectly sideways (great for hypnotic side-scrolling).\n"
        #             "- Crane / pedestal: Moving strictly up or down in space.\n"
        #             "- Handheld: Adds subtle, gritty, realistic shake.\n"
        #             "- Stabilized: Ultra-smooth, gimbal-like motion.\n\n"
        #             "### RULES FOR SMOOTHING\n"
        #             "1. MATCHING MOMENTUM: If consecutive scenes share a similar vibe, match or naturally sequence their camera movements. (e.g., A 'Lateral track' right flows perfectly into a 'Pan' right).\n"
        #             "2. LOGICAL LIMITS: Do not force a camera movement if it feels physically impossible for the described image. If matching the previous scene's movement breaks the current scene, use 'Static' or 'Stabilized' as a neutral reset.\n"
        #             "3. ISOLATION: Separate the camera movement from the subject action."
        #         )
        #     },
        #     {
        #         "role": "user",
        #         "content": (
        #             "Here is the short sequence of scenes in chronological order:\n"
        #             f"{json.dumps(minimal_scenes_for_agent_3, indent=2)}\n\n"
        #             "Analyze the camera movements, harmonize them using ONLY the approved vocabulary, and output the updated sequence."
        #         )
        #     }
        # ]

        # harmonization_response = await llm_client.generate(
        #     messages=agent_3_messages,
        #     response_format=HarmonizedSequenceResponse,
        #     temperature=0.2
        # )

        # # Update local scenes
        # harmonized_dict = {scene.scene_id: scene.video_prompt for scene in harmonization_response.harmonized_scenes}

        # for scene in local_scenes_for_part:
        #     scene_id = scene["local_id"]
        #     if scene_id in harmonized_dict:
        #         scene["video_prompt"] = harmonized_dict[scene_id]
        #     del scene["local_id"] # Cleanup

        return {
            "text": script_part["text"],
            "duration": script_part["duration"],
            "start_time": script_part["start_time"],
            "scenes": local_scenes_for_part
        }


# ==========================================
# MAIN GENERATION FUNCTION
# ==========================================
async def generate_scenes(
    llm_client: 'LLM', 
    script: str,
    splitted_script: List[Dict[str, Any]],
    progress_callback: Optional[Callable] = None,
    max_concurrent_parts: int = 5 # Adjust this based on your API tier limits
) -> List[Dict[str, Any]]:
    
    total_parts = len(splitted_script)
    
    # Semaphore restricts how many script parts process simultaneously
    semaphore = asyncio.Semaphore(max_concurrent_parts)
    
    # Create a task for every script part
    tasks = [
        _process_script_part(i, part, llm_client, script, total_parts, semaphore, progress_callback)
        for i, part in enumerate(splitted_script)
    ]
    
    # Execute all parts concurrently and wait for all to finish
    script_parts_with_scenes = await asyncio.gather(*tasks)

    if progress_callback:
        await progress_callback(status="complete", message="✅ Pipeline finished asynchronously!")

    # asyncio.gather returns results in the exact same order the tasks were passed in
    return list(script_parts_with_scenes)