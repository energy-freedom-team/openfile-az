"""Stamp signatures onto page 2 of each AZ SOS PDF.

Two modes (image preferred, cursive-text fallback):
  • If the caller provides an image_path that exists on disk → uses the image.
  • Otherwise → renders the candidate's name in Brush Script as the typed
    electronic signature (acceptable under AZ A.R.S. § 41-132 when the filer
    assents to electronic execution; the printed-name field on the same line
    serves as the typed-name attestation).

This module exposes a pure function `stamp()`. The orchestrator is
responsible for walking the committee config and calling `stamp()` for
each generated PDF. v0.2 wires this into the CLI's `sign` subcommand
driven entirely by committee_config.yaml.
"""
from __future__ import annotations
import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import LETTER

# Signature line placement (PDF point coordinates, origin = bottom-left).
# The AZ SOS form page 2 "Printed Name" field rect ends at x≈250; "Date"
# starts at x≈470. The signature underline runs roughly x=270..455 at y≈562.
SIG_X = 275          # left edge of signature
SIG_Y = 552          # baseline for cursive text
SIG_W = 175          # max width
SIG_H = 30           # max height

# Register Brush Script for cursive typed signature if available on the
# host system. Fallback to Times-Italic if not. In the hosted browser
# version, we'll bundle an open-licensed cursive TTF.
CURSIVE_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Brush Script.ttf",   # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",  # Linux fallback (not cursive, but italic)
]
CURSIVE_FONT_NAME = "BrushScript"
HAVE_CURSIVE = False
for path in CURSIVE_FONT_CANDIDATES:
    try:
        pdfmetrics.registerFont(TTFont(CURSIVE_FONT_NAME, path))
        HAVE_CURSIVE = True
        break
    except Exception:
        continue


def _overlay_image(image_path: Path):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    c.drawImage(
        str(image_path), SIG_X, SIG_Y, width=SIG_W, height=SIG_H,
        preserveAspectRatio=True, mask="auto",
    )
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def _overlay_cursive(name: str):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    font = CURSIVE_FONT_NAME if HAVE_CURSIVE else "Times-Italic"
    size = 26
    while size > 12:
        if c.stringWidth(name, font, size) <= SIG_W:
            break
        size -= 1
    c.setFont(font, size)
    c.setFillColorRGB(0.05, 0.05, 0.4)  # dark blue ink color
    c.drawString(SIG_X, SIG_Y, name)
    # Faint attestation marker indicating this is an electronic signature
    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(SIG_X, SIG_Y - 8, "/s/ — typed electronic signature, A.R.S. § 41-132")
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def stamp(
    pdf_path: str | Path,
    typed_name: str,
    image_path: str | Path | None = None,
) -> str:
    """Stamp a signature onto page 2 of the PDF at pdf_path, in place.

    Args:
        pdf_path: absolute path to the PDF to sign.
        typed_name: candidate's / treasurer's full name. Used for the cursive
            fallback, and as alt text when an image is provided.
        image_path: optional path to a PNG signature image with transparent
            background. If provided AND the file exists, it takes precedence
            over the cursive typed signature.

    Returns: a short string describing which mode was used ("image" / "cursive").
    """
    pdf_path = Path(pdf_path)
    if image_path and Path(image_path).exists():
        overlay = _overlay_image(Path(image_path))
        mode = f"image ({Path(image_path).name})"
    else:
        overlay = _overlay_cursive(typed_name)
        mode = "cursive text"
    src = PdfReader(pdf_path)
    out = PdfWriter(clone_from=src)
    out.pages[1].merge_page(overlay)  # page 2 = index 1
    with open(pdf_path, "wb") as f:
        out.write(f)
    return mode
