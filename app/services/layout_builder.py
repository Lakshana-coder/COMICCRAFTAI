from typing import Any


def build_comic_layout(
    outline: list[dict[str, Any]],
    story: list[dict[str, Any]],
    image_paths: list[str],
) -> list[dict[str, Any]]:
    """
    Combine outline, story and images into one
    frontend/PDF-friendly structure.
    """

    story_by_panel = {
        item["panel_number"]: item
        for item in story
    }

    layout = []

    for index, panel in enumerate(outline):
        panel_number = panel["panel_number"]

        story_panel = story_by_panel.get(
            panel_number,
            {},
        )

        image_path = (
            image_paths[index]
            if index < len(image_paths)
            else ""
        )

        layout.append(
            {
                "panel_number": panel_number,
                "title": panel.get(
                    "title",
                    f"Panel {panel_number}",
                ),
                "scene_description": panel.get(
                    "scene_description",
                    "",
                ),
                "image_prompt": panel.get(
                    "image_prompt",
                    "",
                ),
                "image_path": image_path,
                "caption": story_panel.get(
                    "caption",
                    "",
                ),
                "narration": story_panel.get(
                    "narration",
                    "",
                ),
                "dialogue": story_panel.get(
                    "dialogue",
                    [],
                ),
            }
        )

    return layout