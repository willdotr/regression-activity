"""Persona 3 colors: Dark Hour navy, electric cyan and blue, hot pink. Colors and panel styling only (fonts untouched).

To revert: `git checkout -- .` then delete this file (the previous look is the last commit).
"""

import streamlit as st

CYAN, PINK, BLUE, INK, LINE, DIM = "#00e5ff", "#ff4d7a", "#3d6bff", "#e8f6ff", "#7f93b8", "#2c3b6b"

CSS = """
.stApp {
  background-color: #031433;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 120' preserveAspectRatio='none'%3E%3Cpath d='M0 60 C150 10 300 110 450 60 S750 10 900 60 S1100 100 1200 60 V120 H0Z' fill='%2300e5ff' fill-opacity='0.10'/%3E%3C/svg%3E"),
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 120' preserveAspectRatio='none'%3E%3Cpath d='M0 70 C200 110 350 20 600 70 S1000 110 1200 70 V120 H0Z' fill='%233d6bff' fill-opacity='0.18'/%3E%3C/svg%3E"),
    linear-gradient(180deg, #0b7aa8 0%, #0a4f8a 28%, #062a63 62%, #031433 100%);
  background-repeat: repeat-x, repeat-x, no-repeat;
  background-position: 0 100%, 0 100%, 0 0;
  background-size: 1200px 130px, 1700px 150px, 100% 100%;
  background-attachment: fixed;
  animation: tide 24s linear infinite;
}
/* the waves slide in opposite directions and bob a little; each shift is a whole tile so the loop is seamless */
@keyframes tide {
  0%   { background-position: 0 100%, 0 100%, 0 0; }
  50%  { background-position: 600px calc(100% + 10px), -850px calc(100% - 10px), 0 0; }
  100% { background-position: 1200px 100%, -1700px 100%, 0 0; }
}
/* light rays drifting from the surface */
.stApp::before {
  content: ""; position: fixed; inset: -10% -20% 40% -20%; pointer-events: none; z-index: 0;
  background: repeating-linear-gradient(105deg, rgba(255,255,255,.05) 0 40px, transparent 40px 130px);
  -webkit-mask-image: linear-gradient(180deg, #000, transparent); mask-image: linear-gradient(180deg, #000, transparent);
  animation: sway 16s ease-in-out infinite alternate;
}
@keyframes sway { from { transform: translateX(-60px); } to { transform: translateX(60px); } }
@media (prefers-reduced-motion: reduce) { .stApp, .stApp::before { animation: none; } }
[data-testid="stHeader"] { background: transparent; }

h1 { color: #fff; border-bottom: 4px solid #3d6bff; display: inline-block; padding-right: 2rem; }
h2, h3 { color: #fff; }
h4, h5 { color: #00e5ff; }

[data-testid="stSidebar"] { background: linear-gradient(180deg, #02081f, #06154a); border-right: 2px solid #1f3a9a; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: #3d6bff !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] span { color: #fff !important; }

[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] [data-testid="stPageLink"]),
[data-testid="stExpander"], [data-testid="stMetric"], [data-testid="stAlert"] {
  background: rgba(20, 44, 120, .45) !important; border: 1px solid #3d6bff !important; border-radius: 6px !important;
}
[data-testid="stMetric"] { padding: .6rem 1.2rem; }
[data-testid="stMetricValue"] { color: #00e5ff; }

[data-baseweb="tab-highlight"] { background-color: #ff4d7a !important; height: 4px !important; }
[data-testid="stPageLink-NavLink"] { background: #3d6bff; border-radius: 6px; }
[data-testid="stPageLink-NavLink"]:hover { background: #ff4d7a; }
[data-testid="stPageLink-NavLink"] p { color: #fff !important; font-weight: 700; }

code, pre { border-left: 3px solid #ff4d7a !important; border-radius: 4px !important; background: rgba(0,0,0,.45) !important; }
[data-testid="stCaptionContainer"] { color: #7f93b8; }
hr { border-color: #00e5ff55; }
"""


def apply() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
