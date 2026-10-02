from pathlib import Path
import os
import re
import time
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
    Generate one AI comic panel using Pixazo FLUX 1 Schnell.
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
        # Pixazo FLUX 1 Schnell generation endpoint
        url = "https://gateway.pixazo.ai/flux-1-schnell/v1/getData"

        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "Ocp-Apim-Subscription-Key": api_key,
            },
            json={
                "prompt": prompt,
                "num_steps": 4,
                "seed": 15,
                "height": 512,
                "width": 512,
            },
            timeout=180,
        )

        response.raise_for_status()

        result = response.json()

        print("PIXAZO RESPONSE:", result)

        request_id = result.get("requestId")

        if not request_id:
            raise RuntimeError(
                f"Pixazo did not return requestId: {result}"
            )

        # Wait for image generation to complete
        image_url = None

        status_url = (
            "https://gateway.pixazo.ai/"
            "flux-1-schnell/v1/checkStatus"
        )

        for attempt in range(36):
            print(
                f"Checking Pixazo status "
                f"({attempt + 1}/36)..."
            )

            time.sleep(5)

            status_response = requests.post(
                status_url,
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                    "Ocp-Apim-Subscription-Key": api_key,
                },
                json={
                    "requestId": request_id
                },
                timeout=60,
            )

            status_response.raise_for_status()

            status_result = status_response.json()

            print("PIXAZO STATUS:", status_result)

            status = str(
                status_result.get("status", "")
            ).lower()

            if status == "completed":
                image_url = status_result.get("output")
                break

            if status in (
                "failed",
                "error",
            ):
                raise RuntimeError(
                    f"Pixazo generation failed: "
                    f"{status_result}"
                )

        if not image_url:
            raise RuntimeError(
                "Pixazo image generation timed out."
            )

        # Download generated image
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

    # Project root
    project_root = (
        Path(__file__).resolve().parents[2]
    )

    # Save generated panels
    output_dir = (
        project_root / "static" / "panels"
    )

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
