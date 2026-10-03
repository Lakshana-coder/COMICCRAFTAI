from pathlib import Path
from app.config import settings
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

    # ---------------------------------------------------------
    # GET POLLINATIONS API KEY
    # ---------------------------------------------------------
    api_key = os.getenv("POLLINATIONS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "POLLINATIONS_API_KEY is not configured on the server."
        )

    api_key = api_key.strip()

    if not api_key:
        raise RuntimeError(
            "POLLINATIONS_API_KEY is empty."
        )

    # ---------------------------------------------------------
    # POLLINATIONS IMAGE API
    # ---------------------------------------------------------
    url = (
        "https://gen.pollinations.ai/image/"
        + requests.utils.quote(prompt, safe="")
    )

    params = {
        "model": "flux",
        "width": 1024,
        "height": 1024,
        "seed": panel_number,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",
    }

    try:
        print("Calling Pollinations...")

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=180,
        )

        print("Pollinations HTTP status:", response.status_code)

        # -----------------------------------------------------
        # HANDLE AUTHORIZATION ERROR
        # -----------------------------------------------------
        if response.status_code == 401:
            raise RuntimeError(
                "Pollinations rejected the API key (401 Unauthorized). "
                "Check the POLLINATIONS_API_KEY environment variable "
                "on Render and make sure it contains the current key."
            )

        # -----------------------------------------------------
        # HANDLE FORBIDDEN
        # -----------------------------------------------------
        if response.status_code == 403:
            raise RuntimeError(
                "Pollinations rejected the request (403 Forbidden). "
                "Check that the Pollinations API key is active and "
                "has permission to generate images."
            )

        # -----------------------------------------------------
        # OTHER HTTP ERRORS
        # -----------------------------------------------------
        if not response.ok:
            try:
                error_text = response.text[:1500]
            except Exception:
                error_text = "Unable to read error response."

            raise RuntimeError(
                f"Pollinations image generation failed: "
                f"HTTP {response.status_code}: {error_text}"
            )

        # -----------------------------------------------------
        # CHECK RESPONSE TYPE
        # -----------------------------------------------------
        content_type = (
            response.headers.get("content-type", "")
            .lower()
            .strip()
        )

        print("Pollinations content type:", content_type)

        if not content_type.startswith("image/"):
            try:
                body = response.text[:1500]
            except Exception:
                body = "Unable to read response."

            raise RuntimeError(
                "Pollinations did not return an image.\n"
                f"Content-Type: {content_type}\n"
                f"Response: {body}"
            )

        # -----------------------------------------------------
        # SAVE IMAGE
        # -----------------------------------------------------
        output_dir = settings.PANEL_DIR
        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = (
            f"{safe_filename(character_name or 'comic')}"
            f"_panel_{panel_number}.png"
        )

        output_path = output_dir / filename

        image = Image.open(
            BytesIO(response.content)
        )

        # Convert to RGB/RGBA if necessary
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")

        image.save(
            output_path,
            format="PNG"
        )

        print("IMAGE GENERATED SUCCESSFULLY")
        print("SAVED TO:", output_path)

        return str(output_path)

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Pollinations request timed out. "
            "Please try generating the comic again."
        )

    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Could not connect to Pollinations: {e}"
        )

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Pollinations request failed: {e}"
        )

    except RuntimeError:
        raise

    except Exception as e:
        raise RuntimeError(
            f"Image generation failed: {e}"
        )
