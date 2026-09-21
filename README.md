# Urdu Lesson Plan Generator

A Streamlit application that uses OpenAI to generate structured lesson-plan content in standard Urdu and renders it onto predefined blank image templates.

## Project structure

```text
lesson-plan-generator/
├── app.py
├── image_utils.py
├── requirements.txt
├── README.md
├── fonts/
│   └── JameelNooriNastaleeq.ttf
└── templates/
    ├── daily_plan_empty.jpeg
    └── weekly_plan_empty.jpeg
```

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Add the Urdu font

Create a `fonts` folder and place an Urdu-capable `.ttf` font inside it.

The code first looks for:

```text
fonts/JameelNooriNastaleeq.ttf
```

You can use another supported Urdu TTF font, but update `find_font()` in `image_utils.py` if its filename is different.

Make sure you have the right to redistribute the font when publishing it in a GitHub repository.

## 3. Add the blank templates

Create a `templates` folder and add:

```text
templates/daily_plan_empty.jpeg
templates/weekly_plan_empty.jpeg
```

The files must be the blank forms with the English headers and empty areas where text should be inserted.

## 4. Configure the OpenAI API key

### Local use

The app asks for the API key in the sidebar.

### Streamlit deployment

A safer approach is to use Streamlit Secrets.

In your Streamlit app settings, add:

```toml
OPENAI_API_KEY = "your-api-key"
```

Do not commit a real API key to GitHub.

## 5. Run locally

```bash
streamlit run app.py
```

## 6. Deploy on Streamlit

Push the project to GitHub, including:

- `app.py`
- `image_utils.py`
- `requirements.txt`
- `README.md`
- `fonts/JameelNooriNastaleeq.ttf` if its license permits redistribution
- `templates/daily_plan_empty.jpeg`
- `templates/weekly_plan_empty.jpeg`

Then create a Streamlit app from the GitHub repository and configure the OpenAI key through Streamlit Secrets.

## 7. Adjust image coordinates

The placeholder coordinates are intentionally editable.

Open `image_utils.py` and edit:

```python
COORDINATES = {
    ...
}
```

Each field has an `(x, y)` coordinate in pixels.

For example:

```python
"TeacherName": (250, 105)
```

Move the values until the generated text aligns with the corresponding blank area in your actual form.

The daily template has coordinates for:

- Teacher Name
- Topic
- Lesson No.
- Subject Title & Code
- Technology
- Year
- Specific Objectives
- Introduction
- Presentation
- Teaching Aids
- Lesson Contents
- Key Points
- Time Allocation
- Activity Feedback
- Assignment

The weekly template has coordinates for:

- Academic Session
- Tech / Trade / Course
- Subject
- Duration
- Week No.
- Prepared By
- Topics Weekly Planner

## Important note about Urdu rendering

Pillow alone does not correctly handle Urdu shaping and right-to-left display in the general case. This project therefore uses:

- `arabic-reshaper`
- `python-bidi`

before drawing Urdu text.

## OpenAI model

The example uses:

```text
gpt-4o
```

through the OpenAI Python package and requests JSON output for predictable field parsing.
