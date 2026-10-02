import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF

from app.config import settings


def _clean_pdf_text(text: str) -> str:
    """
    FPDF's built-in Helvetica font does not support
    all Unicode characters. Convert unsupported
    characters safely.
    """

    text = text or ""

    replacements = {
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "•": "-",
        "→": "->",
        "←": "<-",
        "↑": "^",
        "↓": "v",
        "★": "*",
        "♥": "<3",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return (
        text.encode(
            "latin-1",
            errors="replace",
        )
        .decode("latin-1")
    )


def _absolute_image_path(
    image_path: str,
) -> Path:
    """
    Convert a URL-style path such as:

        /static/panels/file.svg

    into the local filesystem path.
    """

    clean = str(image_path).lstrip("/")

    return settings.BASE_DIR / clean


def _convert_svg_to_png(
    svg_path: Path,
) -> Path | None:
    """
    Convert an SVG image into a PNG image that
    FPDF can safely embed.

    Pillow is also used to re-save the PNG as
    RGB/RGBA, which avoids several FPDF image
    parsing problems.
    """

    try:
        import cairosvg
    except ImportError as e:
        print(
            "PDF IMAGE ERROR: cairosvg is not installed."
        )
        print(e)
        return None

    try:
        from PIL import Image
    except ImportError as e:
        print(
            "PDF IMAGE ERROR: Pillow is not installed."
        )
        print(e)
        return None

    try:
        png_path = (
            svg_path.parent
            / f"{svg_path.stem}_pdf.png"
        )

        print(
            "Converting SVG to PNG:",
            svg_path,
        )

        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=1200,
        )

        print(
            "PNG CREATED:",
            png_path,
            png_path.exists(),
        )

        if not png_path.exists():
            print(
                "PNG was not created."
            )
            return None

        print(
            "PNG SIZE:",
            png_path.stat().st_size,
        )

        # Re-save the PNG using Pillow.
        #
        # This makes the image format much safer
        # for FPDF.
        with Image.open(png_path) as image:

            if image.mode not in (
                "RGB",
                "RGBA",
            ):
                image = image.convert("RGBA")

            image.save(
                png_path,
                format="PNG",
            )

        print(
            "PNG READY FOR PDF:",
            png_path,
        )

        return png_path

    except Exception as e:
        print(
            "PDF SVG CONVERSION ERROR:",
            repr(e),
        )
        return None


def _add_panel_image(
    pdf: FPDF,
    image_path: Path,
) -> None:
    """
    Add a panel image to the PDF.

    SVG files are first converted to PNG.
    PNG/JPG files are used directly.
    """

    if not image_path.exists():
        print(
            "IMAGE NOT FOUND:",
            image_path,
        )
        return

    print(
        "PDF IMAGE PATH:",
        image_path,
    )

    print(
        "PDF IMAGE EXISTS:",
        image_path.exists(),
    )

    image_for_pdf = image_path

    # -------------------------------------------------
    # SVG -> PNG
    # -------------------------------------------------

    if image_path.suffix.lower() == ".svg":

        converted = _convert_svg_to_png(
            image_path
        )

        if converted is None:
            print(
                "Could not convert SVG. "
                "Skipping image."
            )
            return

        image_for_pdf = converted

    # -------------------------------------------------
    # Add image to PDF
    # -------------------------------------------------

    try:
        pdf.image(
            str(image_for_pdf),
            x=15,
            y=35,
            w=180,
            h=100,
        )

        print(
            "PDF IMAGE ADDED:",
            image_for_pdf,
        )

    except Exception as e:

        print(
            "PDF IMAGE ERROR:",
            repr(e),
        )


