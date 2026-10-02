from pathlib import Path
import os
import time
import requests
from io import BytesIO
from PIL import Image

from app.config import settings


def safe_filename(text):
    text = text or "comic"
    filename = "".join(
        c if c.isalnum() or c in ("-", "_") else "_"
        for c in text
    )
    return filename.strip("_") or "comic"


def generate_image(
    image_prompt,
    panel_number=1,
    character_name="",
    setting="",
    art_style="comic book",
):
    """
    Generate an AI comic panel using AI Horde.
    No Hugging Face or Pollinations API key is required.
    """

    # Build a detailed prompt so the generated picture matches the story.
    prompt = f"""
Create a single detailed comic-book panel.

SCENE:
{image_prompt}

MAIN CHARACTER:
{character_name or "the main character described in the scene"}

SETTING:
{setting or "the environment described in the scene"}

ART STYLE:
{art_style or "modern colorful comic book illustration"}

IMPORTANT:
Show the actual action happening in this scene.
Keep the character visually consistent.
Show the correct environment and important objects.
Clear composition, expressive characters, cinematic lighting.
Do not add unrelated objects.
Do not add text, captions, speech bubbles, or narration.
High quality AI comic illustration.
"""

    print("\nGENERATING AI HORDE COMIC PANEL...")
    print("PANEL:", panel_number)
    print("PROMPT:", prompt)

    # AI Horde provides an anonymous API key.
    # Registered users can later replace this with their own key.
    horde_key = os.getenv("AI_HORDE_API_KEY", "0000000000")

    try:
        # Submit generation request.
        response = requests.post(
            "https://aihorde.net/api/v2/generate/async",
            headers={
                "apikey": horde_key,
                "Client-Agent": "ComicCraftAI:1.0",
                "Content-Type": "application/json",
            },
            json={
                "prompt": prompt,
                "params": {
                    "width": 768,
                    "height": 768,
                    "steps": 25,
                    "cfg_scale": 7.5,
                    "n": 1,
                },
                "models": [
                    "SDXL 1.0"
                ],
                "nsfw": False,
            },
            timeout=60,
        )

        response.raise_for_status()
        generation = response.json()

        request_id = generation.get("id")

        if not request_id:
            raise RuntimeError(
                "AI Horde did not return a generation request ID."
            )

        print("AI Horde request:", request_id)

        # Wait for the volunteer worker to finish.
        for attempt in range(60):
            time.sleep(5)

            status_response = requests.get(
                f"https://aihorde.net/api/v2/generate/check/{request_id}",
                headers={
                    "apikey": horde_key,
                    "Client-Agent": "ComicCraftAI:1.0",
                },
                timeout=30,
            )

            status_response.raise_for_status()
            status = status_response.json()

            print(
                f"Waiting for image... "
                f"{attempt + 1}/60"
            )

            if status.get("done"):
                break

        else:
            raise RuntimeError(
                "AI Horde image generation timed out."
            )

        # Retrieve completed generation.
        result_response = requests.get(
            f"https://aihorde.net/api/v2/generate/status/{request_id}",
            headers={
                "apikey": horde_key,
                "Client-Agent": "ComicCraftAI:1.0",
            },
            timeout=60,
        )

        result_response.raise_for_status()
        result = result_response.json()

        generations = result.get("generations", [])

        if not generations:
            raise RuntimeError(
                "AI Horde finished but returned no image."
            )

        image_url = generations[0].get("img")

        if not image_url:
            raise RuntimeError(
                "AI Horde returned no image URL."
            )

        # Download the generated image.
        image_response = requests.get(
            image_url,
            timeout=120,
        )

        image_response.raise_for_status()

        image = Image.open(
            BytesIO(image_response.content)
        )

        # Save to the same location expected by ComicCraft.
        output_dir = Path("static") / "panels"
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = (
            f"panel_{panel_number}_"
            f"{safe_filename(character_name)}.png"
        )

        output_path = output_dir / filename

        image.save(
            output_path,
            format="PNG",
        )

        print(
            "IMAGE SAVED:",
            output_path
        )

        return str(output_path)

    except Exception as exc:
        raise RuntimeError(
            f"AI image generation failed: {exc}"
        ) from exc
