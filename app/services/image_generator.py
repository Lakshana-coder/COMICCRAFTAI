from pathlib import Path
import re
import os
import requests
from io import BytesIO
from PIL import Image


def safe_filename(text):
    text = text or "comic"
    text = re.sub(r"[^a-zA-Z0-9_-]+", "_", text)
    return text.strip("_") or "comic"


def generate_image(
    image_prompt,
    panel_number=1,
    character_name="",
    setting="",
    art_style="comic book",
):
    """
    Generate one AI comic panel using Pixazo Flux Schnell.
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

    print("\nGENERATING PIXAZO COMIC PANEL...")
    print("PANEL:", panel_number)
    print("PROMPT:", image_prompt)

    api_key = os.getenv("PIXAZO_API_KEY")

    if not api_key:
        raise RuntimeError("PIXAZO_API_KEY is not set.")

    try:
    url = "https://gateway.pixazo.ai/flux-1-schnell/v1/generateRequest"

    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": api_key,
        },
        json={
            "prompt": prompt,
        },
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

image_url = result.get("output")

if not image_url:
    raise RuntimeError(
        f"Pixazo returned no image URL: {result}"
    )

image_response = requests.get(
    image_url,
    timeout=60,
)

image_response.raise_for_status()

image = Image.open(
    BytesIO(image_response.content)
).convert("RGB")

    except Exception as exc:
        raise RuntimeError(
            f"Pixazo image generation failed: {exc}"
        ) from exc

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

    image.save(
        output_path,
        format="PNG",
    )

    print(
        "AI COMIC PANEL SAVED:",
        output_path,
    )

    return f"/static/panels/{filename}"
