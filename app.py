import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Flight Explorer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------
# Dark mode toggle
# -----------------------
dark_mode = st.toggle("🌙 Dark mode", value=False)

bg = "#0B1220" if dark_mode else "#F6F7FB"
text = "#E5E7EB" if dark_mode else "#162033"
card_bg = "#111827" if dark_mode else "#FFFFFF"
border = "#1F2937" if dark_mode else "#E6EAF2"
muted = "#9CA3AF" if dark_mode else "#667085"
accent = "#60A5FA" if dark_mode else "#1F5FAE"

# -----------------------
# CSS
# -----------------------
st.markdown(
    f"""
    <style>
    body {{
        background-color: {bg};
        color: {text};
    }}

    .block-container {{
        background-color: {bg};
    }}

    .stApp {{
        background-color: {bg};
        color: {text};
    }}

    .destination-card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 20px;
        padding: 18px;
    }}

    .destination-city {{
        font-size: 22px;
        font-weight: 800;
        color: {text};
    }}

    .destination-code {{
        font-size: 12px;
        font-weight: 700;
        color: {accent};
    }}

    .destination-country {{
        font-size: 14px;
        color: {muted};
    }}

    .destination-fare {{
        font-size: 15px;
        font-weight: 800;
        color: {accent};
    }}

    .destination-fare.muted {{
        color: {muted};
    }}

    label {{
        color: {text} !important;
    }}

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
# Greeting
# -----------------------
def get_greeting(now):
    hour = now.hour
    if hour < 12:
        return "Καλημέρα!"
    elif hour < 18:
        return "Καλησπέρα!"
    else:
        return "Ακόμα εδώ???"

# -----------------------
# API
# -----------------------
def extract_dest_code(item):
    airport = item.get("destination_airport", {})
    return airport.get("code", "") if isinstance(airport, dict) else ""

@st.cache_data(ttl=86400)
def get_destinations(origin):
    if not API_KEY:
        return []

    params = {
        "engine": "google_travel_explore",
        "departure_id": origin,
        "currency": "EUR",
        "api_key": API_KEY,
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params)
        data = response.json()

        results = []
        for d in data.get("destinations", []):
            results.append({
                "city": d.get("name"),
                "airport_code": extract_dest_code(d),
                "country": d.get("country"),
                "price": d.get("flight_price"),
            })
        return results
    except:
        return []

# -----------------------
# Intro
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
# HERO (centered)
# -----------------------
_, center, _ = st.columns([1, 2, 1])

with center:
    _, logo_col, _ = st.columns([1, 2, 1])
    with logo_col:
        st.image("sig_logo.png", width=300)

    st.markdown('<div class="hero-title">Flight Explorer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Select a departure airport to explore available destinations.</div>',
        unsafe_allow_html=True,
    )

# -----------------------
# SEARCH
# -----------------------
_, center, _ = st.columns([1,2,1])

with center:
    st.markdown('<div class="search-heading">✈️ Find destinations</div>', unsafe_allow_html=True)

    origin = st.selectbox(
        "Departure Airport",
        ["JFK", "LAX", "EWR", "MIA", "YYZ"],
    )

    search = st.button("Search")

# -----------------------
# RESULTS
# -----------------------
if search:
    results = get_destinations(origin)

    st.markdown(
        f'<div class="results-header">Destinations from {origin}</div>',
        unsafe_allow_html=True,
    )

    if results:
        # Download button
        df = pd.DataFrame(results)

        st.download_button(
            label="📥 Download to Excel",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"destinations_{origin}.csv",
            mime="text/csv",
        )

        cards_html = []
        for item in results:
            city = item.get("city") or "Unknown destination"
            country = item.get("country") or "—"
            code = item.get("airport_code")
            price = item.get("price")

            fare = f"From €{price}" if price else "Fare unavailable"
            fare_class = "destination-fare" if price else "destination-fare muted"

            cards_html.append(
                f'<div class="destination-card">'
                f'<div class="destination-city">{city}</div>'
                f'<div class="destination-code">{code}</div>'
                f'<div class="destination-country">{country}</div>'
                f'<div class="{fare_class}">{fare}</div>'
                f'</div>'
            )

        st.markdown(
            f'<div class="card-grid">{"".join(cards_html)}</div>',
            unsafe_allow_html=True,
        )

    else:
        st.info("No destinations found.")