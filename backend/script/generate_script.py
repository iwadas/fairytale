from typing import Optional
from AI.llm import LLM
from pydantic import BaseModel

def generate_script(
    llm_client: LLM,
    topic: str = None,
    description: Optional[str] = None,
    story_data: Optional[str] = None,
    reference_stories: Optional[str] = None,
    persistant_characters: bool = False,
    word_limit: int = 180,
) -> str:

    # ADD CONTEXT HISTORY
    # story data - facts, information, research
    # reference stories - example stories about the topic
    if story_data and reference_stories:
        context_instruction = (
            f"Base the story entirely on reference stories and gathered data:\n"
            f"Data:\n{story_data}\n\n"
            f"Example reference stories about the topic: \n{reference_stories}\n\n"
        )
    elif story_data:
        context_instruction = (
            f"Base the story entirely on the following gathered data about the topic:\n{story_data}\n\n"
        )
    elif reference_stories:
        context_instruction = (
            f"Base the story entirely on the following reference stories about the topic: \n{reference_stories}\n\n"
        )

    role_message = {
        "role": "system",
        "content": (
            "You are an expert scriptwriter for short-form video (TikTok/Reels)."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            f"Write a {int(word_limit) - 10}-{int(word_limit) + 10} word script about: { topic }\n\n"
            f"{f'The video should be about: {description}\n\n' if description else ''}"
            f"{context_instruction if (story_data or reference_stories) else ''}"
            "**Strictly follow this \"4-Step Structural Formula\":**\n\n"
            "**Step 1: The \"Pattern Interrupt\" Hook (0-5 seconds)**\n"
            "- Start with a direct, absolute statement that challenges a common belief. \n"
            "- Use the word \"You\" immediately.\n"
            "- Do NOT say \"Hello\" or \"Today we will talk about.\" Just start.\n\n"
            "**Step 2: The \"Mechanism\" (5-20 seconds)**\n"
            "- Explain *how* the phenomenon works using scientific or psychological terminology.\n"
            "- Keep sentences short. fast. Punchy.\n\n"
            "**Step 3: The \"Evolutionary/Deep\" Reason (20-55 seconds)**\n"
            "- Pivot to *why* this happens. \n"
            "- Connect the fact to: Ancient survival, childhood development, deep subconscious protection methods or other psychological mechanisms.\n"
            "- Frame it as: \"Your brain isn't broken; it's protecting you.\"\n"
            "- This section must be empathetic and moody.\n"
            "**Step 4: Split the script using <br> every 2-4 sentences into connected segments.**\n\n"
            "**Tone Guidelines:**\n"
            "- **Voice:** Authoritative, Dark, Moody, Intellectual.\n"
            "- **Rhythm:** Use short sentences. Pause frequently.\n"
            "- **Vocabulary:** Simple words mixed with one or two complex scientific terms for credibility.\n\n"
            "**Write the script now:**"
        )
    }
    
    class ScriptResponse(BaseModel):
        script: str

    response = llm_client.generate(
        messages=[role_message, user_message],
        response_format=ScriptResponse
    )
    
    # normalize script
    # remove doube <br><br> and replace with singe <br>
    # remove \n
    script = response.script.replace("\n", " ").replace("<br><br>", "<br>").strip()
    return script


    
# TESTING
if __name__ == "__main__":
    topic = "The history of the Eiffel Tower"
    story_data = "The Eiffel Tower was constructed from 1887 to 1889 as the entrance arch for the 1889 World's Fair. It was designed by the French engineer Gustave Eiffel and has become a global cultural icon of France and one of the most recognizable structures in the world."
    reference_stories = "1. The Eiffel Tower was initially criticized by some of France's leading artists and intellectuals for its design, but it has since become one of the most visited monuments in the world.\n2. The tower is 324 meters tall andwas the tallest man-made structure in the world until the completion of the Chrysler Building in New York in 1930.\n3. The Eiffel Tower is made of iron and weighs approximately 10,000 tons."
    generated_story = generate_script(topic=topic, story_data=story_data, reference_stories=reference_stories)
    print("Generated Story:\n", generated_story)


    
