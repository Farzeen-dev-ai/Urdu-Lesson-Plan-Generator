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
        "Topic": (270, 333),
        "LessonNo": (270, 365),
        "TeacherName": (372, 393),
        "SubjectTitleCode": (375, 425),
        "Technology": (273, 450),
        "Year": (725, 453),

        # AI Generated Sections (Shifted Down)
        "SpecificObjectives": (150, 537),
        "Introduction": (150, 598),
        "Presentation": (150, 661),
        "TeachingAids": (150, 725),

        # 3-Column Table
        "LessonContents": (130, 830),
        "KeyPoints": (405, 830),
        "TimeAllocation": (915, 830),

        # Bottom Sections
        "ActivityFeedback": (140, 1105),
        "Assignment": (140, 1163),

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
        "Topic": 690,
        "LessonNo": 300,
        "TeacherName": 720,
        "SubjectTitleCode": 710,
        "Technology": 430,
        "Year": 250,

        "SpecificObjectives": 820,
        "Introduction": 820,
        "Presentation": 820,
        "TeachingAids": 820,

        # 3-Column Table
        "LessonContents": 278,
        "KeyPoints": 510,
        "TimeAllocation": 130,

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
    align_right: bool = False,
):
    """Draws RTL Urdu text with optional right alignment."""

    text = "" if text is None else str(text)
    paragraphs = text.split('\n')

    x, baseline_y = xy

    bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_height = (bbox[3] - bbox[1]) + line_spacing

    current_y = baseline_y

    for paragraph in paragraphs:
        if not paragraph.strip():
            current_y += line_height
            continue

        words = paragraph.split(' ')
        lines = []
        current = ""

        for word in words:
            if not word:
                continue

            candidate = f"{current} {word}".strip()
            display_candidate = shape_urdu(candidate)

            bbox = draw.textbbox(
                (0, 0),
                display_candidate,
                font=font
            )

            width = bbox[2] - bbox[0]

            if current and max_width and width > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate

        if current:
            lines.append(current)

        for line in lines:
            rendered = shape_urdu(line)

            if align_right and max_width:
                draw_x = x + max_width
                anchor = "rs"
            else:
                draw_x = x
                anchor = "ls"

            draw.text(
                (draw_x, current_y),
                rendered,
                font=font,
                fill=fill,
                anchor=anchor
            )

            current_y += line_height


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
            draw_rtl_text(
                draw,
                coordinate_group[field],
                data[field],
                admin_font,
                max_width=width_group.get(field, 400),
            )

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

            draw_rtl_text(
                draw,
                coordinate_group[field],
                value,
                content_font,
                max_width=width_group.get(field, 700),
                align_right=True
            )

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _structured_value_to_text(value: Any) -> str:
    if isinstance(value, dict):
        parts = []

        for item in value.values():
            parts.append(_structured_value_to_text(item))

        return "\n".join(part for part in parts if part.strip())

    if isinstance(value, list):
        parts = []

        for item in value:
            parts.append(_structured_value_to_text(item))

        return "\n".join(part for part in parts if part.strip())

    return str(value)
