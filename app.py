import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st

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
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }

    .greeting-screen {
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #F7F8FA;
    }

    .greeting-text {
        font-size: 112px;
        font-weight: 800;
        line-height: 1;
        color: #111111;
        text-align: center;
        animation: fadeInOut 4s ease-in-out forwards;
        padding: 0 30px;
    }

    @keyframes fadeInOut {
        0%   { opacity: 0; transform: scale(0.96); }
        20%  { opacity: 1; transform: scale(1); }
        80%  { opacity: 1; transform: scale(1); }
        100% { opacity: 0; transform: scale(1.02); }
    }

    .hero-wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 28px;
        margin-bottom: 42px;
    }

    .hero-subtitle {
        font-size: 15px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #6B7280;
        text-align: center;
        margin-top: 10px;
    }

    .section-title {
        font-size: 34px;
        font-weight: 800;
        color: #1F2937;
        margin-bottom: 10px;
        line-height: 1.1;
    }

    .section-subtitle {
        font-size: 16px;
        color: #6B7280;
        margin-bottom: 18px;
        line-height: 1.5;
        max-width: 520px;
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

    @media (max-width: 900px) {
        .greeting-text {
            font-size: 64px;
            padding: 0 20px;
        }

        .section-title {
            font-size: 28px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# Config
# -----------------------
TIMEZONE = "Europe/Athens"
GREETING_SECONDS = 4
API_KEY = st.secrets.get("SERPAPI_KEY", "")

# -----------------------
# Greeting logic
# -----------------------
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


# -----------------------
# API
# -----------------------
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
            results.append(
                {
                    "city": d.get("city") or d.get("title") or "Unknown destination",
                    "country": d.get("country") or "—",
                    "price": d.get("price"),
                }
            )
        return results
    except Exception:
        return []


# -----------------------
# Intro state
# -----------------------
if "intro_shown" not in st.session_state:
    st.session_state.intro_shown = False

now = datetime.now(ZoneInfo(TIMEZONE))

if not st.session_state.intro_shown:
    st.markdown(
        f"""
        <div class="greeting-screen">
            <div class="greeting-text">{get_greeting(now)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    time.sleep(GREETING_SECONDS)
    st.session_state.intro_shown = True
    st.rerun()

# -----------------------
# Main dashboard
# -----------------------
st.markdown('<div class="hero-wrap">', unsafe_allow_html=True)
st.image("sig_logo.png", width=240)
st.markdown('<div class="hero-subtitle">Flight Explorer</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

left, right = st.columns([1, 1.7], gap="large")

with left:
    st.markdown('<div class="section-title">✈️ Find destinations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Select a departure airport and search for available destinations.</div>',
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
                f'<div class="section-title" style="font-size:30px;">Destinations from {origin}</div>',
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