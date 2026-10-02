import json
from typing import Any

from google import genai
from google.genai import types

from app.config import settings


def _get_client() -> genai.Client:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Add it to your .env file."
        )

    return genai.Client(
        api_key=settings.GEMINI_API_KEY
    )


def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
) -> list[dict[str, Any]]:
    """
    Generate a structured five-panel comic outline.
    """

    client = _get_client()

    prompt = f"""
You are a professional comic-book story planner.

Create a coherent {settings.PANEL_COUNT}-panel comic outline.

USER STORY:
{story_prompt}

MAIN CHARACTER:
{character_name}

SETTING:
{setting}

TONE:
{tone}

ART STYLE:
{art_style}

Requirements:

1. Create exactly {settings.PANEL_COUNT} panels.
2. Maintain the same main character throughout.
3. The story must have a clear beginning, development, and ending.
4. Each panel must logically continue from the previous panel.
5. Keep the visual descriptions detailed enough for an image-generation model.
6. Do not put dialogue inside the image_prompt.
7. Return ONLY valid JSON.

Return this structure:

{{
  "panels": [
    {{
      "panel_number": 1,
      "title": "Panel title",
      "scene_description": "Description of what happens.",
      "image_prompt": "Detailed visual prompt for the image model."
    }}
  ]
}}
"""
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_FLASH_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                response_mime_type="application/json",
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        data = json.loads(response.text)

    except Exception as exc:
        print(f"Gemini unavailable: {exc}")
        print("Using ComicCraft fallback outline.")

        data = {
            "panels": [
                {
                    "panel_number": 1,
                    "title": "The Beginning",
                    "scene_description": f"{character_name} begins the adventure.",
                    "image_prompt": f"A detailed comic-book scene of {character_name} beginning the adventure."
                },
                {
                    "panel_number": 2,
                    "title": "The Challenge",
                    "scene_description": f"{character_name} faces a difficult challenge.",
                    "image_prompt": f"{character_name} facing a dramatic challenge in a comic-book style."
                },
                {
                    "panel_number": 3,
                    "title": "The Journey",
                    "scene_description": f"{character_name} continues the journey.",
                    "image_prompt": f"{character_name} traveling through an exciting environment, comic-book style."
                },
                {
                    "panel_number": 4,
                    "title": "The Victory",
                    "scene_description": f"{character_name} overcomes the challenge.",
                    "image_prompt": f"{character_name} overcoming the challenge, dramatic comic-book scene."
                },
                {
                    "panel_number": 5,
                    "title": "The Ending",
                    "scene_description": f"{character_name} reaches the conclusion of the story.",
                    "image_prompt": f"{character_name} at the conclusion of the adventure, comic-book style."
                }
            ]
        }
    
   

    panels = data.get("panels")

    if not isinstance(panels, list):
        raise RuntimeError(
            "Gemini outline does not contain a panels list."
        )

    if len(panels) != settings.PANEL_COUNT:
        raise RuntimeError(
            f"Expected {settings.PANEL_COUNT} panels, "
            f"but Gemini returned {len(panels)}."
        )

    cleaned_panels = []

    for index, panel in enumerate(panels, start=1):
        cleaned_panels.append(
            {
                "panel_number": index,
                "title": str(
                    panel.get(
                        "title",
                        f"Panel {index}",
                    )
                ),
                "scene_description": str(
                    panel.get(
                        "scene_description",
                        "",
                    )
                ),
                "image_prompt": str(
                    panel.get(
                        "image_prompt",
                        "",
                    )
                ),
            }
        )

    return cleaned_panels