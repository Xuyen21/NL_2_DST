import streamlit as st

st.set_page_config(page_title="Text to Picture", layout="wide")

# ---------- Custom CSS ----------
st.markdown(
    """
    <style>
        .main {
            padding-top: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        .block-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.6rem;
            color: #222;
        }

        .left-card, .right-card {
            background: #ffffff;
            padding: 1.2rem;
            border-radius: 18px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
            border: 1px solid #eaeaea;
        }

        .right-card {
            min-height: 420px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }

        div.stButton > button {
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

        div.stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 14px rgba(79, 70, 229, 0.25);
        }

        .placeholder-box {
            height: 330px;
            border: 2px dashed #cfcfcf;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #888;
            font-size: 1rem;
            background: #fafafa;
            margin-top: 0.5rem;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# ---------- Title ----------
st.title("Easy Domain Storytelling ")

# ---------- Layout ----------
col1, col2 = st.columns([1, 1.15], gap="large")

with col1:
    # st.markdown('<div class="left-card">', unsafe_allow_html=True)
    st.markdown('<div class="block-title">Tell me about your domain story 🙂</div>', unsafe_allow_html=True)

    input_text = st.text_area(
        label="", placeholder="My story is ...", height=260
    )

    generate_clicked = st.button("Generate -->")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="right-card">', unsafe_allow_html=True)
    st.markdown('<div class="block-title">Picture Output</div>', unsafe_allow_html=True)

    if generate_clicked:
        # Replace this with your real image generation result
        st.image(
            "https://via.placeholder.com/800x500.png?text=Generated+Picture",
            caption="Generated Picture",
            use_container_width=True,
        )
    else:
        st.markdown(
            '<div class="placeholder-box">Your generated picture will appear here</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


