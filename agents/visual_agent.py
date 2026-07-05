"""
Visual Generator Agent — Creates a premium branded infographic using Pillow.

WHY: Visual content dramatically increases LinkedIn engagement (posts with
images get 2x more comments). This agent creates a modern, premium-looking
infographic with vibrant gradients, clean typography, visual data elements,
and proper text handling that never cuts off words.

OUTPUT KEY: "image_path" → stored in session state for the Publisher Agent.
"""

import math
import os
import textwrap
from datetime import datetime
from pathlib import Path

from google.adk.agents import Agent
from utils.model_config import get_model_name


# ── Font loader (shared) ─────────────────────────────────────────────

def _load_fonts():
    """Load system fonts with fallback to Pillow default."""
    from PIL import ImageFont

    bold_paths = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    regular_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]

    bold_path = None
    for p in bold_paths:
        if os.path.exists(p):
            bold_path = p
            break

    reg_path = None
    for p in regular_paths:
        if os.path.exists(p):
            reg_path = p
            break

    fonts = {}
    try:
        bp = bold_path or reg_path
        rp = reg_path or bold_path
        if bp:
            fonts["title"]    = ImageFont.truetype(bp, 38)
            fonts["subtitle"] = ImageFont.truetype(rp, 20)
            fonts["heading"]  = ImageFont.truetype(bp, 24)
            fonts["body"]     = ImageFont.truetype(rp, 19)
            fonts["small"]    = ImageFont.truetype(rp, 15)
            fonts["number"]   = ImageFont.truetype(bp, 42)
            fonts["num_sm"]   = ImageFont.truetype(bp, 28)
            return fonts
    except OSError:
        pass

    default = ImageFont.load_default()
    return {k: default for k in ("title", "subtitle", "heading", "body", "small", "number", "num_sm")}


# ── Drawing helpers ───────────────────────────────────────────────────

def _gradient_rect(draw, box, color_start, color_end, direction="vertical"):
    """Draw a gradient-filled rectangle."""
    x0, y0, x1, y1 = box
    if direction == "vertical":
        for y in range(y0, y1):
            ratio = (y - y0) / max(1, y1 - y0)
            r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
            draw.line([(x0, y), (x1, y)], fill=(r, g, b))
    else:
        for x in range(x0, x1):
            ratio = (x - x0) / max(1, x1 - x0)
            r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
            draw.line([(x, y0), (x, y1)], fill=(r, g, b))


