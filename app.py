import base64
from datetime import datetime
from pathlib import Path
from string import Template
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
    weekday = now.weekday()  # Monday=0 ... Sunday=6

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
# Greeting state
# -----------------------
if "intro_shown" not in st.session_state:
    st.session_state.intro_shown = False

now = datetime.now(ZoneInfo(TIMEZONE))
greeting = get_greeting(now)
show_greeting = not st.session_state.intro_shown
st.session_state.intro_shown = True

greeting_overlay_html = ""
if show_greeting:
    greeting_overlay_html = f"""
    <div class="greeting-overlay">
        <div class="greeting-text">{greeting}</div>
    </div>
    """

greeting_delay = GREETING_FADE_SECONDS if show_greeting else 0

# -----------------------
# Logo
# -----------------------
logo_b64 = get_image_base64(LOGO_PATH)
logo_html = ""
if logo_b64:
    logo_html = f"""
    <div class="hero-logo">
        <img src="data:image/png;base64,{logo_b64}" alt="Logo">
    </div>
    """

# -----------------------
# Streamlit inputs
# -----------------------
airport_options = ["JFK", "LHR", "ATH", "CDG", "FRA", "MXP", "MAD", "BCN"]

left_col, right_col = st.columns([1, 1])

with left_col:
    origin = st.selectbox("Departure Airport", airport_options, index=0)
    search = st.button("Search", use_container_width=False)

with right_col:
    results = []

if search:
    results = get_destinations(origin)

# -----------------------
# Results HTML
# -----------------------
results_html = ""
if search and results:
    cards = []
    for item in results:
        price = item.get("price")
        price_html = f"From €{price}" if price not in [None, ""] else "Price unavailable"

        cards.append(
            f"""
            <div class="destination-card">
                <div class="destination-city">{item.get("city", "Unknown destination")}</div>
                <div class="destination-country">{item.get("country", "—")}</div>
                <div class="destination-price">{price_html}</div>
            </div>
            """
        )

    results_html = f"""
    <div class="results-section">
        <div class="results-title">Destinations from {origin}</div>
        <div class="results-grid">
            {''.join(cards)}
        </div>
    </div>
    """
elif search:
    results_html = """
    <div class="results-section">
        <div class="results-title">No destinations found</div>
    </div>
    """

# -----------------------
# Main HTML
# -----------------------
html_template = Template(
    """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
            background: #F7F8FA;
            font-family: 'Inter', Arial, Helvetica, sans-serif;
            color: #2F3345;
        }

        body {
            position: relative;
        }

        .page {
            width: 100%;
            height: 100vh;
            background: #F7F8FA;
            opacity: 0;
            transform: translateY(10px);
            animation: dashboardFadeInUp 0.9s ease forwards;
            animation-delay: ${greeting_delay}s;
            box-sizing: border-box;
            padding: 28px 42px 32px 42px;
            overflow-y: auto;
        }

        .greeting-overlay {
            position: fixed;
            inset: 0;
            width: 100vw;
            height: 100vh;
            background: #F7F8FA;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            pointer-events: none;
            animation: greetingFadeOut 0.5s ease forwards;
            animation-delay: ${greeting_delay}s;
        }

        .greeting-text {
            font-size: 112px;
            font-weight: 800;
            line-height: 1;
            color: #111111;
            text-align: center;
            opacity: 0;
            animation: fadeInOut ${greeting_seconds}s ease-in-out forwards;
            transform-origin: center center;
            padding: 0 30px;
        }

        .hero {
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-top: 8px;
            margin-bottom: 40px;
        }

        .hero-logo {
            text-align: center;
            margin-bottom: 16px;
        }

        .hero-logo img {
            width: 240px;
            max-width: 80%;
            height: auto;
            pointer-events: none;
            user-select: none;
            -webkit-user-drag: none;
        }

        .hero-subtitle {
            font-size: 15px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #6B7280;
        }

        .content {
            display: grid;
            grid-template-columns: 360px 1fr;
            gap: 28px;
            align-items: start;
        }

        .panel {
            background: #FFFFFF;
            border: 1px solid #E5EAF1;
            border-radius: 22px;
            padding: 22px;
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.04);
        }

        .panel-title {
            font-size: 28px;
            font-weight: 800;
            color: #1F2937;
            margin-bottom: 18px;
            line-height: 1.15;
        }

        .panel-subtitle {
            font-size: 14px;
            color: #6B7280;
            margin-bottom: 18px;
            line-height: 1.5;
        }

        .results-section {
            width: 100%;
        }

        .results-title {
            font-size: 28px;
            font-weight: 800;
            color: #1F2937;
            margin-bottom: 18px;
            line-height: 1.15;
        }

        .results-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 16px;
        }

        .destination-card {
            background: #FFFFFF;
            border: 1px solid #E5EAF1;
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.04);
        }

        .destination-city {
            font-size: 22px;
            font-weight: 800;
            color: #1F2937;
            margin-bottom: 8px;
        }

        .destination-country {
            font-size: 15px;
            font-weight: 600;
            color: #6B7280;
            margin-bottom: 12px;
        }

        .destination-price {
            font-size: 16px;
            font-weight: 700;
            color: #1F5FAE;
        }

        @keyframes fadeInOut {
            0%   { opacity: 0; transform: scale(0.96); }
            20%  { opacity: 1; transform: scale(1); }
            80%  { opacity: 1; transform: scale(1); }
            100% { opacity: 0; transform: scale(1.02); }
        }

        @keyframes greetingFadeOut {
            to {
                opacity: 0;
                visibility: hidden;
            }
        }

        @keyframes dashboardFadeInUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 1200px) {
            .greeting-text {
                font-size: 90px;
            }

            .results-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 900px) {
            html, body {
                overflow: auto;
            }

            .page {
                height: auto;
                min-height: 100vh;
                padding: 20px;
            }

            .content {
                grid-template-columns: 1fr;
            }

            .greeting-text {
                font-size: 64px;
                padding: 0 20px;
            }

            .hero-logo img {
                width: 190px;
            }
        }
    </style>
</head>
<body>
    $greeting_overlay_html

    <div class="page">
        <div class="hero">
            $logo_html
            <div class="hero-subtitle">Flight Explorer</div>
        </div>

        <div class="content">
            <div class="panel">
                <div class="panel-title">✈️ Find destinations</div>
                <div class="panel-subtitle">
                    Select a departure airport on the left side of the Streamlit app and search for available destinations.
                </div>
            </div>

            $results_html
        </div>
    </div>
</body>
</html>
"""
)

html = html_template.substitute(
    greeting_overlay_html=greeting_overlay_html,
    greeting_seconds=GREETING_FADE_SECONDS,
    greeting_delay=greeting_delay,
    logo_html=logo_html,
    results_html=results_html,
)

components.html(html, height=900, scrolling=True)