from pathlib import Path
import re

import os
import requests
from io import BytesIO
from PIL import Image

from app.config import settings


def safe_filename(text):
    text = text or "comic"
    text = re.sub(r"[^a-zA-Z0-9_-]+", "_", text)
    return text.strip("_") or "comic"


def get_client():
    api_key = os.getenv("POLLINATIONS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "POLLINATIONS_API_KEY is missing."
        )

    return api_key
def generate_image(
    image_prompt,
    panel_number=1,
    character_name="",
    setting="",
    art_style="comic book",
):
    """
    Generate one AI comic panel using Pollinations.
    """

    if not image_prompt:
        image_prompt = "Create a comic book scene."

    prompt = f"""
Create ONE detailed comic-book panel.

STORY / PANEL DESCRIPTION:
{image_prompt}

MAIN CHARACTER:
{character_name or "Use the character described in the story."}

SETTING:
{setting or "Use the setting described in the story."}

ART STYLE:
{art_style}, polished digital comic illustration.

IMPORTANT:
- Follow the panel description exactly.
- Show the actual action happening in this panel.
- Keep the main character visually consistent.
- Show the correct environment.
- Include important objects mentioned in the panel.
- Make the character's pose match the action.
- Make the scene cinematic and visually clear.
- Do not replace the described scene with a generic scene.
- Do not add unrelated objects or characters.
- Do not put text, captions, speech bubbles, or narration inside the generated artwork.
- Generate artwork only.
"""

    print("\nGENERATING POLLINATIONS COMIC PANEL...")
    print("PANEL:", panel_number)
    print("PROMPT:", image_prompt)

    pollinations_key = os.getenv("POLLINATIONS_API_KEY")

    if not pollinations_key:
        raise RuntimeError("POLLINATIONS_API_KEY is not set.")

    try:
        from urllib.parse import quote

        encoded_prompt = quote(prompt)

        url = (
            f"https://gen.pollinations.ai/image/{encoded_prompt}"
            f"?model=flux"
        )

        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {pollinations_key}"
            },
            timeout=120,
        )

        response.raise_for_status()

        image = Image.open(BytesIO(response.content))

    except Exception as exc:
        raise RuntimeError(
            f"Pollinations image generation failed: {exc}"
        ) from exc

    if image is None:
        raise RuntimeError(
            "Pollinations did not return an image."
        )

    output_dir = Path("static") / "panels"

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = (
        f"{safe_filename(character_name)}"
        f"_panel_{panel_number}.png"
    )

    output_path = output_dir / filename

    image.save(output_path)

    print(
        "AI COMIC PANEL SAVED:",
        output_path
    )

    return f"/static/panels/{filename}"

