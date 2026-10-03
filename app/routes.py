from typing import Any
from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
)

from app.config import settings
from app.schemas import (
    ImageTestRequest,
    PromptRequest,
)
from app.services.exporters import save_pdf
from app.services.gemini_flash import (
    generate_outline,
)
from app.services.gemini_pro import (
    generate_story,
)
from app.services.image_generator import (
    generate_image,
)
from app.services.layout_builder import (
    build_comic_layout,
)

router = APIRouter()


def generate_complete_comic(
    request_data: PromptRequest,
) -> tuple[
    list[dict[str, Any]],
    str,
]:
    """
    Run the complete ComicCraft pipeline.
    """

    outline = generate_outline(
        story_prompt=request_data.story_prompt,
        character_name=request_data.character_name,
        setting=request_data.setting,
        tone=request_data.tone,
        art_style=request_data.art_style,
    )

    story = generate_story(
        story_prompt=request_data.story_prompt,
        character_name=request_data.character_name,
        setting=request_data.setting,
        tone=request_data.tone,
        outline=outline,
    )

    image_paths = []

    for panel in outline:
        image_path = generate_image(
            image_prompt=panel["image_prompt"],
            panel_number=panel["panel_number"],
        )

        image_paths.append(image_path)

    layout = build_comic_layout(
        outline=outline,
        story=story,
        image_paths=image_paths,
    )

    pdf_path = save_pdf(
    layout=layout,
    title=request_data.character_name,
    )

# Convert filesystem image paths to browser URLs
    for panel in layout:
        image_path = panel.get("image_path", "")
        if image_path:
            panel["image_path"] = "/static/panels/" + Path(image_path).name

    return layout, pdf_path
@router.get(
"/",
response_class=HTMLResponse,
)
async def home(request: Request):
    return request.app.state.templates.TemplateResponse(
    request=request,
    name="index.html",
    context={
        "request": request,
        "app_name": settings.APP_NAME,
    },
)


@router.post(
    "/generate",
    response_class=HTMLResponse,
)
async def generate_comic(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    try:
        request_data = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        layout, pdf_path = generate_complete_comic(
            request_data
        )

        return request.app.state.templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "request": request,
                "layout": layout,
                "pdf_path": pdf_path,
                "character_name": character_name,
                "setting": setting,
                "tone": tone,
                "art_style": art_style,
            },
        )

    except Exception as exc:
        print("ERROR:",repr(exc))
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "error": str(exc),
            },
            status_code=500,
        )


@router.post(
    "/generate-comic/json",
)
async def generate_comic_json(
    request_data: PromptRequest,
):
    try:
        layout, pdf_path = (
            generate_complete_comic(
                request_data
            )
        )

        return JSONResponse(
            content={
                "success": True,
                "message": (
                    "Comic generated successfully."
                ),
                "layout": layout,
                "pdf_path": pdf_path,
            }
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post(
    "/test-image",
)
async def test_image(
    request_data: ImageTestRequest,
):
    try:
        image_path = generate_image(
            image_prompt=request_data.prompt,
        )

        return {
            "success": True,
            "image_path": image_path,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
async def export_success(
    request: Request,
):
    return request.app.state.templates.TemplateResponse(
        "export_success.html",
        {
            "request": request,
        },
    )
