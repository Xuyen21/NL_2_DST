import streamlit as st
import requests
from plantuml import PlantUML

from pipeline import pipeline
from prompt_strategy.extraction_rules import SYSTEM_PROMPT
from text_to_json.schema_design import DomainStory


puml_public = PlantUML(url='http://www.plantuml.com/plantuml/svg/')

st.set_page_config(layout="wide")
st.title("Domain Storytelling")

left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.subheader("Input")
    with st.form("story_form"):
        story_text = st.text_area("What is your story?", height=300)
        submitted = st.form_submit_button("Generate Story", use_container_width=True)

with right_col:
    st.subheader("Result")
    result_placeholder = st.empty()

    if submitted:
        # Clear anything previously shown in the result area
        result_placeholder.empty()

        if not story_text.strip():
            result_placeholder.warning("Please enter a story first.")
        else:
            with st.spinner("Generating..."):
                result = pipeline(
                    response_model=DomainStory,
                    prompt=SYSTEM_PROMPT,
                    content=story_text
                )
                image_url = puml_public.get_url(result)
                result_placeholder.image(image_url, use_container_width=True)