"""
Visual Generator Agent — Creates a branded infographic image using Pillow.

WHY: Visual content dramatically increases LinkedIn engagement (posts with
images get 2x more comments). This agent creates a professional infographic
using Pillow (Python Imaging Library), ensuring the pipeline ALWAYS produces
an image regardless of external API availability.

DESIGN: LinkedIn-style blue/white professional color scheme.
FALLBACK: Pillow is a local library — no API keys, no network calls, always works.

OUTPUT KEY: "image_path" → stored in session state for the Publisher Agent.
"""

import os
import textwrap
from datetime import datetime
from pathlib import Path

from google.adk.agents import Agent


def generate_infographic(
    topic: str,
    key_points: str,
    persona_name: str,
) -> dict:
    """
    Generate a professional branded infographic image using Pillow.

    Creates a LinkedIn-optimized image (1200x627) with a blue/white
    gradient, topic title, key points, and persona branding.

    Args:
        topic: The main topic/title for the infographic.
        key_points: 2-4 key points to display, separated by newlines.
        persona_name: The persona/brand name for the footer branding.

    Returns:
        dict with status, image_path, and dimensions.
    """
    # ── Import Pillow inside the function for graceful error handling ──
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return {
            "status": "error",
            "error": "Pillow is not installed. Run: pip install Pillow",
            "image_path": None,
        }

    try:
        # ── Canvas setup (LinkedIn recommended: 1200×627) ─────────────
        width, height = 1200, 627
        img = Image.new("RGB", (width, height), "#FFFFFF")
        draw = ImageDraw.Draw(img)

        # ── LinkedIn-style blue/white color palette ───────────────────
        colors = {
            "primary_blue": (10, 102, 194),     # #0A66C2 — LinkedIn blue
            "dark_blue": (0, 65, 130),           # #004182 — header gradient start
            "light_bg": (232, 244, 253),         # #E8F4FD — content background
            "white": (255, 255, 255),
            "text_dark": (25, 25, 25),           # #191919
            "text_secondary": (102, 102, 102),   # #666666
            "accent_blue": (0, 115, 177),        # #0073B1
            "highlight": (26, 125, 212),         # #1A7DD4
        }

        # ── Draw gradient background ─────────────────────────────────
        # Header zone: dark blue → primary blue gradient
        for y in range(height):
            if y < 200:
                ratio = y / 200
                r = int(colors["dark_blue"][0] * (1 - ratio) + colors["primary_blue"][0] * ratio)
                g = int(colors["dark_blue"][1] * (1 - ratio) + colors["primary_blue"][1] * ratio)
                b = int(colors["dark_blue"][2] * (1 - ratio) + colors["primary_blue"][2] * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            elif y < 210:
                # Accent stripe separating header from content
                draw.line([(0, y), (width, y)], fill=colors["accent_blue"])
            else:
                # Light background for content area
                draw.line([(0, y), (width, y)], fill=colors["light_bg"])

        # ── Load fonts (system fonts → Pillow default fallback) ───────
        # WHY: We try common system font paths first, then fall back to
        # Pillow's built-in font. This ensures the image generates on
        # ANY operating system without crashing.
        title_font = body_font = small_font = None
        font_paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    title_font = ImageFont.truetype(font_path, 36)
                    body_font = ImageFont.truetype(font_path, 22)
                    small_font = ImageFont.truetype(font_path, 16)
                    break
                except OSError:
                    continue

        # Fallback to Pillow's built-in bitmap font
        if title_font is None:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # ── Draw title in the header area ─────────────────────────────
        wrapped_title = textwrap.fill(topic, width=40)
        title_y = 40
        for line in wrapped_title.split("\n")[:3]:  # Cap at 3 lines
            draw.text((60, title_y), line, fill=colors["white"], font=title_font)
            title_y += 45

        # ── Draw persona branding subtitle ────────────────────────────
        draw.text(
            (60, 160),
            f"by {persona_name}",
            fill=(176, 212, 241),  # Light blue for readability on dark bg
            font=small_font,
        )

        # ── Draw decorative header circles ────────────────────────────
        draw.ellipse(
            [width - 150, -50, width + 50, 150],
            fill=colors["highlight"],
        )
        draw.ellipse(
            [width - 80, 50, width + 20, 150],
            fill=(46, 139, 216),  # Slightly lighter blue
        )

        # ── Draw key points in the content area ──────────────────────
        points = [p.strip() for p in key_points.strip().split("\n") if p.strip()]
        point_y = 240

        for i, point in enumerate(points[:4]):  # Max 4 points
            # Bullet circle
            cx, cy = 60, point_y + 8
            draw.ellipse(
                [cx, cy, cx + 12, cy + 12],
                fill=colors["primary_blue"],
            )

            # Point text (wrapped to fit)
            wrapped_point = textwrap.fill(point, width=55)
            for line in wrapped_point.split("\n")[:2]:  # Max 2 lines per point
                draw.text(
                    (85, point_y),
                    line,
                    fill=colors["text_dark"],
                    font=body_font,
                )
                point_y += 30
            point_y += 20  # Gap between points

        # ── Draw footer bar ──────────────────────────────────────────
        footer_y = height - 50
        draw.rectangle(
            [(0, footer_y), (width, height)],
            fill=colors["primary_blue"],
        )
        draw.text(
            (60, footer_y + 14),
            f"AI Brand Content Strategist  •  {datetime.now().strftime('%B %d, %Y')}",
            fill=colors["white"],
            font=small_font,
        )

        # ── Save the image ───────────────────────────────────────────
        output_dir = Path("assets") / "generated"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"infographic_{timestamp}.png"
        image_path = str(output_dir / filename)

        img.save(image_path, "PNG", quality=95)

        return {
            "status": "success",
            "image_path": image_path,
            "dimensions": f"{width}x{height}",
            "format": "PNG",
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "image_path": None,
        }


def create_visual_agent() -> Agent:
    """
    Create a Visual Generator Agent that produces branded infographics.

    The agent reads the planned topic and LinkedIn post from session state,
    extracts key points, and calls the generate_infographic tool to create
    a supporting image.

    Returns:
        Configured ADK Agent instance.
    """
    return Agent(
        name="visual_agent",
        model="gemini-2.5-flash",
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
