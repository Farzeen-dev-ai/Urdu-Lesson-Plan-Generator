from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
FONTS_DIR = BASE_DIR / "fonts"

# --- Configuration for Coordinates ---
# Estimated for daily_plan_empty_2.jpeg and weekly_plan_empty_2.jpeg
# Format: "Dictionary_Key": (x_coordinate, y_coordinate) in pixels.
COORDINATES = {
    "DailyPlan": {
        # --- User Inputs ---
        "Topic": (220, 200),
        "LessonNo": (230, 230),
        "TeacherName": (310, 260),
        "SubjectTitleCode": (310, 290),
        "Technology": (230, 320),
        "Year": (630, 320),

        # --- AI Generated Content ---
        "SpecificObjectives": (120, 380),
        "Introduction": (120, 440),
        "Presentation": (120, 500),
        "TeachingAids": (120, 560),
        "LessonContents": (130, 640),
        "KeyPoints": (380, 640),
        "TimeAllocation": (880, 640),
        "ActivityFeedback": (120, 1060),
        "Assignment": (120, 1140),
    },

    "WeeklyPlan": {
        # --- User Inputs ---
        "AcademicSession": (140, 110),
        "TechTradeCourse": (370, 110),
        "Subject": (370, 150),
        "Duration": (930, 110),
        "WeekNo": (80, 220),
        "PreparedBy": (220, 1370),

        # --- AI Generated Content ---
        "TopicsWeeklyPlanner": (230, 220),
    },
}


def find_font() -> Path:
    """Find a custom Urdu font, preferring Jameel Noori Nastaleeq."""
    candidates = [
        FONTS_DIR / "JameelNooriNastaleeq.ttf",
        FONTS_DIR / "Jameel Noori Nastaleeq.ttf",
        FONTS_DIR / "NotoNaskhArabic-Regular.ttf",
        FONTS_DIR / "NotoNaskhArabic.ttf",
    ]

    for font_path in candidates:
        if font_path.exists():
            return font_path

    raise FileNotFoundError(
        "No Urdu font found. Add fonts/JameelNooriNastaleeq.ttf "
        "or another supported Urdu TTF font to the repository."
    )


def load_font(size: int = 30) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(find_font()), size)


def shape_urdu(text: Any) -> str:
    """Reshape Arabic/Urdu glyphs and apply bidi display ordering for PIL."""
    text = "" if text is None else str(text)
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def draw_rtl_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: Any,
    font: ImageFont.FreeTypeFont,
    fill: str = "black",
    max_width: int | None = None,
    line_spacing: int = 8,
):
    """
    Draw Urdu correctly using arabic-reshaper + python-bidi.
    If max_width is supplied, text is wrapped approximately by pixel width.
    """
    text = "" if text is None else str(text)

    if not max_width:
        draw.text(xy, shape_urdu(text), font=font, fill=fill)
        return

    # Word-based wrapping for longer fields.
    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        display_candidate = shape_urdu(candidate)
        bbox = draw.textbbox((0, 0), display_candidate, font=font)
        width = bbox[2] - bbox[0]

        if current and width > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    x, y = xy
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_height = (bbox[3] - bbox[1]) + line_spacing

    for line in lines:
        draw.text((x, y), shape_urdu(line), font=font, fill=fill)
        y += line_height


def _template_path(template_type: str) -> Path:
    if template_type == "Daily Lesson Plan":
        return TEMPLATES_DIR / "daily_plan_empty_2.jpeg"
    if template_type == "Weekly Lesson Plan":
        return TEMPLATES_DIR / "weekly_plan_empty_2.jpeg"
    raise ValueError(f"Unsupported template type: {template_type}")


def render_lesson_plan(template_type: str, data: dict[str, Any]) -> bytes:
    """Load the selected template, draw all fields, and return PNG bytes."""
    template_path = _template_path(template_type)

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    image = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    coordinate_group = (
        COORDINATES["DailyPlan"]
        if template_type == "Daily Lesson Plan"
        else COORDINATES["WeeklyPlan"]
    )

    # Change these sizes as needed for your actual template.
    admin_font = load_font(28)
    content_font = load_font(27)

    admin_fields = (
        [
            "TeacherName", "Topic", "LessonNo",
            "SubjectTitleCode", "Technology", "Year"
        ]
        if template_type == "Daily Lesson Plan"
        else [
            "AcademicSession", "TechTradeCourse", "Subject",
            "Duration", "WeekNo", "PreparedBy"
        ]
    )

    for field in admin_fields:
        if field in coordinate_group and field in data:
            draw_rtl_text(
                draw,
                coordinate_group[field],
                data[field],
                admin_font,
                max_width=550,
            )

    ai_fields = (
        [
            "SpecificObjectives", "Introduction", "Presentation",
            "TeachingAids", "LessonContents", "KeyPoints",
            "TimeAllocation", "ActivityFeedback", "Assignment"
        ]
        if template_type == "Daily Lesson Plan"
        else ["TopicsWeeklyPlanner"]
    )

    for field in ai_fields:
        if field in coordinate_group and field in data:
            value = data[field]

            # JSON values can be lists/dictionaries. Convert them to readable text.
            if isinstance(value, (dict, list)):
                value = _structured_value_to_text(value)

            draw_rtl_text(
                draw,
                coordinate_group[field],
                value,
                content_font,
                max_width=1500,
            )

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _structured_value_to_text(value: Any) -> str:
    """Convert nested JSON values into readable Urdu-form text."""
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            parts.append(f"{key}: {item}")
        return "\n".join(parts)

    if isinstance(value, list):
        return "\n".join(f"• {item}" for item in value)

    return str(value)