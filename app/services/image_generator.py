from pathlib import Path
import os
import time
import requests
from io import BytesIO
from PIL import Image


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
    Generate one AI comic panel using AI Horde.
    """

    prompt = f"""
Create a single high-quality comic-book illustration.

SCENE:
{image_prompt}

MAIN CHARACTER:
{character_name or "the main character described in the scene"}

SETTING:
{setting or "the environment described in the scene"}

ART STYLE:
{art_style or "colorful modern comic book illustration"}

IMPORTANT:
- Show the actual action happening in this scene.
- Keep the main character visually consistent.
- Show the correct environment.
- Use clear composition.
- Use expressive characters.
- Use cinematic lighting.
- Do not add unrelated objects.
- Do not add text.
- Do not add captions.
- Do not add speech bubbles.
- Create a polished story illustration.
"""

    print("\n==============================")
    print("GENERATING AI HORDE PANEL")
    print("PANEL:", panel_number)
    print("==============================")

    horde_key = os.getenv("AI_HORDE_API_KEY", "0000000000")

    headers = {
        "apikey": horde_key,
        "Client-Agent": "ComicCraftAI:1.0",
        "Content-Type": "application/json",
    }

    try:
        # ---------------------------------------
        # 1. SUBMIT GENERATION
        # ---------------------------------------
        response = requests.post(
            "https://aihorde.net/api/v2/generate/async",
            headers=headers,
            json={
                "prompt": prompt,
                "params": {
                    "width": 512,
                    "height": 512,
                    "steps": 20,
                    "cfg_scale": 7.0,
                    "n": 1,
                },
                "nsfw": False,
                "censor_nsfw": True,
            },
            timeout=30,
        )

        response.raise_for_status()
        generation = response.json()

        request_id = generation.get("id")

        if not request_id:
            raise RuntimeError(
                f"AI Horde did not return a request ID: {generation}"
            )

        print("AI Horde request ID:", request_id)

        # ---------------------------------------
        # 2. WAIT FOR GENERATION
        # ---------------------------------------
        max_attempts = 120

        for attempt in range(max_attempts):

            time.sleep(5)

            check_response = requests.get(
                f"https://aihorde.net/api/v2/generate/check/{request_id}",
                headers=headers,
                timeout=30,
            )

            check_response.raise_for_status()
            status = check_response.json()

            finished = status.get("finished", 0)
            processing = status.get("processing", 0)
            waiting = status.get("waiting", 0)

            print(
                f"AI Horde panel {panel_number}: "
                f"{attempt + 1}/{max_attempts} | "
                f"finished={finished} "
                f"processing={processing} "
                f"waiting={waiting}"
            )

            if status.get("done") or finished >= 1:
                print("Generation completed.")
                break

        else:
            raise RuntimeError(
                "AI Horde is taking too long. "
                "The request is still queued."
            )

        # ---------------------------------------
        # 3. GET COMPLETED IMAGE
        # ---------------------------------------
        result_response = requests.get(
            f"https://aihorde.net/api/v2/generate/status/{request_id}",
            headers=headers,
            timeout=60,
        )

        result_response.raise_for_status()
        result = result_response.json()

        generations = result.get("generations", [])

        if not generations:
            raise RuntimeError(
                f"AI Horde finished but returned no image: {result}"
            )

        image_data = generations[0].get("img")

        if not image_data:
            raise RuntimeError(
                "AI Horde returned an empty image."
            )

        # ---------------------------------------
        # 4. DOWNLOAD IMAGE
        # ---------------------------------------
        if image_data.startswith("http"):

            image_response = requests.get(
                image_data,
                timeout=120,
            )

            image_response.raise_for_status()

            image = Image.open(
                BytesIO(image_response.content)
            )

        else:
            raise RuntimeError(
                "AI Horde returned an unsupported image format."
            )

        # ---------------------------------------
        # 5. SAVE IMAGE
        # ---------------------------------------
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

        print("IMAGE SAVED:", output_path)

        return str(output_path)

    except Exception as exc:

        print("AI HORDE ERROR:", exc)

        raise RuntimeError(
            f"AI image generation failed: {exc}"
        ) from exc
