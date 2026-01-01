import asyncio
import datetime
import uuid

from db import (
    Base,
    engine,
    async_session_maker,
    Project,
    Character,
    Scene,
    Voiceover,
    Place,
    SceneImage,
)

async def create_tables(drop_all: bool = False):
    async with engine.begin() as conn:
        if drop_all:
            await conn.run_sync(Base.metadata.drop_all)
            print("Dropped all tables.")
        await conn.run_sync(Base.metadata.create_all)
        print("Created all tables.")

async def seed_database():
    async with async_session_maker() as session:
        async with session.begin():
            # ---------- PROJECT ----------
            project_id = "cb65c0db-a844-4ede-8b4e-4d5ebe391716"
            project = Project(
                id=project_id,
                name="Rare Human Super Powers",
            )
            session.add(project)

            # ---------- SCENES + SCENE IMAGES ----------
            scenes_data = [
                # (scene_id, start_time, duration, video_prompt, video_src, image_prompt, image_src)
                ("35bf14f9-44f5-41a3-80af-44e752b64471", 0,      5, "Camera pans across the crowd, focusing on the excited individual as they gesture animatedly, conveying a sense of wonder.", None,
                 "A lively crowd of diverse people in a vibrant city square, with one person dramatically pointing upwards, eyes wide with excitement. The sky is bright blue with fluffy clouds.", None),

                ("4418b8ba-6a7c-4cb8-b3fd-06c09b8a0235", 3.8,   6, "The camera slowly zooms in on the figure, highlighting their confident stance as people walk by, oblivious to their extraordinary presence.", None,
                 "A superhero-like figure standing confidently in a park, wearing a casual outfit yet emanating a powerful aura. Sunlight filters through the trees, creating a magical atmosphere.", None),

                ("1e899c88-5626-42f7-86a3-ac1224e8e0b5", 8.3,   6, "The camera slowly circles around the person, emphasizing their stillness and the stark contrast of the broken toy on the floor.", None,
                 "A person sitting alone in a dimly lit room, staring blankly at a broken toy soldier on the floor, their expression devoid of emotion.", None),

                ("705064a2-88e5-4d4c-a3ea-6b62c2633e32", 14.3,  6, "The camera focuses on the hand, then gently pulls back to reveal the person's face, still void of emotion as they glance at their injury.", None,
                 "A close-up shot of a hand gripping a broken bone, a dull ache of emptiness in the expression, contrasting with the vivid colors around them.", None),

                ("d50bad77-d752-4ad4-afa7-995c2ef17216", 19.4,  7, "The camera tracks the person’s gaze, revealing their confusion as they attempt to connect with those around them.", None,
                 "A person standing in a crowded café, looking around with a puzzled expression as familiar faces pass by without recognition.", None),

                ("f102e7aa-846d-4a7d-8a11-05f0f40ac115", 26.8,  8, "The camera follows the person as they walk into the room, with laughter and chatter echoing, intensifying their feeling of isolation.", None,
                 "An open door leading to a crowded party, with one person hesitantly stepping inside, their face filled with uncertainty.", None),

                ("f43ad9de-b7db-4659-91a3-97206fd3c8af", 34.2,  6, "The camera follows the runner from the side, capturing their powerful stride and the beauty of nature surrounding them, emphasizing their endurance.", None,
                 "A lone runner racing through a scenic forest trail, determination etched on their face as they push their limits, sweat glistening in the sunlight.", None),

                ("1ed5afc0-3ff5-46b4-b90c-e8a86ae0c07e", 40.2,  6, "The camera shifts focus to the feet, then tilts up to reveal the runner's fierce expression, embodying relentless energy.", None,
                 "A close-up of the runner's feet pounding against the ground, dirt flying up, showcasing their speed and stamina.", None),

                ("d85b06d5-00e9-487b-968a-e20d5a1eaff7", 46.7,  6, "The camera sweeps through the flowers, capturing the brightness and variety of colors, then focuses on the person's amazed expression.", None,
                 "A vibrant, colorful landscape filled with flowers of every hue, with a person standing in the center, eyes wide with awe.", None),

                ("6b00c9ae-f5d2-4143-8a12-ec7b8be7eb9d", 52.7,  6, "The camera zooms in on their eyes, then pans out to showcase the rainbow of colors enveloping them.", None,
                 "A close-up of the person's eyes reflecting the vivid colors around them, showing a sense of wonder and joy.", None),

                ("4883c7f5-5b84-42f8-a255-363c5c317a21", 57.5,  6, "The camera focuses tightly on the wound, capturing the healing process, then shifts to the person's astonished face.", None,
                 "A hand with a fresh cut, blood trickling down but visibly healing before our eyes, as the person watches in amazement.", None),

                ("c4c087da-a292-43c8-8536-6dd7c22971a6", 63.5,  6, "The camera slowly pulls back, capturing the peaceful surroundings as the person admires their flawless skin.", None,
                 "A serene setting with the person smiling, showcasing their unblemished skin and vibrant health, bringing a sense of wonder.", None),

                ("d5804ee2-a7f2-4545-94ee-1b6521ea1ee0", 67.2,  7, "The camera captures a wide shot of the person at the edge, then zooms in on their face, showing tranquility amidst danger.", None,
                 "A person standing on the edge of a tall building, looking down with a calm and fearless expression, the city sprawling beneath them.", None),

                ("703e450d-a66c-4007-8493-9d34ab24e261", 74.2,  7, "The camera follows closely behind, capturing the person’s fearless strides as they navigate the darkness, oblivious to potential threats.", None,
                 "A scene of the person walking through a dark alley, shadows lurking, yet they stride confidently, unbothered by the surroundings.", None),

                ("f40c9c8a-e53b-46dc-bfda-392ef0251838", 80.6,  6, "The camera follows the person as they move fluidly, showcasing their unique ability to perceive details in the dark.", None,
                 "A person in a dimly lit room, eyes glowing softly as they navigate effortlessly through the shadows, with an air of confidence.", None),

                ("93a314b1-f4df-4b2f-8783-cbe1081ba208", 86.6,  6, "The camera zooms in on their eyes, then pulls back to reveal them smiling, reveling in their extraordinary power.", None,
                 "A close-up of the person’s eyes, reflecting the faint light of the room, highlighting their night vision abilities.", None),

                ("3e001c99-b966-437b-bbee-9bc02acce740", 90.4,  6, "The camera slowly pans out from the figure, capturing the serene beauty of the landscape, emphasizing the weight of their thoughts.", None,
                 "A somber yet hopeful landscape at dusk, with a solitary figure gazing into the distance, reflecting on the reality of human mutations.", None),

                ("58164fa4-334f-484d-9fa8-ac4e07c7ed4d", 95.8,  7, "The camera captures snippets of joy and inspiration as each person performs their extraordinary feats, highlighting the beauty of human potential.", None,
                 "A montage of diverse people showcasing their unique abilities in everyday settings, smiling and inspiring others around them.", None),

                ("45fcd51c-a544-429b-aa2c-824d3fb93403", 103.3, 2, "The camera slowly pulls back to reveal the horizon, leaving a sense of hope and wonder in the air.", None,
                 "A tranquil sunset with silhouettes of people standing together, united in their diversity and uniqueness.", None),
            ]

            for scene_id, start_time, duration, video_prompt, video_src, image_prompt, image_src in scenes_data:
                scene = Scene(
                    id=scene_id,
                    project_id=project_id,
                    start_time=start_time,
                    duration=duration,
                    video_prompt=video_prompt,
                    video_src=video_src,
                )
                session.add(scene)

                # One image per scene (time = "start" by default, as in your original data)
                scene_image = SceneImage(
                    id=str(uuid.uuid4()),  # generate new ID, old one is gone anyway
                    scene_id=scene_id,
                    time="start",
                    prompt=image_prompt,
                    src=image_src,
                )
                session.add(scene_image)

            # ---------- VOICEOVERS ----------
            voiceovers_data = [
                ("417f8a4c-25c3-4d1d-95b2-f8f5f6c9e9cc", 0,    2.8, "[excited] Think humans are average? Think again.", "[excited] Think humans are average? Think again"),
                ("6c6b4033-ef5a-427f-a987-53c70b012375", 3.8,  3.5, "Some people walk around with real-life superpowers.", "Some people walk around with real-life superpowers"),
                ("1ff3ab08-1d8a-4a5f-8411-454942c3c338", 8.3, 10.1, " Imagine feeling absolutely no pain. That’s the reality for those with CIP pain insensitivity — 1 in 125,000! Break a bone? Still nothing.", "Imagine feeling absolutely no pain|That’s the reality for those with|CIP pain insensitivity — 1 in 125|000! Break a bone? Still nothing"),
                ("4dedf854-7fca-4c1c-b219-a069a990d79b", 19.4, 5.4, " \nBut what about those with prosopamnesia? [curious] They remember everything, except faces!", "But what about those with|prosopamnesia? [curious] They remember everything|except faces!"),
                ("bb8836b4-61e9-4f41-ad38-4f3dfe69d31c", 26.8, 6.4, "Can you imagine walking into a room full of people, but knowing none of them?", "Can you imagine walking into|a room full of people|but knowing none of them?"),
                ("43014aa0-2ab1-47cf-b05d-85f6a9dfc301", 34.2,10.5, "  \nThen there are ultra-endurance mutants, 1 in 20,000. They can run almost forever. Their bodies barely produce lactate. [shout] How do they keep going?", "Then there are ultra-endurance mutants|1 in 20000|They can run almost forever|Their bodies barely produce lactate|[shout] How do they keep going?"),
                ("5480751c-ef98-468c-8c26-28a10717d712", 46.7, 9.8, "  \nAnd let’s not forget tetrachromacy! With these extra color cones, they see up to 100 million colors! What must that look like?", "And let’s not forget tetrachromacy!|With these extra color cones|they see up to 100 million|colors! What must that look like?"),
                ("a2d9346a-afb6-46c4-9abd-bce3fff344f6", 57.5, 8.7, "  \nUltra-fast healers are out there too — 1 in 10,000. Cuts close fast. Barely any scars. [whisper] How incredible is that?", "Ultra-fast healers are out there|too — 1 in 10000|Cuts close fast|Barely any scars|[whisper] How incredible is that?"),
                ("1700e89a-f2ea-4abe-a7f9-d7905bde0d4a", 67.2,11.4, "  \nThen, there’s the fearlessness mutation — 1 in 100,000. Their amygdala barely reacts. Near-zero fear! What would life look like if you were never afraid?", "Then|there’s the fearlessness mutation|— 1 in 100000|Their amygdala barely reacts|Near-zero fear! What would life look|like if you were never afraid?"),
                ("3e277cad-591f-4dcf-9e11-17d5dc0fa855", 80.6, 8.8, "  \nFinally, night vision mutations! 1 in 10,000 who can see in low light like a cat. [excited] It’s like having superpowers!", "Finally|night vision mutations! 1 in 10000 who can see in|low light like a cat|[excited] It’s like having superpowers!"),
                ("d02eb5b8-3aea-42f3-aa46-e0c2d09e23ca", 90.4, 4.4, " \n[quietly]These aren’t comic-book tales. They’re mutations, rare and real. ", "[quietly]These aren’t comic-book tales|They’re mutations|rare and real"),
                ("c1a3e1aa-28ef-44e1-89c7-5c4a58d0a3af", 95.8, 5.5, "\n[curious]What do they teach us? That human limits are wider than we think. ", "[curious]What do they teach us? That|human limits are wider than we think"),
                ("7c7f6f1e-1774-4d9d-bfd2-dc8290cdcd54",103.3, 0,   "", ""),
            ]

            for vo_id, start_time, duration, text, text_with_pauses in voiceovers_data:
                vo = Voiceover(
                    id=vo_id,
                    project_id=project_id,
                    start_time=start_time,
                    duration=duration if duration > 0 else None,
                    text=text.strip(),
                    text_with_pauses=text_with_pauses.strip(),
                    src=None,
                    timestamps=None,
                )
                session.add(vo)

        await session.commit()
    print("Database seeded successfully with 'Rare Human Super Powers' project!")

async def main(drop_all: bool = True, seed: bool = False):
    await create_tables(drop_all=drop_all,)
    if seed:
        await seed_database()

if __name__ == "__main__":
    asyncio.run(main(drop_all=True, seed=True))
