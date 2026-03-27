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
        max-width: 100% !important;
        padding-top: 0 !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    .greeting-screen {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #F6F7FB;
    }

    .greeting-text {
        font-size: 112px;
        font-weight: 800;
        line-height: 1;
        color: #111111;
        text-align: center;
        animation: fadeInOut 4s ease-in-out forwards;
        padding: 0 30px;
        letter-spacing: -0.03em;
    }

    @keyframes fadeInOut {
        0%   { opacity: 0; transform: scale(0.96); }
        20%  { opacity: 1; transform: scale(1); }
        80%  { opacity: 1; transform: scale(1); }
        100% { opacity: 0; transform: scale(1.02); }
    }

    .hero-title {
        margin-top: 12px;
        font-size: 16px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #667085;
        text-align: center;
    }

    .hero-subtitle {
        margin-top: 10px;
        margin-bottom: 30px;
        font-size: 18px;
        line-height: 1.5;
        color: #667085;
        text-align: center;
    }

    .search-heading {
        font-size: 34px;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.03em;
        color: #162033;
        text-align: center;
        margin-bottom: 8px;
    }

    .search-description {
        font-size: 16px;
        line-height: 1.5;
        color: #667085;
        text-align: center;
        margin-bottom: 20px;
    }

    .results-header {
        font-size: 32px;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.03em;
        color: #162033;
        text-align: center;
        margin-bottom: 20px;
    }

    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 18px;
    }

    .destination-card {
        background: #FFFFFF;
        border: 1px solid #E6EAF2;
        border-radius: 22px;
        padding: 20px 20px 18px 20px;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
    }

    .destination-city {
        font-size: 24px;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.02em;
        color: #162033;
        margin-bottom: 8px;
    }

    .destination-code {
        display: inline-block;
        font-size: 13px;
        font-weight: 800;
        color: #1F5FAE;
        background: #EEF4FF;
        border-radius: 999px;
        padding: 5px 10px;
        margin-bottom: 12px;
        letter-spacing: 0.04em;
    }

    .destination-country {
        font-size: 15px;
        font-weight: 600;
        line-height: 1.4;
        color: #667085;
        margin-bottom: 18px;
    }

    .destination-fare {
        font-size: 16px;
        font-weight: 800;
        color: #1F5FAE;
    }

    .destination-fare.muted {
        color: #98A2B3;
    }

    div[data-testid="stSelectbox"] label {
        font-weight: 700;
        color: #344054;
    }

    div[data-testid="stButton"] button {
        border-radius: 14px;
        padding: 0.72rem 1.7rem;
        font-weight: 700;
        font-size: 15px;
    }

    @media (max-width: 900px) {
        .greeting-text {
            font-size: 64px;
            padding: 0 20px;
        }

        .search-heading,
        .results-header {
            font-size: 28px;
        }

        .hero-subtitle {
            font-size: 16px;
        }

        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

TIMEZONE = "Europe/Athens"
GREETING_SECONDS = 4
API_KEY = st.secrets.get("SERPAPI_KEY", "")


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


def extract_dest_code(item: dict) -> str:
    candidates = [
        item.get("airport_code"),
        item.get("iata_code"),
        item.get("destination_id"),
        item.get("airport"),
        item.get("code"),
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip().upper()
    return ""


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
                    "airport_code": extract_dest_code(d),
                    "country": d.get("country") or "—",
                    "price": d.get("price"),
                }
            )
        return results
    except Exception:
        return []


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

# Centered hero
_, hero_col, _ = st.columns([1.2, 2, 1.2])

with hero_col:
    st.image("sig_logo.png", width=320)
    st.markdown('<div class="hero-title">Flight Explorer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Select a departure airport to explore available destinations.</div>',
        unsafe_allow_html=True,
    )

# Centered search area
_, search_col, _ = st.columns([1.2, 2, 1.2])

with search_col:
    st.markdown('<div class="search-heading">✈️ Find destinations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="search-description">Choose a starting airport and discover the destinations available from it.</div>',
        unsafe_allow_html=True,
    )

    origin = st.selectbox(
        "Departure Airport",
        ["JFK", "LAX", "EWR", "MIA", "YYZ"],
        index=0,
    )

    btn_left, btn_mid, btn_right = st.columns([1.3, 1, 1.3])
    with btn_mid:
        search = st.button("Search", use_container_width=True)

if search:
    with st.spinner("Searching destinations..."):
        results = get_destinations(origin)

    st.markdown(
        f'<div class="results-header">Destinations from {origin}</div>',
        unsafe_allow_html=True,
    )

    if results:
        cards_html = []
        for item in results:
            city = item.get("city", "Unknown destination")
            country = item.get("country", "—")
            airport_code = item.get("airport_code", "")
            price = item.get("price")

            code_html = f'<div class="destination-code">{airport_code}</div>' if airport_code else ""
            fare_class = "destination-fare" if price not in [None, ""] else "destination-fare muted"
            fare_text = f"From €{price}" if price not in [None, ""] else "Fare unavailable"

            cards_html.append(
                f"""
                <div class="destination-card">
                    <div class="destination-city">{city}</div>
                    {code_html}
                    <div class="destination-country">{country}</div>
                    <div class="{fare_class}">{fare_text}</div>
                </div>
                """
            )

        st.markdown(f'<div class="card-grid">{"".join(cards_html)}</div>', unsafe_allow_html=True)
    else:
        st.info("No destinations found.")