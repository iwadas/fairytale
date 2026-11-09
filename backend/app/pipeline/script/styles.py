"""Visual style catalogue used by the scene generator.

Each style has a ``use_case`` (shown to the idea-generation agent so it can pick
a style) and a ``technical_prompt`` (injected into the prompt-expansion agent).
"""
from typing import TypedDict


class StyleDefinition(TypedDict):
    use_case: str
    technical_prompt: str


AVAILABLE_STYLES: dict[str, StyleDefinition] = {

    # ==============================
    # WIDE (Cosmic Scale, Space, The Void)
    # ==============================
    "cosmos_vast_wide": {
        "use_case": "Use this to establish overwhelming cosmic or geological scale. Ideal for opening shots of the universe, deep time, planetary vistas, or the insignificance of civilization against geological age.",
        "technical_prompt": (
            "Ultra-wide cinematic documentary establishing shot. Cosmic Existentialism style. "
            "[LLM SELECTS ONE CAMERA POSITION: True top-down orbital perspective looking down at a planet's curvature, stars bleeding into the frame | Sweeping low-altitude drone arc across an ancient ruined landscape with a massive nebula dominating the entire sky | Extreme wide ground-level shot across a barren desert plain, camera nearly touching the earth, the Milky Way a thick band filling the upper two-thirds of frame]. "
            "[LLM INSERTS ANCIENT OR COSMIC SUBJECT HERE, e.g., The eroded ruins of an unknown stone civilization on a windswept plateau / A single crumbling monolith standing in a vast salt flat under a star-dense sky] "
            "dwarfed by an overwhelming cosmic backdrop — a turbulent nebula in deep amber and charcoal, or a gas giant's arc on the horizon, or the dense star field of the galactic core. "
            "Color palette: deep indigo and midnight blue for the sky, warm ochre and raw umber for earth and stone, pale gold for starlight, ash white for distant dust clouds. No artificial color grading, no oversaturation. "
            "Atmosphere: volumetric dust haze at the horizon, subtle lens flare from a distant star or moon, a single light source (star, moon, or bioluminescent phenomenon) casting long directional shadows. "
            "Film grain: heavy 35mm cinematic grain baked in throughout. Motion: the camera moves with glacial slowness, as if time itself is heavy. "
            "Tilt-shift zone of focus: the horizon line is sharp, foreground stone and distant nebula both gently fall off into depth haze. "
            "Mood: profound silence, geological patience, the weight of deep time. "
            "Hyper-realistic render, 8k, photochemical grain, IMAX documentary cinematography. 16:9 aspect ratio."
        )
    },

    # ==============================
    # MACRO (Detail, Discovery, The Unseen)
    # ==============================
    "cosmos_macro_discovery": {
        "use_case": "Use this when the narrative zooms into a small physical detail that carries enormous meaning — an inscription, a carved symbol, a crystal formation, a fossilized pattern, a cellular or atomic structure mirroring the cosmic.",
        "technical_prompt": (
            "Extreme macro documentary close-up, forensic and reverent. Cosmic Existentialism style. "
            "[LLM SELECTS ONE CAMERA ANGLE: Dead-flat top-down zenith shot looking straight into the surface, as if studying evidence | Oblique 45-degree angle with shallow DOF catching surface texture in raking light | True side-profile macro capturing the cross-section of layers — stone, ice, bone, or mineral]. "
            "STRICT COLOR PALETTE: The palette is dictated entirely by natural material — warm sandstone ochres, cold granite grays, bone ivory, mineral green-gold, rust iron oxide. No artificial light colors. "
            "[LLM INSERTS PHYSICAL DETAIL HERE (MUST BE A REAL OR PLAUSIBLY REAL MATERIAL OBJECT), e.g., A deeply carved ancient glyph filled with centuries of mineral sediment / A cross-section of meteorite revealing crystalline Widmanstätten patterns / A fossilized spiral shell embedded in limestone] "
            "occupying the full frame, every microscopic texture rendered with forensic clarity. "
            "Lighting: single-source raking light at an extreme low angle, dragging across the surface and casting long micro-shadows that reveal topology invisible to the naked eye. "
            "Depth of field: ultra-shallow (f/1.4 macro equivalent), the precise point of meaning is in sharp focus, the surrounding material dissolves into a warm material bokeh. "
            "The background is the natural material itself blurred beyond recognition — no void, no black, just the texture of the object swallowed by its own depth. "
            "[LLM OPTIONALLY INSERTS ONE SUBTLE VISUAL ACCENT: e.g., A single mote of dust frozen in the raking light / A hairline crack filled with quartz crystal catching the light like a vein of frozen lightning. Keep it minimal.] "
            "Film grain: heavy analogue grain. Mood: the feeling of a scientist making a discovery that rewrites everything. "
            "8k, forensic macro photography, photorealistic natural materials, breathless intimacy. 1:1 aspect ratio."
        )
    },

    # ==============================
    # PSYCHOLOGICAL: LIMINAL (Ancient & Abandoned)
    # ==============================
    "cosmos_liminal_ancient": {
        "use_case": "Use this to evoke lost time, abandoned civilizations, and the uncanny stillness of places that were once full of life. Empty ancient architecture, underground chambers, submerged ruins. No people — only the echo of them.",
        "technical_prompt": (
            "Uncanny liminal ancient architecture, deserted and timeless. Cosmic Existentialism style. "
            "[LLM SELECTS ONE CAMERA ANGLE: Low corridor-level perspective looking into an infinite receding hallway of stone columns | High CCTV-like angle looking down into a circular chamber floor carved with symbols | Dutch angle peering through a collapsed stone doorway into deeper darkness beyond]. "
            "NO PEOPLE. NO SYNTHETIC HUMANOIDS. Only space, stone, and the residue of whoever was here. "
            "[LLM INSERTS ANCIENT SPACE HERE, e.g., A vast underground Egyptian-scale hall, columns stretching beyond sight, torchlight long dead / A circular submerged stone chamber, still water reaching ankle height, carvings covering every surface / A collapsed corridor of an unidentified pre-historical site, roots penetrating the ceiling]. "
            "Color palette: torch-amber and deep shadow. Warm incandescent light from a single unseen source — perhaps a crack in the ceiling through which filtered sunlight falls in a single shaft. Everything else is cool stone gray and dense brown shadow. "
            "Surface material priority: render stone, moss, mineral deposits, water stains, and carved surfaces with photorealistic geological fidelity — every crack, every tool mark, every weathering pattern counts. "
            "Atmosphere: absolute silence translated visually — still air, no dust movement, the faint suggestion of shallow still water on the floor reflecting the ceiling. "
            "Depth: strong depth cues from receding architecture, but the far end is always swallowed by darkness — never fully revealed. "
            "Film grain: heavy. A sense that this footage was captured at great personal risk. "
            "8k, archaeological documentary realism, Unreal Engine 5 photorealism, suffocating sense of deep history. 1:1 aspect ratio."
        )
    },

    # ==============================
    # SCALE: CIVILIZATION VS COSMOS
    # ==============================
    "cosmos_civilization_scale": {
        "use_case": "Use this to show the relationship between human civilization — ancient or modern — and the overwhelming scale of the cosmos. Pyramids under a nebula. A city under a dying star. Architecture that reaches for heaven and fails.",
        "technical_prompt": (
            "Cinematic scale contrast shot, civilization against cosmos. Cosmic Existentialism style. "
            "[LLM SELECTS ONE CAMERA ANGLE: Low-angle looking up along the face of a massive ancient structure, stars beginning behind its apex | Wide symmetrical shot framing a monumental structure dead-center against a sky that dwarfs it | Slow-rising crane shot that begins at human scale and ends with the structure reduced to a speck in a planetary vista]. "
            "[LLM INSERTS CIVILIZATION ELEMENT HERE, e.g., The Great Pyramid of Giza / A ziggurat of unknown origin on a plain / A colossal stone head half-buried in jungle / A Roman aqueduct crossing a valley under a full moon] "
            "rendered with absolute architectural and geological accuracy. "
            "The sky is the emotional core: a Milky Way at maximum density, or a partial lunar eclipse casting cold blue shadow, or a total solar corona, or a comet's tail splitting the sky. "
            "Color palette: the warm ochre and amber of ancient stone against the cold blue-white and indigo of the night sky. This temperature contrast is the visual tension. "
            "Lighting: a single strong natural light source (moon, star, or dawn horizon glow) creating long architectural shadows that emphasize geometry. "
            "Human presence: optionally one tiny silhouetted human figure at the base of the structure — not larger than 1/20th of the frame height — purely to establish scale. No faces, no detail. Just scale. "
            "Film grain: heavy. Long-exposure star trails optionally visible as faint light arcs. "
            "Hyper-realistic, 8k, photographic night sky accuracy, National Geographic documentary framing. 16:9 aspect ratio."
        )
    },

    # ==============================
    # THEME: CONSCIOUSNESS INTERIOR (Abstract Mind)
    # ==============================
    "cosmos_consciousness_interior": {
        "use_case": "Use this to visualize abstract concepts — time, consciousness, memory, the nature of existence, the self. The 'inside' of a mind or the universe rendered as a physical space you can inhabit.",
        "technical_prompt": (
            "Surreal interior space, consciousness as architecture. Cosmic Existentialism style. "
            "[LLM SELECTS ONE CAMERA ANGLE: First-person perspective drifting through the space as if weightless, the camera tilting slowly to suggest floating | Looking upward from the floor of an impossible space, the ceiling infinite and star-dense | Slow pull-back revealing the space is far larger than it first appeared — a reverse tilt-shift expanding to a cosmic scale]. "
            "[LLM INSERTS THE ABSTRACT CONCEPT TRANSLATED INTO PHYSICAL SPACE, e.g., Memory rendered as a library of crumbling stone shelves receding to infinity, each shelf holding a glowing amber orb / Time rendered as a corridor where the walls are transparent and show different eras simultaneously / Consciousness rendered as a dark ocean with a single island of light in the infinite distance]. "
            "Color palette: deep indigo and black for the void, warm amber and gold for moments of meaning, cold silver-white for intellectual clarity. All transitions between color zones are gradual — no hard cuts in the color space. "
            "Physical logic: the space follows its own internal gravitational and architectural logic — whatever that logic is, it must be consistent throughout the frame. "
            "Lighting: one warm concentrated light source illuminating the meaningful element, surrounded by the cold ambient glow of a distant star field or phosphorescent phenomenon. "
            "Atmosphere: subtle volumetric haze at mid-depth suggesting the space has weight and presence. Motes of light — like dust particles or neurons firing — drifting slowly through the scene. "
            "Film grain: moderate, suggesting 16mm documentary footage shot in an impossible location. "
            "Mood: profound wonder with a thread of existential unease — beautiful but slightly too large to fully comprehend. "
            "8k, Octane render, photorealistic atmosphere, Christopher Nolan documentary aesthetic. 1:1 aspect ratio."
        )
    },

    # ==============================
    # THRESHOLD (The Moment Before Discovery)
    # ==============================
    "cosmos_threshold_discovery": {
        "use_case": "Use this for the moment of standing at the edge of the unknown — the entrance to an unexplored ruin, the event horizon of a black hole, the surface of an uncharted planet. The moment before everything changes.",
        "technical_prompt": (
            "Cinematic threshold composition, the edge of the unknown. Cosmic Existentialism style. "
            "[LLM SELECTS ONE CAMERA ANGLE: Over-the-shoulder rear shot of a lone figure approaching a massive portal or rupture, the camera close and low behind them | Symmetrical frontal shot framing a doorway or event horizon dead-center, the subject a silhouette barely visible within | Extreme wide shot showing a tiny figure at the base of something incomprehensibly large, approaching it alone]. "
            "[LLM INSERTS THRESHOLD HERE, e.g., The entrance to a deep cave system lit from within by unknown bioluminescence / The edge of a cliff above ruins buried under centuries of jungle / The surface boundary of a black hole's accretion disk, light bending visibly at the margin / A sealed stone doorway covered in carvings that have not been opened in ten thousand years]. "
            "STRICT COLOR PALETTE: The near side — where the viewer stands — is cold and dark: deep stone gray, charcoal, midnight blue. The far side of the threshold emits warm amber or luminous gold, creating a strong temperature gradient that makes crossing irresistible. "
            "The threshold itself is the sharpest element in the frame. Everything before and behind falls into progressive depth haze. "
            "Human figure (optional): if present, strictly a silhouette, never more than 1/6th of the frame, never facing the camera. Present purely to give scale and psychological identification. "
            "Atmosphere: sparse floating particulate matter — dust, spores, or ionized gas — catching the light from the far side. "
            "Film grain: heavy. The feeling of found footage or expedition documentation. "
            "Mood: the physical manifestation of a question that cannot be un-asked. "
            "8k, Unreal Engine 5, photorealistic geological and cosmic materials, cinematic tension. 1:1 aspect ratio."
        )
    },

    # ==============================
    # PATTERN: THE HIDDEN ORDER (Fractals, Repetition, Sacred Geometry)
    # ==============================
    "cosmos_hidden_pattern": {
        "use_case": "Use this when the theme is the unseen patterns beneath reality — sacred geometry, fractal structures in nature, the repetition of cosmic and microscopic forms, the mathematical underpinning of existence.",
        "technical_prompt": (
            "Revelation of pattern, microscopic and cosmic simultaneously. Cosmic Existentialism style. "
            "[LLM SELECTS ONE DYNAMIC CAMERA ANGLE: True zenith top-down showing a pattern that reveals itself at scale — the camera pulling back to reveal the repetition | Slow push-in toward a detail that begins to show its geometric structure | Split-composition showing two scales simultaneously — a galaxy spiral and a nautilus shell side by side, lit identically]. "
            "STRICT COLOR PALETTE: Natural material colors only. Stone ochre, bone ivory, mineral rust, deep forest green, water blue-gray. The pattern itself is revealed through shadow and raking light — not artificial color. "
            "[LLM INSERTS THE PATTERN OR STRUCTURE HERE — MUST BE GROUNDED IN REAL NATURAL OR HISTORICAL PHENOMENON, e.g., The Fibonacci spiral emerging simultaneously in a galaxy formation and a cross-section of ammonite fossil / Voronoi cell structures appearing in both a giraffe's coat and a satellite image of dried lakebed / The hexagonal geometry of basalt columns echoing honeycomb and the molecular lattice of graphene]. "
            "The composition forces the eye to find the pattern — nothing is labeled or annotated. The discovery is purely visual. "
            "Lighting: raking natural light at low angle to reveal surface topology through shadow. The pattern must be discoverable through light and shadow alone, not color contrast. "
            "[LLM OPTIONALLY INSERTS ONE SUBTLE VISUAL BRIDGE: e.g., A thin translucent overlay of the mathematical structure just barely visible, like a watermark — present enough to notice on second viewing, invisible on first. Keep it extremely subtle.] "
            "Film grain: heavy, as if this footage was discovered in an archive. "
            "Mood: the vertiginous feeling that reality is structured all the way down and all the way up — that everything rhymes. "
            "8k, photorealistic natural textures, slow reveal cinematography, David Attenborough meets Carl Sagan. 1:1 aspect ratio."
        )
    },
}
