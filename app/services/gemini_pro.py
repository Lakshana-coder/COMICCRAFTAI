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


def generate_story(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    outline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Expand the outline into narration, captions,
    and dialogue for every panel.
    """

    client = _get_client()

    outline_json = json.dumps(
        outline,
        indent=2,
        ensure_ascii=False,
    )

    prompt = f"""
You are a professional comic-book writer.

Create the complete narration and dialogue for a
{settings.PANEL_COUNT}-panel comic.

ORIGINAL STORY:
{story_prompt}

MAIN CHARACTER:
{character_name}

SETTING:
{setting}

TONE:
{tone}

PANEL OUTLINE:
{outline_json}

Requirements:

1. Preserve the exact panel order.
2. Every panel must contain:
   - caption
   - narration
   - dialogue
3. Keep dialogue natural and concise.
4. Make the story feel like one continuous comic.
5. Do not create additional panels.
6. Do not modify the panel titles.
7. Return ONLY valid JSON.

Return:

{{
  "panels": [
    {{
      "panel_number": 1,
      "caption": "...",
      "narration": "...",
      "dialogue": [
        {{
          "character": "{character_name}",
          "text": "..."
        }}
      ]
    }}
  ]
}}
"""

    response = client.models.generate_content(
        model=settings.GEMINI_PRO_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.9,
            response_mime_type="application/json",
        ),
    )

    if not response.text:
        raise RuntimeError(
            "Gemini did not return the comic story."
        )

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned invalid JSON for the story."
        ) from exc

    panels = data.get("panels")

    if not isinstance(panels, list):
        raise RuntimeError(
            "Gemini story does not contain a panels list."
        )

    story_panels = []

    for index in range(settings.PANEL_COUNT):
        source = (
            panels[index]
            if index < len(panels)
            else {}
        )

        dialogue = source.get("dialogue", [])

        if not isinstance(dialogue, list):
            dialogue = []

        cleaned_dialogue = []

        for item in dialogue:
            if isinstance(item, dict):
                cleaned_dialogue.append(
                    {
                        "character": str(
                            item.get(
                                "character",
                                character_name,
                            )
                        ),
                        "text": str(
                            item.get("text", "")
                        ),
                    }
                )

        story_panels.append(
            {
                "panel_number": index + 1,
                "caption": str(
                    source.get("caption", "")
                ),
                "narration": str(
                    source.get("narration", "")
                ),
                "dialogue": cleaned_dialogue,
            }
        )

    return story_panels