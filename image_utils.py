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
# Mapped exactly to the GOVT. COLLEGE OF TECHNOLOGY (W) SAHIWAL form.
COORDINATES = {
    "DailyPlan": {
        # --- User Inputs (Administrative) ---
        "Topic": (300, 305),
        "LessonNo": (250, 345),
        "TeacherName": (420, 380),
        "SubjectTitleCode": (420, 415),
        "Technology": (270, 450),
        "Year": (730, 450),

        # --- AI Generated Content ---
        "SpecificObjectives": (120, 520),
        "Introduction": (120, 630),
        "Presentation": (120, 730),
        "TeachingAids": (120, 800),
        
        # --- Table Columns ---
        "LessonContents": (120, 930),
        "KeyPoints": (380, 930),
        "TimeAllocation": (880, 930),
        
        # --- Bottom Section ---
        "ActivityFeedback": (120, 1330),
        "Assignment": (120, 1410),
    },

    "WeeklyPlan": {
        # --- User Inputs ---
        "AcademicSession": (300, 300),
        "TechTradeCourse": (300, 350),
        "Subject": (300, 400),
        "Duration": (750, 300),
        "WeekNo": (750, 350),
        "PreparedBy": (750, 400),

        # --- AI Generated Content ---
        "TopicsWeeklyPlanner": (120, 550),
    },
}

# --- Column Boundary Limits ---
# Prevents text from spilling into the next column or off the page.
MAX_WIDTHS = {
    "DailyPlan": {
        "SpecificObjectives": 900,
        "Introduction": 900,
        "Presentation": 900,
        "TeachingAids": 900,
        "LessonContents": 240,   # Stays inside the first column
        "KeyPoints": 480,        # Stays inside the middle column
        "TimeAllocation": 200,   # Stays inside the last column
        "ActivityFeedback": 900,
        "Assignment": 900,
    },
    "WeeklyPlan": {
        "TopicsWeeklyPlanner": 900,
    }
}


def find_font() -> Path:
    candidates = [
        FONTS_DIR / "JameelNooriNastaleeq.ttf",
        FONTS_DIR / "Jameel Noori Nastaleeq.ttf",
        FONTS_DIR / "NotoNaskhArabic-Regular.ttf",
        FONTS_DIR / "NotoNaskhArabic.ttf",
    ]
    for font_path in candidates:
        if font_path.exists():
            return font_path
    raise FileNotFoundError("No Urdu font found in the fonts/ folder.")


def load_font(size: int = 30) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(find_font()), size)


def shape_urdu(text: Any) -> str:
    """Reshape Arabic/Urdu glyphs and apply bidi display ordering."""
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
    Draw Urdu correctly. Preserves line breaks (\n) and wraps long text safely.
    """
    text = "" if text is None else str(text)
    
    # Split by explicit line breaks first to preserve AI bullet points
    paragraphs = text.split('\n')
    
    x, y = xy
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_height = (bbox[3] - bbox[1]) + line_spacing

    for paragraph in paragraphs:
        if not paragraph.strip():
            y += line_height
            continue
            
        if not max_width:
            draw.text((x, y), shape_urdu(paragraph), font=font, fill=fill)
            y += line_height
            continue

        # Wrap text logically within the paragraph bounds
        words = paragraph.split(' ')
        lines = []
        current = ""

        for word in words:
            if not word: continue
            candidate = f"{current} {word}".strip()
            # Measure width using reshaped text to ensure accuracy
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
    
    width_group = (
        MAX_WIDTHS["DailyPlan"]
        if template_type == "Daily Lesson Plan"
        else MAX_WIDTHS["WeeklyPlan"]
    )

    admin_font = load_font(28)
    content_font = load_font(27)

    admin_fields = (
        ["TeacherName", "Topic", "LessonNo", "SubjectTitleCode", "Technology", "Year"]
        if template_type == "Daily Lesson Plan"
        else ["AcademicSession", "TechTradeCourse", "Subject", "Duration", "WeekNo", "PreparedBy"]
    )

    for field in admin_fields:
        if field in coordinate_group and field in data:
            draw_rtl_text(draw, coordinate_group[field], data[field], admin_font, max_width=400)

    ai_fields = (
        ["SpecificObjectives", "Introduction", "Presentation", "TeachingAids", 
         "LessonContents", "KeyPoints", "TimeAllocation", "ActivityFeedback", "Assignment"]
        if template_type == "Daily Lesson Plan"
        else ["TopicsWeeklyPlanner"]
    )

    for field in ai_fields:
        if field in coordinate_group and field in data:
            value = data[field]

            if isinstance(value, (dict, list)):
                value = _structured_value_to_text(value)

            # Use the specific max_width for this exact field so tables don't overlap!
            field_max_width = width_group.get(field, 900)

            draw_rtl_text(draw, coordinate_group[field], value, content_font, max_width=field_max_width)

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _structured_value_to_text(value: Any) -> str:
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if isinstance(item, list):
                item_str = "\n".join(f"• {i}" for i in item)
                parts.append(f"{item_str}")
            else:
                parts.append(f"{item}")
        return "\n\n".join(parts)

    if isinstance(value, list):
        return "\n".join(f"• {item}" for item in value)

    return str(value)
