import json
import os
import streamlit as st
from openai import OpenAI

from image_utils import render_lesson_plan

st.set_page_config(
    page_title="Urdu Lesson Plan Generator",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Urdu Lesson Plan Generator")
st.write("Generate a Daily or Weekly lesson plan in standard Urdu and place it onto your form template.")

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="You can also store GROQ_API_KEY in Streamlit Secrets.",
    )
    st.caption("Your API key is used only for the current app session.")

    if not api_key:
        try:
            api_key = st.secrets.get("OPENAI_API_KEY", "")
        except Exception:
            api_key = os.getenv("OPENAI_API_KEY", "")

template_type = st.selectbox(
    "Template Type",
    ["Daily Lesson Plan", "Weekly Lesson Plan"],
)

st.subheader("Administrative Details")

if template_type == "Daily Lesson Plan":
    c1, c2 = st.columns(2)
    with c1:
        topic = st.text_input("Topic")
        lesson_no = st.text_input("Lesson No.")
        teacher_name = st.text_input("Name of the Teacher")
    with c2:
        subject_title_code = st.text_input("Subject Title & Code")
        technology = st.text_input("Technology")
        year = st.text_input("Year")

    user_data = {
        "Topic": topic,
        "LessonNo": lesson_no,
        "TeacherName": teacher_name,
        "SubjectTitleCode": subject_title_code,
        "Technology": technology,
        "Year": year,
    }

else:
    c1, c2 = st.columns(2)
    with c1:
        academic_session = st.text_input("Academic Session")
        tech_trade_course = st.text_input("Tech / Trade / Course")
        subject = st.text_input("Subject")
    with c2:
        duration = st.text_input("Duration")
        week_no = st.text_input("Week No.")
        prepared_by = st.text_input("Prepared By")

    user_data = {
        "AcademicSession": academic_session,
        "TechTradeCourse": tech_trade_course,
        "Subject": subject,
        "Duration": duration,
        "WeekNo": week_no,
        "PreparedBy": prepared_by,
    }

def daily_prompt(data):
    return f"""
You are an expert teacher preparing a formal lesson plan.

Create a detailed lesson plan for the following information:
Topic: {data["Topic"]}
Lesson No.: {data["LessonNo"]}
Teacher: {data["TeacherName"]}
Subject Title & Code: {data["SubjectTitleCode"]}
Technology: {data["Technology"]}
Year: {data["Year"]}

Return ONLY one valid JSON object. Do not use Markdown fences.
The JSON object MUST contain exactly these keys:
SpecificObjectives
Introduction
Presentation
TeachingAids
LessonContents
KeyPoints
TimeAllocation
ActivityFeedback
Assignment

All values must be written strictly in standard, natural Urdu.
Keep the content educational, clear, age-appropriate, and practical.
TimeAllocation should contain realistic time allocations.
"""

def weekly_prompt(data):
    return f"""
You are an expert teacher preparing a formal weekly lesson plan.

Create a detailed day-by-day weekly planner for:
Academic Session: {data["AcademicSession"]}
Tech / Trade / Course: {data["TechTradeCourse"]}
Subject: {data["Subject"]}
Duration: {data["Duration"]}
Week No.: {data["WeekNo"]}
Prepared By: {data["PreparedBy"]}

Return ONLY one valid JSON object. Do not use Markdown fences.
The JSON object MUST contain exactly this key:
TopicsWeeklyPlanner

TopicsWeeklyPlanner should contain a detailed day-by-day breakdown for the week,
including suitable topics, learning activities, and useful teaching information.

All generated content must be strictly in standard, natural Urdu.
"""

if st.button("Generate Plan", type="primary", use_container_width=True):
    missing = [k for k, v in user_data.items() if not str(v).strip()]

    if missing:
        st.error("Please fill in all administrative fields before generating the plan.")
        st.stop()

    if not api_key:
        st.error("Please enter your OpenAI API key or configure OPENAI_API_KEY in Streamlit Secrets.")
        st.stop()

    try:
        # This tells the OpenAI library to route the request to Groq instead
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )

        with st.spinner("Generating Urdu lesson plan..."):
            prompt = daily_prompt(user_data) if template_type == "Daily Lesson Plan" else weekly_prompt(user_data)

            response = client.chat.completions.create(
                model="llama3-70b-8192",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You produce valid JSON and standard Urdu educational content.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
            )

        raw_content = response.choices[0].message.content
        ai_data = json.loads(raw_content)

        required_keys = (
            [
                "SpecificObjectives", "Introduction", "Presentation",
                "TeachingAids", "LessonContents", "KeyPoints",
                "TimeAllocation", "ActivityFeedback", "Assignment"
            ]
            if template_type == "Daily Lesson Plan"
            else ["TopicsWeeklyPlanner"]
        )

        missing_json_keys = [key for key in required_keys if key not in ai_data]
        if missing_json_keys:
            st.error("The AI response did not contain all required fields.")
            st.json(ai_data)
            st.stop()

        merged_data = {**user_data, **ai_data}

        st.subheader("Generated Urdu Content")
        st.json(ai_data)

        with st.spinner("Rendering content onto the form..."):
            output_bytes = render_lesson_plan(template_type, merged_data)

        st.subheader("Finished Lesson Plan")
        st.image(output_bytes, use_container_width=True)

        filename = (
            "daily_lesson_plan.png"
            if template_type == "Daily Lesson Plan"
            else "weekly_lesson_plan.png"
        )

        st.download_button(
            "Download Image",
            data=output_bytes,
            file_name=filename,
            mime="image/png",
            use_container_width=True,
        )

    except json.JSONDecodeError:
        st.error("The AI returned invalid JSON. Please try again.")
    except Exception as exc:
        st.error(f"Generation failed: {exc}")
        st.info("Check your API key, model access, template files, font file, and internet connection.")
