import base64
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Flight Explorer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    footer {visibility: hidden;}
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    .main-wrap {
        min-height: 100vh;
        background: #F7F8FA;
        padding: 24px 42px 40px 42px;
    }

    .hero-wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 18px;
        margin-bottom: 46px;
    }

    .hero-logo img {
        width: 240px;
        max-width: 80%;
        height: auto;
        display: block;
        margin: 0 auto;
    }

    .hero-subtitle {
        margin-top: 14px;
        font-size: 15px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #6B7280;
        text-align: center;
    }

    .search-title {
        font-size: 34px;
        font-weight: 800;
        color: #1F2937;
        margin-bottom: 10px;
        line-height: 1.1;
    }

    .search-subtitle {
        font-size: 16px;
        color: #6B7280;
        margin-bottom: 18px;
        max-width: 560px;
        line-height: 1.5;
    }

    .result-card {
        background: #FFFFFF;
        border: 1px solid #E5EAF1;
        border-radius: 20px;
        padding: 18px;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.04);
        margin-bottom: 14px;
    }

    .result-city {
        font-size: 22px;
        font-weight: 800;
        color: #1F2937;
        margin-bottom: 8px;
    }

    .result-country {
        font-size: 15px;
        font-weight: 600;
        color: #6B7280;
        margin-bottom: 10px;
    }

    .result-price {
        font-size: 16px;
        font-weight: 700;
        color: #1F5FAE;
    }

    div[data-testid="stSelectbox"] label {
        font-weight: 600;
    }

    div[data-testid="stButton"] button {
        border-radius: 12px;
        padding: 0.55rem 1.1rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# Config
# -----------------------
TIMEZONE = "Europe/Athens"
LOGO_PATH = "sig_logo.png"
GREETING_FADE_SECONDS = 4
API_KEY = st.secrets.get("SERPAPI_KEY", "")

# -----------------------
# Helpers
# -----------------------
def get_image_base64(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return base64.b64encode(file_path.read_bytes()).decode()

def get_greeting(now: datetime) -> str:
    hour = now.hour
    weekday = now.weekday()

    weekday_messages = [
        ((0, 6), "Τι έγινε, έχουμε αϋπνίες?"),
        ((6, 8), "Νωρίς σήμερα..."),
        ((8, 12), "Καλημέρα!"),
        ((12, 16), "Καλησπέρα!"),
        ((16, 17), "Ετοίμαζε πράγματα σιγά σιγά..."),
        ((17, 20), "Ακόμα εδώ???"),
        ((20, 24), "Το έκαψες..."),
    ]

    saturday_messages = [
        ((0, 6), "Σάββατο ξημερώματα και είσαι εδώ;"),
        ((6, 8), "Σάββατο και τόσο νωρίς;"),
        ((8, 12), "Καλημέρα... για Σάββατο πάντα"),
        ((12, 16), "Σάββατο μεσημέρι, τι φάση;"),
        ((16, 17), "Άντε, μάζευε πράγματα σιγά σιγά..."),
        ((17, 20), "Σάββατο απόγευμα και ακόμα εδώ???"),
        ((20, 24), "Οκ, το παράκανες σήμερα..."),
    ]

    sunday_messages = [
        ((0, 6), "Κυριακή ξημερώματα... όλα καλά;"),
        ((6, 8), "Κυριακή και ξύπνησες από τώρα;"),
        ((8, 12), "Καλημέρα... όσο καλή μπορεί να είναι..."),
        ((12, 16), "Κυριακή μεσημέρι, αύριο πάλι απ’ την αρχή"),
        ((16, 17), "Σιγά σιγά τελειώνει το παραμύθι..."),
        ((17, 20), "Κυριακή απόγευμα και ακόμα εδώ???"),
        ((20, 24), "Αύριο δουλειά. Τα κεφάλια μέσα."),
    ]

    if weekday == 5:
        messages = saturday_messages
    elif weekday == 6:
        messages = sunday_messages
    else:
        messages = weekday_messages

    for (start_hour, end_hour), message in messages:
        if start_hour <= hour < end_hour:
            return message

    return "Καλημέρα!"

@st.cache_data(ttl=86400, show_spinner=False)
def get_destinations(origin: str) -> list[dict]:
    if not API_KEY:
        return []

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_travel_explore",
        "departure_id": origin,
        "api_key": API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        results = []
        for d in data.get("destinations", []):
            results.append({
                "city": d.get("city") or d.get("title") or "Unknown destination",
                "country": d.get("country") or "—",
                "price": d.get("price"),
            })
        return results
    except Exception:
        return []

# -----------------------
# Greeting overlay
# -----------------------
if "intro_shown" not in st.session_state:
    st.session_state.intro_shown = False

now = datetime.now(ZoneInfo(TIMEZONE))
greeting = get_greeting(now)
show_greeting = not st.session_state.intro_shown
st.session_state.intro_shown = True

if show_greeting:
    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                html, body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                }}

                .greeting-overlay {{
                    position: fixed;
                    inset: 0;
                    width: 100vw;
                    height: 100vh;
                    background: #F7F8FA;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 999999;
                    pointer-events: none;
                    animation: greetingFadeOut 0.5s ease forwards;
                    animation-delay: {GREETING_FADE_SECONDS}s;
                }}

                .greeting-text {{
                    font-family: Inter, Arial, sans-serif;
                    font-size: 112px;
                    font-weight: 800;
                    line-height: 1;
                    color: #111111;
                    text-align: center;
                    opacity: 0;
                    animation: fadeInOut {GREETING_FADE_SECONDS}s ease-in-out forwards;
                    transform-origin: center center;
                    padding: 0 30px;
                }}

                @keyframes fadeInOut {{
                    0%   {{ opacity: 0; transform: scale(0.96); }}
                    20%  {{ opacity: 1; transform: scale(1); }}
                    80%  {{ opacity: 1; transform: scale(1); }}
                    100% {{ opacity: 0; transform: scale(1.02); }}
                }}

                @keyframes greetingFadeOut {{
                    to {{
                        opacity: 0;
                        visibility: hidden;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="greeting-overlay">
                <div class="greeting-text">{greeting}</div>
            </div>
        </body>
        </html>
        """,
        height=0,
        scrolling=False,
    )

# -----------------------
# Main page
# -----------------------
logo_b64 = get_image_base64(LOGO_PATH)

st.markdown('<div class="main-wrap">', unsafe_allow_html=True)

if logo_b64:
    st.markdown(
        f"""
        <div class="hero-wrap">
            <div class="hero-logo">
                <img src="data:image/png;base64,{logo_b64}" alt="Logo">
            </div>
            <div class="hero-subtitle">Flight Explorer</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

left, right = st.columns([1, 1.7], gap="large")

with left:
    st.markdown('<div class="search-title">✈️ Find destinations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="search-subtitle">Select a departure airport and search for available destinations.</div>',
        unsafe_allow_html=True,
    )

    origin = st.selectbox(
        "Departure Airport",
        ["JFK", "LHR", "ATH", "CDG", "FRA", "MXP", "MAD", "BCN"],
        index=0,
    )

    search = st.button("Search")

with right:
    if search:
        with st.spinner("Searching destinations..."):
            results = get_destinations(origin)

        if results:
            st.markdown(
                f'<div class="search-title" style="font-size:30px;">Destinations from {origin}</div>',
                unsafe_allow_html=True,
            )
            for item in results:
                price = item.get("price")
                price_text = f"From €{price}" if price not in [None, ""] else "Price unavailable"

                st.markdown(
                    f"""
                    <div class="result-card">
                        <div class="result-city">{item.get("city", "Unknown destination")}</div>
                        <div class="result-country">{item.get("country", "—")}</div>
                        <div class="result-price">{price_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No destinations found.")

st.markdown("</div>", unsafe_allow_html=True)