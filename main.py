import streamlit as st
from plantuml import PlantUML

from pipeline import pipeline

puml_public = PlantUML(url='http://www.plantuml.com/plantuml/svg/')

st.set_page_config(layout="wide")
st.title("Domain Storytelling")

st.subheader("Input")
with st.form("story_form"):
    story_text = st.text_area("What is your story?", height=300) or ""
    submitted = st.form_submit_button("Generate Story", use_container_width=True)

st.subheader("Result")
result_placeholder = st.empty()

if submitted:
    result_placeholder.empty()

    if not story_text.strip():
        result_placeholder.warning("Please enter a story first.")
    else:
        with st.spinner("Generating..."):
            try:
                result = pipeline(content=story_text)
                image_url = puml_public.get_url(result)
                result_placeholder.image(image_url, use_container_width=True)
            except Exception as e:
                result_placeholder.error(f"Generation failed: {e}")
