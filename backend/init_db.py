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
    Place,  # new
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
            project_id = "f445ea30-b133-4d0a-9e2c-d9e4bd19eb33"
            project = Project(
                id=project_id,
                name="Test2",
                created_at=datetime.datetime.fromisoformat("2025-09-30T14:45:09")
            )

            # ---------- CHARACTERS ----------
            characters = [
                Character(
                    id="0z1a2b3c-4d5e6f7g-8h9i0j1k-2l3m4n5o6p7",
                    name="Nature Wizard",
                    prompt="A mystical character adorned with leaves and flowers, wielding a magical staff that resonates with nature.",
                    src="static/images/characters/nature_wizard.png"
                ),
                Character(
                    id="7h8i9j0k-1l2m3n4o-5p6q7r8s-t9u0v1w2x3y4",
                    name="Mega Knight",
                    prompt="A large, muscular character in shiny armor, holding a massive sword, embodying bravery and strength.",
                    src="static/images/characters/mega_knight.png"
                ),
                Character(
                    id="3q4r5s6t-7u8v9w0x-1y2z3a4b-5c6d7e8f9g0",
                    name="Stone Golem",
                    prompt="A towering golem made of rocks and minerals, with a fierce expression and a protective stance.",
                    src="static/images/characters/stone_giant.png"
                ),
                Character(
                    id="1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
                    name="Ojciec Mateusz",
                    prompt="A dark character dressed in dark robes, with piercing eyes and an aura of mystery, standing beside a fearsome dragon.",
                    src="static/images/characters/ojciec_mateusz.png"
                ),
                Character(
                    id="9f8e7d6c-5b4a-3c2d-1e0f-9a8b7c6d5e4f",
                    name="Dragon",
                    prompt="A mystical dragon soaring through the skies, its scales shimmering in the sunlight.",
                    src="static/images/characters/dragon.jpg"
                ),
            ]

            # ---------- SCENES ----------
            scenes = [
                Scene(
                    id="c4e404e8-48a1-42d7-a843-c190c4e26162",
                    scene_number=1,
                    duration=4,
                    image_prompt="A peaceful village scene with the characters Mega Knight, Nature Wizard, and Stone Golem playing together in a sunny meadow.\r\nImportant: The final image/scene should reflect the realm of the characters. If the characters are cartoonish, the environment should also be in a cartoonish style. The goal is for the scene and characters to feel like they naturally belong together, in the same artistic world.",
                    video_prompt="Camera pans across the meadow, showing the characters laughing and playing, with a bright and vibrant color palette.",
                    project=project,
                    image_src="static/images/scenes/scene_c4e404e8-48a1-42d7-a843-c190c4e26162.png",
                    video_src="static/videos/scenes/scene_c4e404e8-48a1-42d7-a843-c190c4e26162.mp4"
                ),
                Scene(
                    id="a7c88a8c-42d2-4012-8b39-6fca019dd7f0",
                    scene_number=2,
                    duration=3,
                    image_prompt="A menacing dark cliff where Ojciec Mateusz appears, casting a shadow across the land.",
                    video_prompt="The camera zooms in on Ojciec Mateusz, with storm clouds gathering in the background, intensifying the atmosphere.",
                    project=project,
                    image_src="static/images/scenes/scene_d79a2d02-f185-4848-a312-5c30db385b81.png",
                    video_src="static/videos/scenes/scene_d79a2d02-f185-4848-a312-5c30db385b81.mp4"
                ),
                Scene(
                    id="b1234567-89ab-cdef-0123-456789abcdef",
                    scene_number=3,
                    duration=4,
                    image_prompt="Ojciec Mateusz summons the Dragon, which bursts forth in flames, creating a terrifying scene of destruction.",
                    video_prompt="Dragon roars with fire engulfing the sky, Ojciec Mateusz stands with arms raised triumphantly.",
                    project=project,
                    image_src="static/images/scenes/scene_5dd4f6f6-0c24-4bda-acb2-e6181a2b1483.png",
                    video_src="static/videos/scenes/scene_5dd4f6f6-0c24-4bda-acb2-e6181a2b1483.mp4"
                ),
                Scene(
                    id="c2345678-90ab-cdef-1234-567890abcdef",
                    scene_number=4,
                    duration=4,
                    image_prompt="The Dragon attacks the peaceful village, breathing fire on houses as villagers run in panic.",
                    video_prompt="The camera shows the Dragon swooping over the village, fire engulfing rooftops, and chaos spreading everywhere.",
                    project=project,
                    image_src="static/images/scenes/scene_1494d543-5e7c-4135-99b6-b39b736b7a4c.png",
                    video_src="static/videos/scenes/scene_1494d543-5e7c-4135-99b6-b39b736b7a4c.mp4"
                ),
                Scene(
                    id="d3456789-01ab-cdef-2345-678901abcdef",
                    scene_number=5,
                    duration=3,
                    image_prompt="Mega Knight stands tall, his sword glowing, rallying the villagers to stand against the Dragon.",
                    video_prompt="Close-up of Mega Knight lifting his sword, determination in his eyes as the camera zooms dramatically.",
                    project=project,
                    image_src="static/images/scenes/scene_f12e0e98-5982-4a87-b38d-4d35aba6354b.png",
                    video_src="static/videos/scenes/scene_f12e0e98-5982-4a87-b38d-4d35aba6354b.mp4"
                ),
                Scene(
                    id="e4567890-12ab-cdef-3456-789012abcdef",
                    scene_number=6,
                    duration=3,
                    image_prompt="Nature Wizard summons vines and flowers that rise to defend the villagers, forming a magical shield.",
                    video_prompt="Magical vines grow rapidly around the village, creating barriers of glowing nature energy.",
                    project=project,
                    image_src="static/images/scenes/scene_3ebaaf52-78af-4809-b06d-829c87e1b655.png",
                    video_src=None
                ),
                Scene(
                    id="f5678901-23ab-cdef-4567-890123abcdef",
                    scene_number=7,
                    duration=3,
                    image_prompt="Stone Golem rises from the earth, his rocky fists ready to strike against the Dragon.",
                    video_prompt="The ground shakes as Stone Golem emerges, raising his fists with dust and debris falling around.",
                    project=project,
                    image_src=None,
                    video_src=None
                ),
                Scene(
                    id="g6789012-34ab-cdef-5678-901234abcdef",
                    scene_number=8,
                    duration=5,
                    image_prompt="All heroes unite, standing together in front of the Dragon with determination and courage.",
                    video_prompt="Camera circles around the heroes as they stand in unity, their powers glowing against the looming Dragon.",
                    project=project,
                    image_src=None,
                    video_src=None
                ),
                Scene(
                    id="h7890123-45ab-cdef-6789-012345abcdef",
                    scene_number=9,
                    duration=6,
                    image_prompt="An epic battle ensues, with the heroes clashing against the Dragon, fire and magic filling the battlefield.",
                    video_prompt="Dynamic shots of the battle: Mega Knight swings his sword, Nature Wizard casts spells, Stone Golem punches the Dragon, Dragon breathes fire.",
                    project=project,
                    image_src=None,
                    video_src=None
                ),
                Scene(
                    id="i8901234-56ab-cdef-7890-123456abcdef",
                    scene_number=10,
                    duration=5,
                    image_prompt="The Dragon is defeated, Ojciec Mateusz is banished, and peace returns to the village with the heroes celebrated.",
                    video_prompt="The Dragon falls, Ojciec Mateusz disappears in shadows, villagers cheer and lift the heroes in joy.",
                    project=project,
                    image_src=None,
                    video_src=None
                ),
            ]

            # ---------- VOICEOVERS ----------
            voiceovers = [
                Voiceover(
                    id="abcd1234-efgh-5678-ijkl-91011mnop",
                    project=project,
                    text="In a land where joy reigned and laughter filled the air, our heroes enjoyed their time in peace.",
                    start_time=1,
                    duration=5,
                    src="static/voiceovers/voiceover_abcd1234-efgh-5678-ijkl-91011mnop.mp3"
                ),
                Voiceover(
                    id="bcde2345-fghi-6789-jklm-101112nopq",
                    project=project,
                    text="But darkness loomed on the horizon, as Ojciec Mateusz revealed his sinister plan.",
                    start_time=6,
                    duration=4,
                    src="static/voiceovers/voiceover_qrst1234-uvwx-5678-yzcd-91011mnop.mp3"
                ),
                Voiceover(
                    id="cdef3456-ghij-7890-klmn-111213opqr",
                    project=project,
                    text="With a mighty roar, the Dragon emerged, striking fear into the hearts of the villagers.",
                    start_time=10,
                    duration=5,
                    src="static/voiceovers/voiceover_ghij1234-klmn-5678-opqr-91011stuv.mp3"
                ),
                Voiceover(
                    id="defg4567-hijk-8901-lmno-121314pqrs",
                    project=project,
                    text="Yet, courage sparked in the hearts of our heroes, who rose to defend their home.",
                    start_time=15,
                    duration=5,
                    src=None
                ),
                Voiceover(
                    id="efgh5678-ijkl-9012-mnop-131415qrst",
                    project=project,
                    text="The battle shook the land, but unity and bravery lit their path forward.",
                    start_time=20,
                    duration=6,
                    src=None
                ),
                Voiceover(
                    id="fghi6789-jklm-0123-nopq-141516rstu",
                    project=project,
                    text="At last, victory was theirs, and peace returned, stronger than ever before.",
                    start_time=26,
                    duration=5,
                    src=None
                ),
            ]

            # ---------- PLACES ----------
            places = []  # empty for now (can seed later)

            # ---------- ADD TO SESSION ----------
            session.add(project)
            session.add_all(characters)
            session.add_all(scenes)
            session.add_all(voiceovers)
            session.add_all(places)

            # ---------- RELATIONSHIPS ----------
            project.characters.extend(characters)

            scenes[0].characters.extend([characters[1], characters[0], characters[2]])
            scenes[1].characters.append(characters[3])
            scenes[2].characters.extend([characters[3], characters[4]])
            scenes[3].characters.extend([characters[3], characters[4]])
            scenes[4].characters.append(characters[1])
            scenes[5].characters.append(characters[0])
            scenes[6].characters.append(characters[2])
            scenes[7].characters.extend(characters)
            scenes[8].characters.extend(characters)
            scenes[9].characters.extend([characters[3], characters[4], characters[0]])

    print("Seeding finished.")

async def main(drop_all: bool = True, seed: bool = True):
    await create_tables(drop_all=drop_all)
    if seed:
        await seed_database()

if __name__ == "__main__":
    asyncio.run(main(drop_all=True, seed=True))
