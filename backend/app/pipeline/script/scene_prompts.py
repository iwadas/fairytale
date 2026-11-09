"""Prompt templates for the scene generator.

Agent 1 ("Visual Director") brainstorms scene ideas for a script part, picking a
style from the catalogue. Agent 2 ("Prompt Engineer") expands each idea into an
image prompt and a video prompt.

The text here is sent verbatim to the LLM; edit with care.
"""
from collections.abc import Mapping

from app.pipeline.script.styles import StyleDefinition

# ------------------------------------------
# Agent 1: scene idea generation
# ------------------------------------------
IDEA_SYSTEM_PROMPT_PREFIX = (
    "You are a highly creative Visual Director for a video production pipeline. "
    "Your job is to brainstorm short, high-impact scene ideas for specific parts of a script. "
    "CRITICAL INSTRUCTION: You must build your visual concepts AROUND the provided available styles. "
    "Do not brainstorm an idea and then assign a style. Instead, you must first select an available style, "
    "read its 'use_case', and let those specific constraints dictate what happens in the scene. "
    "You do not need to worry about character or location consistency. We are generating many short, "
    "rapid-fire scenes to cherry-pick the best ones later - so try to use a variety of ideas. "
    "Here is the full script just for context:\n\n"
)

IDEA_OUTPUT_ORDER_INSTRUCTIONS = (
    "To ensure the style drives the visual, you MUST generate your output in this STRICT ORDER:\n"
    "- \"style\": FIRST, pick the name of the most appropriate style from the available list.\n"
    "- \"reasoning\": SECOND, explain why this style's specific 'use_case' fits the emotional or narrative context of the sentence.\n"
    "- \"idea\": FINALLY, describe the visual scene. This description MUST strictly adhere to the style and use case you just selected. "
    "Keep it concise—focus on the core visual subject and environment.\n\n"
)


def format_style_catalogue(styles: Mapping[str, StyleDefinition]) -> str:
    """One ``- name: use_case`` line per style, for Agent 1 to choose from."""
    return "\n".join([f"- {name}: {data['use_case']}" for name, data in styles.items()])


def build_idea_messages(
    script: str, sentence: str, num_scenes: int, style_catalogue: str
) -> list[dict[str, str]]:
    """Messages for Agent 1: brainstorm ``num_scenes`` ideas for one sentence."""
    return [
        {
            "role": "system",
            "content": IDEA_SYSTEM_PROMPT_PREFIX + script,
        },
        {
            "role": "user",
            "content": (
                f"Generate EXACTLY {num_scenes} raw visual concepts for this sentence: \"{sentence}\".\n\n"
                "Available styles and their use cases:\n"
                f"{style_catalogue}\n\n"
                + IDEA_OUTPUT_ORDER_INSTRUCTIONS
            ),
        },
    ]


# ------------------------------------------
# Agent 2: prompt expansion
# ------------------------------------------
EXPANSION_SYSTEM_PROMPT = (
    "You are an expert AI Prompt Engineer specializing in Text-to-Image (Nano Banana Pro) "
    "and Image-to-Video models (e.g. Veo Pro, Sora Pro, Kling AI, Seedance)."
)

EXPANSION_TASK_INSTRUCTIONS = (
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


def build_expansion_messages(idea: str, reasoning: str, style_prompt: str) -> list[dict[str, str]]:
    """Messages for Agent 2: expand one idea into ``image_prompt`` + ``video_prompt``."""
    return [
        {
            "role": "system",
            "content": EXPANSION_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": (
                "I have a raw scene idea:\n"
                f"idea: {idea}\n"
                f"reasoning: {reasoning}\n"
                f"style: {style_prompt}\n\n"
                + EXPANSION_TASK_INSTRUCTIONS
            ),
        },
    ]
