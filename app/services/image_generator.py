from pathlib import Path
import os
import re
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
    Generate one AI comic panel using Pollinations AI.
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
- Do not replace the described scene with a generic scene.
- Do not add unrelated objects or characters.
- Do not put text, captions, speech bubbles, or narration inside the generated artwork.
- Generate artwork only.
"""

    print("\nGENERATING POLLINATIONS COMIC PANEL...")
    print("PANEL:", panel_number)
    print("PROMPT:", image_prompt)

    # Pollinations API key
    api_key = os.getenv("POLLINATIONS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "POLLINATIONS_API_KEY is not set."
        )

    try:
        # Pollinations image generation endpoint
        url = "https://gen.pollinations.ai/image/" + requests.utils.quote(
            prompt,
            safe=""
        )

        params = {
            "model": "flux",
            "width": 1024,
            "height": 1024,
            "seed": panel_number,
        }

        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=180,
        )

        response.raise_for_status()

        # Make sure we actually received image data
        content_type = response.headers.get("content-type", "")

        if not content_type.startswith("image/"):
            raise RuntimeError(
                f"Pollinations returned unexpected content type: "
                f"{content_type}\n{response.text[:500]}"
            )

        # Save generated image
        output_dir = Path("generated_images")
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            f"{safe_filename(character_name or 'comic')}"
            f"_panel_{panel_number}.png"
        )

        output_path = output_dir / filename

        image = Image.open(BytesIO(response.content))
        image.save(output_path, format="PNG")

        print("IMAGE GENERATED SUCCESSFULLY")
        print("SAVED TO:", output_path)

        return str(output_path)

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "unknown"

        error_text = ""
        if e.response is not None:
            try:
                error_text = e.response.text[:1000]
            except Exception:
                pass

        raise RuntimeError(
            f"Pollinations image generation failed: "
            f"HTTP {status}: {error_text}"
        )

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Pollinations request failed: {e}"
        )

    except Exception as e:
        raise RuntimeError(
            f"Image generation failed: {e}"
        )