def save_pdf(
    layout: list[dict[str, Any]],
    title: str = "ComicCraft Comic",
) -> str:
    """
    Generate a multi-page PDF.

    One comic panel is placed on each page.
    """

    if not layout:
        raise ValueError(
            "Cannot export an empty comic."
        )

    # -------------------------------------------------
    # Create filename
    # -------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    safe_title = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        title,
    ).strip("_")

    if not safe_title:
        safe_title = "comic"

    filename = (
        f"{safe_title}_{timestamp}.pdf"
    )

    # -------------------------------------------------
    # Make sure export directory exists
    # -------------------------------------------------

    settings.EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        settings.EXPORT_DIR / filename
    )

    # -------------------------------------------------
    # Create PDF
    # -------------------------------------------------

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4",
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15,
    )

    # -------------------------------------------------
    # Process every panel
    # -------------------------------------------------

    for panel in layout:

        pdf.add_page()

        # =============================================
        # PANEL TITLE
        # =============================================

        pdf.set_font(
            "Helvetica",
            "B",
            20,
        )

        panel_number = panel.get(
            "panel_number",
            "",
        )

        panel_title = panel.get(
            "title",
            "",
        )

        panel_heading = _clean_pdf_text(
            f"Panel {panel_number}: "
            f"{panel_title}"
        )

        pdf.set_x(15)

        pdf.multi_cell(
            180,
            10,
            panel_heading,
            align="C",
        )

        pdf.ln(4)

        # =============================================
        # PANEL IMAGE
        # =============================================

        raw_image_path = panel.get(
            "image_path",
            "",
        )

        if raw_image_path:

            image_path = (
                _absolute_image_path(
                    raw_image_path
                )
            )

            _add_panel_image(
                pdf,
                image_path,
            )
            pdf.set_y(142)

        else:

            print(
                "No image_path found for panel:",
                panel_number,
            )

        # =============================================
        # SCENE DESCRIPTION
        # =============================================

        pdf.set_font(
            "Helvetica",
            "I",
            10,
        )

        description = _clean_pdf_text(
            panel.get(
                "scene_description",
                "",
            )
        )

        if description:

            pdf.set_x(15)

            pdf.multi_cell(
                180,
                6,
                description,
            )

        pdf.ln(3)

        # =============================================
        # CAPTION
        # =============================================

        caption = _clean_pdf_text(
            panel.get(
                "caption",
                "",
            )
        )

        if caption:

            pdf.set_font(
                "Helvetica",
                "B",
                11,
            )

            pdf.set_x(15)

            pdf.multi_cell(
                180,
                6,
                f"Caption: {caption}",
            )

            pdf.ln(2)

        # =============================================
        # NARRATION
        # =============================================

        narration = _clean_pdf_text(
            panel.get(
                "narration",
                "",
            )
        )

        if narration:

            pdf.set_font(
                "Helvetica",
                "",
                11,
            )

            pdf.set_x(15)

            pdf.multi_cell(
                180,
                6,
                narration,
            )

            pdf.ln(2)

        # =============================================
        # DIALOGUE
        # =============================================

        dialogue = panel.get(
            "dialogue",
            [],
        )

        if dialogue:

            pdf.ln(3)

            pdf.set_font(
                "Helvetica",
                "B",
                11,
            )

            pdf.set_x(15)

            pdf.multi_cell(
                180,
                6,
                "Dialogue:",
            )

            pdf.set_font(
                "Helvetica",
                "",
                10,
            )

            for line in dialogue:

                if not isinstance(
                    line,
                    dict,
                ):
                    continue

                character = _clean_pdf_text(
                    str(
                        line.get(
                            "character",
                            "Character",
                        )
                    )
                )

                text = _clean_pdf_text(
                    str(
                        line.get(
                            "text",
                            "",
                        )
                    )
                )

                pdf.set_x(15)

                pdf.multi_cell(
                    180,
                    5,
                    f"{character}: {text}",
                )

    # -------------------------------------------------
    # SAVE PDF
    # -------------------------------------------------

    pdf.output(
        str(output_path)
    )

    print(
        "PDF CREATED:",
        output_path,
    )

    # -------------------------------------------------
    # Return browser-accessible path
    # -------------------------------------------------

    return (
        f"/static/exports/{filename}"
    )