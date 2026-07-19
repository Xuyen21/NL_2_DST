import streamlit as st

APP_STYLES = """
<style>
    .main {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    .pane-section {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 1.25rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }

    .pane-splitter {
        height: 1px;
        margin: 1.25rem 0;
        background: linear-gradient(90deg, rgba(124, 58, 237, 0), rgba(124, 58, 237, 0.45), rgba(79, 70, 229, 0));
    }

    .block-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
        color: #222;
    }

    .section-spacer {
        margin: 1.5rem 0;
    }

    div[data-testid="stTextArea"] textarea {
        border-radius: 14px;
        border: 1px solid #d9d9e3;
        padding: 1rem;
        background: #ffffff;
    }

    div.stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        width: 100%;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        font-weight: 600;
        border: none;
        background: linear-gradient(90deg, #4f46e5, #7c3aed);
        color: white;
        transition: 0.2s ease-in-out;
    }

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(79, 70, 229, 0.25);
    }

    .placeholder-box {
        min-height: 330px;
        border: 2px dashed #cfcfcf;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #888;
        font-size: 1rem;
        background: #fafafa;
        margin-top: 0.5rem;
        padding: 1rem;
        text-align: center;
    }
</style>
"""


def apply_styles() -> None:
    st.markdown(APP_STYLES, unsafe_allow_html=True)