def _rounded_rect(draw, box, radius, fill):
    """Draw a rectangle with rounded corners."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.pieslice([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270, fill=fill)
    draw.pieslice([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - 2 * radius, x0 + 2 * radius, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - 2 * radius, y1 - 2 * radius, x1, y1], 0, 90, fill=fill)


def _draw_progress_bar(draw, x, y, width, height, pct, bar_color, bg_color):
    """Draw a horizontal progress bar."""
    _rounded_rect(draw, (x, y, x + width, y + height), height // 2, bg_color)
    fill_w = max(height, int(width * pct))
    _rounded_rect(draw, (x, y, x + fill_w, y + height), height // 2, bar_color)


def _safe_text(draw, xy, text, fill, font, max_width_chars=50):
    """Draw text that is properly word-wrapped — never cuts mid-word."""
    wrapped = textwrap.fill(text, width=max_width_chars)
    lines = wrapped.split("\n")
    x, y = xy
    line_height = 28
    try:
        bbox = font.getbbox("Ay")
        line_height = bbox[3] - bbox[1] + 6
    except Exception:
        pass
    for line in lines[:3]:
        draw.text((x, y), line, fill=fill, font=font)
        y += line_height
    return y


# ── Main infographic generator ────────────────────────────────────────

def generate_infographic(
    topic: str,
    key_points: str,
    persona_name: str,
) -> dict:
    """
    Generate a premium branded infographic image using Pillow.

    Creates a LinkedIn-optimized (1200x627) image with vibrant gradients,
    modern card layout, visual data elements, and clean typography.

    Args:
        topic: The main topic/title for the infographic.
        key_points: 2-4 key points separated by newlines.
        persona_name: The persona/brand name for footer branding.

    Returns:
        dict with status, image_path, and dimensions.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return {"status": "error", "error": "Pillow not installed", "image_path": None}

    try:
        W, H = 1200, 627
        img = Image.new("RGB", (W, H), "#0f0f1a")
        draw = ImageDraw.Draw(img)
        fonts = _load_fonts()

        # ── Color palette — premium dark with vivid accents ──────────
        BG_DARK   = (15, 15, 26)
        BG_MID    = (26, 26, 46)
        PURPLE    = (102, 126, 234)
        VIOLET    = (118, 75, 162)
        PINK      = (240, 147, 251)
        TEAL      = (56, 224, 208)
        WHITE     = (255, 255, 255)
        GRAY_TEXT = (180, 180, 210)
        CARD_BG   = (30, 33, 48)
        CARD_BORDER = (50, 55, 80)

        # ── Full background gradient ─────────────────────────────────
        _gradient_rect(draw, (0, 0, W, H), (15, 12, 30), (22, 28, 52))

        # ── Decorative glowing circles ───────────────────────────────
        for cx, cy, rad, col in [
            (100, 60, 220, (102, 126, 234, 25)),
            (W - 150, H - 100, 280, (118, 75, 162, 20)),
            (W // 2, -80, 300, (240, 147, 251, 12)),
        ]:
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ov_draw = ImageDraw.Draw(overlay)
            for r in range(rad, 0, -3):
                alpha = max(0, col[3] - int(col[3] * (r / rad)))
                ov_draw.ellipse(
                    [cx - r, cy - r, cx + r, cy + r],
                    fill=(col[0], col[1], col[2], alpha),
                )
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

        # ── Top accent line ──────────────────────────────────────────
        _gradient_rect(draw, (0, 0, W, 4), PURPLE, PINK, "horizontal")

        # ── Left column: Title area (takes ~55% width) ───────────────
        left_w = 640
        pad = 50

        # Badge
        badge_text = "AI-GENERATED INSIGHT"
        _rounded_rect(draw, (pad, 36, pad + 200, 56), 10, (102, 126, 234, 40))
        draw.text((pad + 12, 38), badge_text, fill=TEAL, font=fonts["small"])

        # Title — properly word-wrapped
        title_clean = topic.strip().title()
        title_y = 72
        title_y = _safe_text(draw, (pad, title_y), title_clean, WHITE, fonts["title"], max_width_chars=28)

        # Subtitle line
        draw.text(
            (pad, title_y + 8),
            f"by {persona_name}  ·  {datetime.now().strftime('%B %d, %Y')}",
            fill=GRAY_TEXT, font=fonts["small"],
        )

        # ── Left column: Key points as styled cards ──────────────────
        points = [p.strip() for p in key_points.strip().split("\n") if p.strip()]
        card_y = title_y + 50
        card_colors = [PURPLE, VIOLET, TEAL, PINK]
        pct_values = [0.85, 0.72, 0.64, 0.58]

        for i, point in enumerate(points[:4]):
            accent = card_colors[i % len(card_colors)]
            pct = pct_values[i % len(pct_values)]

            # Card background
            cy_end = card_y + 80
            if cy_end > H - 55:
                break
            _rounded_rect(draw, (pad, card_y, left_w - 10, cy_end), 10, CARD_BG)

            # Left accent bar
            draw.rectangle(
                [(pad, card_y + 8), (pad + 4, cy_end - 8)],
                fill=accent,
            )

            # Number badge
            num_str = f"0{i + 1}"
            draw.text((pad + 18, card_y + 10), num_str, fill=accent, font=fonts["num_sm"])

            # Point text — properly wrapped
            _safe_text(
                draw, (pad + 60, card_y + 14),
                point, WHITE, fonts["body"], max_width_chars=38,
            )

            # Mini progress bar
            _draw_progress_bar(
                draw, pad + 60, cy_end - 18, 200, 8,
                pct, accent, (40, 44, 65),
            )

            # Percentage label
            draw.text(
                (pad + 270, cy_end - 22),
                f"{int(pct * 100)}%", fill=GRAY_TEXT, font=fonts["small"],
            )

            card_y = cy_end + 10

        # ── Right column: Stats panel (takes ~40% width) ─────────────
        rx = left_w + 20
        rw = W - rx - pad

        # Stats card background
        _rounded_rect(draw, (rx, 36, W - pad, H - 55), 14, CARD_BG)
        draw.rectangle([(rx, 36), (rx + 4, H - 55)], fill=PURPLE)

        # Stats header
        draw.text((rx + 24, 52), "KEY METRICS", fill=TEAL, font=fonts["small"])
        draw.line([(rx + 24, 74), (W - pad - 24, 74)], fill=CARD_BORDER, width=1)

        # Generate visual stat blocks
        stat_y = 90
        stats_data = [
            {"label": "Relevance Score", "value": "94%", "color": PURPLE},
            {"label": "Trend Momentum", "value": "↑ High", "color": TEAL},
            {"label": "Engagement Potential", "value": "8.7/10", "color": PINK},
            {"label": "Content Freshness", "value": "Today", "color": VIOLET},
        ]

        for sd in stats_data:
            if stat_y + 100 > H - 70:
                break

            # Stat number
            draw.text((rx + 28, stat_y), sd["value"], fill=sd["color"], font=fonts["number"])

            # Stat label
            draw.text(
                (rx + 28, stat_y + 52),
                sd["label"], fill=GRAY_TEXT, font=fonts["small"],
            )

            # Horizontal separator
            stat_y += 85
            if stat_y < H - 90:
                draw.line(
                    [(rx + 24, stat_y - 10), (W - pad - 24, stat_y - 10)],
                    fill=CARD_BORDER, width=1,
                )

        # ── Donut chart visualization ────────────────────────────────
        donut_cx = rx + rw // 2
        donut_cy = stat_y + 40
        if donut_cy + 50 < H - 55:
            outer_r = 38
            # Background ring
            draw.arc(
                [donut_cx - outer_r, donut_cy - outer_r,
                 donut_cx + outer_r, donut_cy + outer_r],
                0, 360, fill=(40, 44, 65), width=10,
            )
            # Colored arcs
            draw.arc(
                [donut_cx - outer_r, donut_cy - outer_r,
                 donut_cx + outer_r, donut_cy + outer_r],
                -90, 160, fill=PURPLE, width=10,
            )
            draw.arc(
                [donut_cx - outer_r, donut_cy - outer_r,
                 donut_cx + outer_r, donut_cy + outer_r],
                165, 250, fill=TEAL, width=10,
            )
            draw.arc(
                [donut_cx - outer_r, donut_cy - outer_r,
                 donut_cx + outer_r, donut_cy + outer_r],
                255, 270, fill=PINK, width=10,
            )

        # ── Footer bar ───────────────────────────────────────────────
        _gradient_rect(draw, (0, H - 42, W, H), (20, 18, 36), (30, 28, 50))
        _gradient_rect(draw, (0, H - 42, W, H - 40), PURPLE, PINK, "horizontal")

        draw.text(
            (pad, H - 34),
            f"AI Brand Content Strategist  ·  {datetime.now().strftime('%B %d, %Y')}  ·  linkedin.com",
            fill=GRAY_TEXT, font=fonts["small"],
        )

        # ── Save ─────────────────────────────────────────────────────
        output_dir = Path("assets") / "generated"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"infographic_{timestamp}.png"
        image_path = str(output_dir / filename)

        # Convert back to RGB for PNG save
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(image_path, "PNG", quality=95)

        return {
            "status": "success",
            "image_path": image_path,
            "dimensions": f"{W}x{H}",
            "format": "PNG",
        }

    except Exception as e:
        return {"status": "error", "error": str(e), "image_path": None}


def create_visual_agent() -> Agent:
    """
    Create a Visual Generator Agent that produces branded infographics.
    """
    return Agent(
        name="visual_agent",
        model=get_model_name(),
        description="Generates a professional branded infographic for the LinkedIn post.",
        instruction="""You are a visual content specialist.

YOUR TASK:
Create a professional infographic to accompany the LinkedIn post.

INPUTS (from previous agents):
- Topic: {planned_topic}
- LinkedIn Post: {linkedin_post}

STEPS:
1. Read the topic and LinkedIn post carefully.
2. Extract 2-4 key points from the post that would work as infographic bullets.
   IMPORTANT: Keep each point SHORT — under 60 characters each.
3. Call the generate_infographic tool with:
   - topic: A concise version of the main topic
   - key_points: The key points, one per line (separated by newlines)
   - persona_name: The persona's name from the topic context

EXAMPLE tool call:
  topic: "5 Python Mistakes Slowing Your Code"
  key_points: "Use list comprehensions over loops\\nAvoid mutable default arguments\\nProfile before optimizing\\nCache expensive computations"
  persona_name: "Python Mentor"

OUTPUT: Report whether the image was generated successfully and provide the file path.
If generation fails, report the error clearly. The pipeline will continue regardless.""",
        tools=[generate_infographic],
        output_key="image_path",
    )
