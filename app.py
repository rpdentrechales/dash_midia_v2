import streamlit as st

# --- PAGE SETUP ---
acompanhamento_fb_page = st.Page(
    "views/acompanhamento_fb.py",
    title="Acompanhamento FB",
    icon=":material/summarize:",
)

# testes_page = st.Page(
#     "views/testes.py",
#     title="Testes",
#     icon=":material/summarize:",
# )


# --- NAVIGATION SETUP [WITHOUT SECTIONS] ---
# pg = st.navigation(pages=[about_page, project_1_page, project_2_page])

# --- NAVIGATION SETUP [WITH SECTIONS]---
pg = st.navigation(
    {
        "Acompanhamento": [acompanhamento_fb_page],
    }
)


# --- SHARED ON ALL PAGES ---
# st.logo("assets/codingisfun_logo.png")


# --- RUN NAVIGATION ---
pg.run()
