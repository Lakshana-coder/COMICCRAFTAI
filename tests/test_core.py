from pathlib import Path

from app.config import settings
from app.services.layout_builder import (
    build_comic_layout,
)


def test_required_directories_exist():
    assert settings.STATIC_DIR.exists()
    assert settings.PANEL_DIR.exists()
    assert settings.EXPORT_DIR.exists()
    assert settings.TEMPLATE_DIR.exists()


def test_layout_builder():

    outline = [
        {
            "panel_number": 1,
            "title": "The Beginning",
            "scene_description": "A hero enters.",
            "image_prompt": "A comic hero",
        }
    ]

    story = [
        {
            "panel_number": 1,
            "caption": "Morning begins.",
            "narration": "The journey starts.",
            "dialogue": [
                {
                    "character": "Hero",
                    "text": "Let's go!",
                }
            ],
        }
    ]

    images = [
        "/static/panels/test.png"
    ]

    layout = build_comic_layout(
        outline,
        story,
        images,
    )

    assert len(layout) == 1
    assert layout[0]["panel_number"] == 1
    assert layout[0]["title"] == "The Beginning"
    assert (
        layout[0]["image_path"]
        == "/static/panels/test.png"
    )
    assert (
        layout[0]["dialogue"][0]["text"]
        == "Let's go!"
    )