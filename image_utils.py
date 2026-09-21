from io import BytesIO
from pathlib import Path
from typing import Any
import urllib.request

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
FONTS_DIR = BASE_DIR / "fonts"

# --- Exact Coordinates & Limits for daily_plan_empty_2.jpeg ---
COORDINATES = {
    "DailyPlan": {
        # Administrative Fields (Shifted Down & Right)
        "Topic": (320, 270),
        "LessonNo": (250, 295),
        "TeacherName": (420, 330),
        "SubjectTitleCode": (420, 370),
        "Technology": (320, 410),
        "Year": (700, 410),

        # AI Generated Sections (Shifted Down)
        "SpecificObjectives": (150, 480),
        "Introduction": (150, 550),
        "Presentation": (150, 620),
        "TeachingAids": (150, 690),

        # 3-Column Table (Shifted deep down into the boxes)
        "LessonContents": (150, 780),
        "KeyPoints": (450, 780),
        "TimeAllocation": (800, 780),

        # Bottom Sections
        "ActivityFeedback": (150, 1150),
        "Assignment": (150, 1220),
    },

    "WeeklyPlan": {
        "AcademicSession": (300, 300),
        "TechTradeCourse": (300, 350),
        "Subject": (300, 400),
        "Duration": (750, 300),
        "WeekNo": (750, 350),
        "PreparedBy": (750, 400),
        "TopicsWeeklyPlanner": (120, 550),
    },
}

MAX_WIDTHS = {
    "DailyPlan": {
        "Topic": 450,
        "LessonNo": 200,
        "TeacherName": 400,
        "SubjectTitleCode": 400,
        "Technology": 250,
        "Year": 150,

        "SpecificObjectives": 850,
        "Introduction": 850,
        "Presentation": 850,
        "TeachingAids": 850,

        "LessonContents": 280,   # Stays rigidly in the left box
        "KeyPoints": 320,        # Stays rigidly in the middle box
        "TimeAllocation": 100,   # Stays rigidly in the right box

        "ActivityFeedback": 850,
        "Assignment": 850,
    },
    "WeeklyPlan": {
        "TopicsWeeklyPlanner": 850,
    }
}


def find_font() -> Path:
    """Finds or automatically downloads NotoNaskhArabic for clean PIL rendering."""
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    noto_font = FONTS_DIR / "NotoNaskhArabic-Regular.ttf"
    
    if not noto_font.exists():
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/notonaskharabic/NotoNaskhArabic%5Bwght%5D.ttf"
            urllib.request.urlretrieve(url, noto_font)
        except Exception:
            pass

    candidates = [
        noto_font,
        FONTS_DIR / "NotoNaskhArabic-Regular.ttf",
        FONTS_DIR / "JameelNooriNastaleeq.ttf",
    ]

    for font_path in candidates:
        if font_path.exists():
            return font_path

    raise FileNotFoundError("No valid Urdu font found.")


def load_font(size: int = 20) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(find_font()), size)


def shape_urdu(text: Any) -> str:
    """Reshapes Urdu and locks direction strictly to Right-To-Left."""
    text = "" if text is None else str(text)
    if not text.strip():
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped, base_dir="R")


def draw_rtl_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: Any,
    font: ImageFont.FreeTypeFont,
    fill: str = "black",
    max_width: int | None = None,
    line_spacing: int = 4,
):
    """Draws RTL text preserving newlines and preventing overlap."""
    text = "" if text is None else str(text)
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

        words = paragraph.split(' ')
        lines = []
        current = ""

        for word in words:
            if not word: continue
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

    coordinate_group = COORDINATES["DailyPlan"] if template_type == "Daily Lesson Plan" else COORDINATES["WeeklyPlan"]
    width_group = MAX_WIDTHS["DailyPlan"] if template_type == "Daily Lesson Plan" else MAX_WIDTHS["WeeklyPlan"]

    admin_font = load_font(19)
    content_font = load_font(17)

    admin_fields = (
        ["TeacherName", "Topic", "LessonNo", "SubjectTitleCode", "Technology", "Year"]
        if template_type == "Daily Lesson Plan"
        else ["AcademicSession", "TechTradeCourse", "Subject", "Duration", "WeekNo", "PreparedBy"]
    )

    for field in admin_fields:
        if field in coordinate_group and field in data:
            draw_rtl_text(draw, coordinate_group[field], data[field], admin_font, max_width=width_group.get(field, 400))

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

            draw_rtl_text(draw, coordinate_group[field], value, content_font, max_width=width_group.get(field, 700))

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _structured_value_to_text(value: Any) -> str:
    if isinstance(value, dict):
        parts = [f"{item}" for key, item in value.items()]
        return "\n".join(parts)
    if isinstance(value, list):
        return "\n".join(f"{item}" for item in value)
    return str(value)
