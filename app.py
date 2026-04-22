import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Flight Explorer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TIMEZONE = "Europe/Athens"
GREETING_SECONDS = 4
API_KEY = st.secrets.get("SERPAPI_KEY", "")
SERPAPI_URL = "https://serpapi.com/search.json"
AIRPORTS_FILE = Path("airports.dat")

POPULAR_AIRPORTS = {
    "United States": ["JFK", "EWR", "LAX", "MIA", "ORD", "SFO", "ATL", "BOS", "IAD", "DFW", "SEA"],
    "Canada": ["YYZ", "YUL", "YVR", "YYC", "YOW", "YHZ"],
}

# Main Europe + Istanbul list
EUROPE_DESTINATIONS = [
    # Greece
    {"airport_code": "ATH", "city": "Athens", "country": "Greece"},
    {"airport_code": "SKG", "city": "Thessaloniki", "country": "Greece"},
    {"airport_code": "HER", "city": "Heraklion", "country": "Greece"},
    {"airport_code": "CHQ", "city": "Chania", "country": "Greece"},
    {"airport_code": "RHO", "city": "Rhodes", "country": "Greece"},
    {"airport_code": "CFU", "city": "Corfu", "country": "Greece"},

    # United Kingdom
    {"airport_code": "LHR", "city": "London", "country": "United Kingdom"},
    {"airport_code": "LGW", "city": "London", "country": "United Kingdom"},
    {"airport_code": "STN", "city": "London", "country": "United Kingdom"},
    {"airport_code": "LTN", "city": "London", "country": "United Kingdom"},
    {"airport_code": "MAN", "city": "Manchester", "country": "United Kingdom"},
    {"airport_code": "EDI", "city": "Edinburgh", "country": "United Kingdom"},
    {"airport_code": "GLA", "city": "Glasgow", "country": "United Kingdom"},
    {"airport_code": "BHX", "city": "Birmingham", "country": "United Kingdom"},
    {"airport_code": "BRS", "city": "Bristol", "country": "United Kingdom"},

    # France
    {"airport_code": "CDG", "city": "Paris", "country": "France"},
    {"airport_code": "ORY", "city": "Paris", "country": "France"},
    {"airport_code": "NCE", "city": "Nice", "country": "France"},
    {"airport_code": "LYS", "city": "Lyon", "country": "France"},
    {"airport_code": "MRS", "city": "Marseille", "country": "France"},

    # Germany
    {"airport_code": "FRA", "city": "Frankfurt", "country": "Germany"},
    {"airport_code": "MUC", "city": "Munich", "country": "Germany"},
    {"airport_code": "BER", "city": "Berlin", "country": "Germany"},
    {"airport_code": "DUS", "city": "Dusseldorf", "country": "Germany"},
    {"airport_code": "HAM", "city": "Hamburg", "country": "Germany"},
    {"airport_code": "CGN", "city": "Cologne", "country": "Germany"},

    # Italy
    {"airport_code": "FCO", "city": "Rome", "country": "Italy"},
    {"airport_code": "CIA", "city": "Rome", "country": "Italy"},
    {"airport_code": "MXP", "city": "Milan", "country": "Italy"},
    {"airport_code": "LIN", "city": "Milan", "country": "Italy"},
    {"airport_code": "NAP", "city": "Naples", "country": "Italy"},
    {"airport_code": "VCE", "city": "Venice", "country": "Italy"},
    {"airport_code": "BLQ", "city": "Bologna", "country": "Italy"},
    {"airport_code": "CTA", "city": "Catania", "country": "Italy"},

    # Spain
    {"airport_code": "MAD", "city": "Madrid", "country": "Spain"},
    {"airport_code": "BCN", "city": "Barcelona", "country": "Spain"},
    {"airport_code": "AGP", "city": "Malaga", "country": "Spain"},
    {"airport_code": "PMI", "city": "Palma", "country": "Spain"},
    {"airport_code": "SVQ", "city": "Seville", "country": "Spain"},
    {"airport_code": "VLC", "city": "Valencia", "country": "Spain"},
    {"airport_code": "BIO", "city": "Bilbao", "country": "Spain"},
    {"airport_code": "ALC", "city": "Alicante", "country": "Spain"},

    # Portugal
    {"airport_code": "LIS", "city": "Lisbon", "country": "Portugal"},
    {"airport_code": "OPO", "city": "Porto", "country": "Portugal"},
    {"airport_code": "FAO", "city": "Faro", "country": "Portugal"},
    {"airport_code": "FNC", "city": "Funchal", "country": "Portugal"},

    # Netherlands / Belgium / Switzerland / Austria
    {"airport_code": "AMS", "city": "Amsterdam", "country": "Netherlands"},
    {"airport_code": "EIN", "city": "Eindhoven", "country": "Netherlands"},
    {"airport_code": "BRU", "city": "Brussels", "country": "Belgium"},
    {"airport_code": "CRL", "city": "Brussels", "country": "Belgium"},
    {"airport_code": "ZRH", "city": "Zurich", "country": "Switzerland"},
    {"airport_code": "GVA", "city": "Geneva", "country": "Switzerland"},
    {"airport_code": "BSL", "city": "Basel", "country": "Switzerland"},
    {"airport_code": "VIE", "city": "Vienna", "country": "Austria"},
    {"airport_code": "SZG", "city": "Salzburg", "country": "Austria"},

    # Nordics
    {"airport_code": "CPH", "city": "Copenhagen", "country": "Denmark"},
    {"airport_code": "ARN", "city": "Stockholm", "country": "Sweden"},
    {"airport_code": "GOT", "city": "Gothenburg", "country": "Sweden"},
    {"airport_code": "OSL", "city": "Oslo", "country": "Norway"},
    {"airport_code": "HEL", "city": "Helsinki", "country": "Finland"},
    {"airport_code": "KEF", "city": "Reykjavik", "country": "Iceland"},

    # Central / Eastern Europe
    {"airport_code": "PRG", "city": "Prague", "country": "Czech Republic"},
    {"airport_code": "BUD", "city": "Budapest", "country": "Hungary"},
    {"airport_code": "WAW", "city": "Warsaw", "country": "Poland"},
    {"airport_code": "KRK", "city": "Krakow", "country": "Poland"},
    {"airport_code": "OTP", "city": "Bucharest", "country": "Romania"},
    {"airport_code": "SOF", "city": "Sofia", "country": "Bulgaria"},
    {"airport_code": "BEG", "city": "Belgrade", "country": "Serbia"},
    {"airport_code": "ZAG", "city": "Zagreb", "country": "Croatia"},
    {"airport_code": "DBV", "city": "Dubrovnik", "country": "Croatia"},
    {"airport_code": "SPU", "city": "Split", "country": "Croatia"},
    {"airport_code": "LJU", "city": "Ljubljana", "country": "Slovenia"},
    {"airport_code": "TGD", "city": "Podgorica", "country": "Montenegro"},
    {"airport_code": "TIA", "city": "Tirana", "country": "Albania"},
    {"airport_code": "SKP", "city": "Skopje", "country": "North Macedonia"},
    {"airport_code": "RIX", "city": "Riga", "country": "Latvia"},
    {"airport_code": "VNO", "city": "Vilnius", "country": "Lithuania"},
    {"airport_code": "TLL", "city": "Tallinn", "country": "Estonia"},

    # Ireland / Malta / Cyprus / Luxembourg
    {"airport_code": "DUB", "city": "Dublin", "country": "Ireland"},
    {"airport_code": "ORK", "city": "Cork", "country": "Ireland"},
    {"airport_code": "MLA", "city": "Malta", "country": "Malta"},
    {"airport_code": "LCA", "city": "Larnaca", "country": "Cyprus"},
    {"airport_code": "PFO", "city": "Paphos", "country": "Cyprus"},
    {"airport_code": "LUX", "city": "Luxembourg", "country": "Luxembourg"},

    # Istanbul
    {"airport_code": "IST", "city": "Istanbul", "country": "Turkey"},
    {"airport_code": "SAW", "city": "Istanbul", "country": "Turkey"},
]

# Smaller subset for faster searches
MAJOR_DEST_CODES = {
    "ATH", "SKG",
    "LHR", "LGW", "MAN",
    "CDG", "ORY", "NCE",
    "FRA", "MUC", "BER",
    "FCO", "MXP", "NAP", "VCE",
    "MAD", "BCN", "AGP", "PMI",
    "LIS", "OPO",
    "AMS", "BRU", "ZRH", "GVA", "VIE",
    "CPH", "ARN", "OSL", "HEL",
    "PRG", "BUD", "WAW", "OTP",
    "DUB", "LCA", "MLA",
    "IST", "SAW",
}

SORT_OPTIONS = [
    "Cheapest first",
    "Shortest first",
    "Fewest stops",
    "City A–Z",
]

STOP_OPTIONS = {
    "Any": 0,
    "Direct only": 1,
    "Up to 1 stop": 2,
    "Up to 2 stops": 3,
}

COUNTRY_FLAGS = {
    "Greece": "🇬🇷",
    "United Kingdom": "🇬🇧",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Italy": "🇮🇹",
    "Spain": "🇪🇸",
    "Portugal": "🇵🇹",
    "Netherlands": "🇳🇱",
    "Belgium": "🇧🇪",
    "Switzerland": "🇨🇭",
    "Austria": "🇦🇹",
    "Denmark": "🇩🇰",
    "Sweden": "🇸🇪",
    "Norway": "🇳🇴",
    "Finland": "🇫🇮",
    "Iceland": "🇮🇸",
    "Czech Republic": "🇨🇿",
    "Hungary": "🇭🇺",
    "Poland": "🇵🇱",
    "Romania": "🇷🇴",
    "Bulgaria": "🇧🇬",
    "Serbia": "🇷🇸",
    "Croatia": "🇭🇷",
    "Slovenia": "🇸🇮",
    "Montenegro": "🇲🇪",
    "Albania": "🇦🇱",
    "North Macedonia": "🇲🇰",
    "Latvia": "🇱🇻",
    "Lithuania": "🇱🇹",
    "Estonia": "🇪🇪",
    "Ireland": "🇮🇪",
    "Malta": "🇲🇹",
    "Cyprus": "🇨🇾",
    "Luxembourg": "🇱🇺",
    "Turkey": "🇹🇷",
}


def get_theme_css() -> str:
    return """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet">

    <style>
    /* ── Reset Streamlit chrome ── */
    footer { visibility: hidden; }
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }

    /* ── CSS Variables ── */
    :root {
        --white: #ffffff;
        --off-white: #F8F9FA;
        --surface: #F1F3F4;
        --border: #E0E3E8;
        --border-light: #ECEEF1;
        --text-primary: #202124;
        --text-secondary: #5F6368;
        --text-tertiary: #9AA0A6;
        --accent: #1A73E8;
        --accent-hover: #1557B0;
        --accent-soft: #E8F0FE;
        --green: #137333;
        --green-soft: #E6F4EA;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md: 0 4px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04);
        --shadow-lg: 0 8px 32px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 20px;
        --radius-pill: 999px;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        font-family: 'DM Sans', sans-serif !important;
        background: var(--off-white) !important;
        color: var(--text-primary) !important;
        -webkit-font-smoothing: antialiased;
    }

    .block-container {
        max-width: 1100px !important;
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* ── Greeting screen ── */
    .greeting-screen {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--white);
    }

    .greeting-text {
        font-family: 'DM Serif Display', serif;
        font-size: clamp(56px, 10vw, 112px);
        font-weight: 400;
        line-height: 1;
        color: var(--text-primary);
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

    /* ── Hero ── */
    .hero-eyebrow {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--accent);
        text-align: center;
        margin-bottom: 10px;
    }

    .hero-title {
        font-family: 'DM Serif Display', serif;
        font-size: clamp(36px, 5vw, 52px);
        font-weight: 400;
        line-height: 1.05;
        letter-spacing: -0.02em;
        color: var(--text-primary);
        text-align: center;
        margin-bottom: 12px;
    }

    .hero-title em {
        font-style: italic;
        color: var(--accent);
    }

    .hero-subtitle {
        font-size: 16px;
        line-height: 1.6;
        color: var(--text-secondary);
        text-align: center;
        margin-bottom: 32px;
        font-weight: 400;
    }

    /* ── Search panel card (Streamlit's bordered container) ── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--white) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: 28px 32px 24px !important;
        box-shadow: var(--shadow-md) !important;
        margin-bottom: 8px !important;
    }

    .search-panel-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-tertiary);
        margin-bottom: 20px;
    }

    .controls-note {
        font-size: 12px;
        color: var(--text-tertiary);
        text-align: center;
        margin-top: 12px;
        margin-bottom: 4px;
    }

    /* ── Streamlit widget overrides ── */
    div[data-testid="stSelectbox"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stToggle"] label,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stNumberInput"] label {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: var(--text-tertiary) !important;
    }

    div[data-baseweb="select"] > div {
        background-color: var(--white) !important;
        border-color: var(--border) !important;
        border-radius: var(--radius-md) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: var(--text-primary) !important;
        min-height: 44px !important;
    }

    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(26,115,232,0.12) !important;
    }

    div[data-testid="stDateInput"] input,
    div[data-testid="stNumberInput"] input {
        background-color: var(--white) !important;
        border-color: var(--border) !important;
        border-radius: var(--radius-md) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: var(--text-primary) !important;
        min-height: 44px !important;
    }

    /* Multi-select tags — override Streamlit's default red */
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"],
    div[data-baseweb="tag"],
    [data-baseweb="tag"] {
        background-color: var(--accent-soft) !important;
        border-color: var(--accent-soft) !important;
        border-radius: var(--radius-pill) !important;
    }

    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] span,
    div[data-baseweb="tag"] span,
    [data-baseweb="tag"] span {
        color: var(--accent) !important;
        font-weight: 600 !important;
        font-size: 12px !important;
    }

    /* Tag close (×) button */
    div[data-baseweb="tag"] [role="button"],
    div[data-baseweb="tag"] button {
        color: var(--accent) !important;
        opacity: 0.7;
    }

    /* Expander */
    div[data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        background: var(--white) !important;
        box-shadow: none !important;
    }

    div[data-testid="stExpander"] summary {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
    }

    /* Search / Download buttons */
    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button {
        font-family: 'DM Sans', sans-serif !important;
        border-radius: var(--radius-pill) !important;
        padding: 0 24px !important;
        height: 44px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        background: var(--accent) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: none !important;
        transition: background 0.15s, box-shadow 0.15s !important;
    }

    div[data-testid="stButton"] button:hover,
    div[data-testid="stDownloadButton"] button:hover {
        background: var(--accent-hover) !important;
        box-shadow: 0 2px 8px rgba(26,115,232,0.3) !important;
    }

    div[data-testid="stButton"] button:disabled {
        background: var(--border) !important;
        color: var(--text-tertiary) !important;
    }

    /* Toggle */
    div[data-testid="stToggle"] > label > div[role="switch"] {
        background-color: var(--border) !important;
    }

    div[data-testid="stToggle"] > label > div[aria-checked="true"] {
        background-color: var(--accent) !important;
    }

    /* Spinner */
    div[data-testid="stSpinner"] p {
        font-family: 'DM Sans', sans-serif !important;
        color: var(--text-secondary) !important;
    }

    /* Alerts */
    div[data-testid="stAlert"] {
        border-radius: var(--radius-md) !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    /* ── Results header ── */
    .results-header {
        font-family: 'DM Serif Display', serif;
        font-size: 28px;
        font-weight: 400;
        letter-spacing: -0.02em;
        color: var(--text-primary);
        margin-bottom: 4px;
    }

    .sub-header {
        font-size: 13px;
        color: var(--text-secondary);
        margin-bottom: 20px;
        font-weight: 500;
    }

    /* ── Summary bar ── */
    .summary-bar {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: var(--radius-pill);
        background: var(--green-soft);
        color: var(--green);
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 28px;
    }

    /* ── Country section header ── */
    .country-section {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 32px;
        margin-bottom: 14px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border);
    }

    .country-flag {
        font-size: 20px;
        line-height: 1;
    }

    .country-name {
        font-size: 15px;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.01em;
    }

    .country-count {
        font-size: 12px;
        color: var(--text-tertiary);
        font-weight: 500;
    }

    .country-cheapest {
        margin-left: auto;
        font-size: 12px;
        font-weight: 600;
        color: var(--green);
        background: var(--green-soft);
        padding: 3px 10px;
        border-radius: var(--radius-pill);
    }

    /* ── Card grid ── */
    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 14px;
        margin-bottom: 8px;
    }

    /* ── Destination card ── */
    .dest-card {
        background: var(--white);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-lg);
        padding: 20px;
        display: flex;
        flex-direction: column;
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
    }

    .dest-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
        border-color: var(--accent);
    }

    .card-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 3px;
    }

    .card-city {
        font-size: 20px;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.02em;
        line-height: 1.2;
    }

    .card-code {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        color: var(--accent);
        background: var(--accent-soft);
        padding: 3px 8px;
        border-radius: var(--radius-pill);
        margin-top: 3px;
        white-space: nowrap;
    }

    .card-country {
        font-size: 12px;
        color: var(--text-tertiary);
        font-weight: 500;
        margin-bottom: 14px;
    }

    .card-divider {
        height: 1px;
        background: var(--border-light);
        margin-bottom: 14px;
    }

    .card-badges {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-bottom: 12px;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        height: 24px;
        padding: 0 8px;
        border-radius: var(--radius-pill);
        background: var(--surface);
        color: var(--text-secondary);
        font-size: 11px;
        font-weight: 600;
    }

    .badge-direct {
        background: var(--green-soft);
        color: var(--green);
    }

    .times-row {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 12px;
    }

    .times-line {
        flex: 1;
        height: 1px;
        background: var(--border);
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .times-line::after {
        content: '✈';
        font-size: 10px;
        color: var(--text-tertiary);
        background: var(--white);
        padding: 0 4px;
    }

    .card-meta {
        font-size: 12px;
        color: var(--text-secondary);
        margin-bottom: 4px;
        display: flex;
        gap: 4px;
    }

    .card-meta-label {
        color: var(--text-tertiary);
        font-weight: 500;
        min-width: 50px;
    }

    .card-meta-value {
        font-weight: 500;
    }

    .card-footer {
        margin-top: auto;
        padding-top: 14px;
        border-top: 1px solid var(--border-light);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
    }

    .card-price {
        font-family: 'DM Serif Display', serif;
        font-size: 26px;
        letter-spacing: -0.02em;
        color: var(--text-primary);
        line-height: 1;
    }

    .card-price-label {
        font-size: 11px;
        color: var(--text-tertiary);
        font-weight: 500;
        margin-top: 2px;
    }

    .card-price-unavailable {
        font-size: 14px;
        color: var(--text-tertiary);
        font-weight: 500;
    }

    .book-btn,
    .book-btn:link,
    .book-btn:visited,
    .book-btn:hover,
    .book-btn:active {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        height: 36px;
        padding: 0 16px;
        border-radius: var(--radius-pill);
        background: var(--accent);
        color: #ffffff !important;
        font-family: 'DM Sans', sans-serif;
        font-size: 12px;
        font-weight: 600;
        text-decoration: none !important;
        border: none;
        cursor: pointer;
        white-space: nowrap;
        transition: background 0.15s, box-shadow 0.15s;
    }

    .book-btn:hover {
        background: var(--accent-hover) !important;
        box-shadow: 0 2px 8px rgba(26,115,232,0.25);
    }

    /* ── Responsive ── */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        .greeting-text {
            font-size: 52px;
            padding: 0 16px;
        }

        .hero-title {
            font-size: 32px;
        }

        .card-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """


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
        ((12, 16), "Κυριακή μεσημέρι, αύριο πάλι απ' την αρχή"),
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
def load_departure_airports() -> list[dict]:
    if not AIRPORTS_FILE.exists():
        return []

    airports = []
    with AIRPORTS_FILE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 8:
                continue

            name = row[1].strip()
            city = row[2].strip()
            country = row[3].strip()
            iata = row[4].strip()

            if country not in {"United States", "Canada"}:
                continue

            if not iata or iata == r"\N" or len(iata) != 3:
                continue

            airports.append(
                {
                    "code": iata.upper(),
                    "city": city,
                    "country": country,
                    "name": name,
                    "label": f"{iata.upper()} ({city})",
                }
            )

    unique = {}
    for airport in airports:
        unique[airport["code"]] = airport

    cleaned = list(unique.values())
    cleaned.sort(key=lambda x: (x["country"], x["city"], x["code"]))
    return cleaned


def get_airport_options_for_country(all_airports: list[dict], selected_country: str) -> list[dict]:
    filtered = [a for a in all_airports if a["country"] == selected_country]
    popular_codes = POPULAR_AIRPORTS.get(selected_country, [])

    popular = [a for a in filtered if a["code"] in popular_codes]
    popular.sort(key=lambda x: popular_codes.index(x["code"]))

    others = [a for a in filtered if a["code"] not in popular_codes]
    others.sort(key=lambda x: (x["city"], x["code"]))

    return popular + others


def get_destination_pool(scope: str, allowed_countries: list[str]) -> list[dict]:
    destinations = [d for d in EUROPE_DESTINATIONS if d["country"] in allowed_countries]

    if scope == "Major airports only":
        destinations = [d for d in destinations if d["airport_code"] in MAJOR_DEST_CODES]

    return destinations


def safe_float(value):
    if value in (None, "", "—"):
        return None
    try:
        return float(value)
    except Exception:
        try:
            return float(str(value).replace(",", ""))
        except Exception:
            return None


def format_price(value) -> str:
    amount = safe_float(value)
    if amount is None:
        return "Fare unavailable"
    if amount.is_integer():
        return f"€{int(amount)}"
    return f"€{amount:,.0f}"


def format_duration(minutes) -> str:
    mins = safe_float(minutes)
    if mins is None:
        return "—"
    mins = int(mins)
    hours = mins // 60
    remainder = mins % 60
    return f"{hours}h {remainder}m"


def extract_layover_text(layovers) -> str:
    if not layovers:
        return "Direct"

    parts = []
    for layover in layovers:
        if not isinstance(layover, dict):
            continue
        name = layover.get("name") or layover.get("airport_name") or layover.get("id") or layover.get("code")
        duration = layover.get("duration")
        duration_text = ""
        if duration not in (None, ""):
            duration_text = f" ({format_duration(duration)})"
        if name:
            parts.append(f"{name}{duration_text}")

    return ", ".join(parts) if parts else "Connection"


def build_search_url(origin: str, destination_code: str, outbound_date: str) -> str:
    query = quote_plus(f"Google Flights {origin} to {destination_code} {outbound_date}")
    return f"https://www.google.com/search?q={query}"


def parse_flight_result(data: dict, fallback: dict, origin: str, outbound_date: str) -> dict | None:
    itineraries = []
    itineraries.extend(data.get("best_flights", []))
    itineraries.extend(data.get("other_flights", []))

    valid = []
    for itinerary in itineraries:
        price = safe_float(itinerary.get("price"))
        if price is None:
            continue

        layovers = itinerary.get("layovers", []) or []
        flights = itinerary.get("flights", []) or []

        airline_names = []
        departure_time = None
        arrival_time = None

        for idx, flight in enumerate(flights):
            airline = flight.get("airline")
            if airline and airline not in airline_names:
                airline_names.append(airline)

            if idx == 0:
                departure_time = flight.get("departure_airport", {}).get("time") or flight.get("departure_time")
            if idx == len(flights) - 1:
                arrival_time = flight.get("arrival_airport", {}).get("time") or flight.get("arrival_time")

        valid.append(
            {
                "city": fallback["city"],
                "country": fallback["country"],
                "airport_code": fallback["airport_code"],
                "price": price,
                "stops": len(layovers),
                "airlines": ", ".join(airline_names[:2]) if airline_names else "—",
                "duration_mins": itinerary.get("total_duration"),
                "layover_text": extract_layover_text(layovers),
                "departure_time": departure_time or "—",
                "arrival_time": arrival_time or "—",
                "booking_url": build_search_url(origin, fallback["airport_code"], outbound_date),
            }
        )

    if not valid:
        return None

    valid.sort(key=lambda x: (x["price"], x["stops"], safe_float(x["duration_mins"]) or 999999))
    return valid[0]


@st.cache_data(ttl=21600, show_spinner=False)
def search_destination(origin: str, destination: dict, outbound_date: str, stops_param: int) -> dict | None:
    if not API_KEY:
        return None

    if origin == destination["airport_code"]:
        return None

    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination["airport_code"],
        "outbound_date": outbound_date,
        "type": 2,
        "stops": stops_param,
        "sort_by": 2,
        "hl": "en",
        "gl": "gr",
        "currency": "EUR",
        "api_key": API_KEY,
    }

    try:
        response = requests.get(SERPAPI_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return parse_flight_result(data, destination, origin, outbound_date)
    except Exception:
        return None


def sort_results(results: list[dict], sort_by: str) -> list[dict]:
    if sort_by == "Shortest first":
        return sorted(results, key=lambda x: (safe_float(x["duration_mins"]) or 999999, x["price"], x["city"]))
    if sort_by == "Fewest stops":
        return sorted(results, key=lambda x: (x["stops"], x["price"], safe_float(x["duration_mins"]) or 999999))
    if sort_by == "City A–Z":
        return sorted(results, key=lambda x: (x["country"], x["city"], x["price"]))
    return sorted(results, key=lambda x: (x["price"], x["stops"], safe_float(x["duration_mins"]) or 999999))


def filter_results(results: list[dict], max_price):
    if max_price is None:
        return results
    return [r for r in results if r["price"] <= max_price]


def get_destinations(
    origin: str,
    outbound_date: str,
    destination_pool: list[dict],
    stops_param: int,
    max_price,
    sort_by: str,
    max_workers: int,
) -> list[dict]:
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(search_destination, origin, destination, outbound_date, stops_param)
            for destination in destination_pool
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    results = filter_results(results, max_price)

    # Group by country + city and keep cheapest airport/itinerary
    grouped = {}
    for item in results:
        group_key = (item["country"].strip().lower(), item["city"].strip().lower())
        existing = grouped.get(group_key)
        if existing is None or item["price"] < existing["price"]:
            grouped[group_key] = item

    final_results = list(grouped.values())
    final_results = sort_results(final_results, sort_by)
    return final_results


def group_by_country(results: list[dict]) -> dict[str, list[dict]]:
    grouped = {}
    for item in results:
        grouped.setdefault(item["country"], []).append(item)

    for country in grouped:
        grouped[country] = sort_results(grouped[country], st.session_state.get("sort_by_value", "Cheapest first"))

    ordered_countries = sorted(
        grouped.keys(),
        key=lambda c: min(x["price"] for x in grouped[c]) if grouped[c] else 999999
    )
    return {country: grouped[country] for country in ordered_countries}


def results_to_excel(results: list[dict], origin: str, outbound_date: str) -> bytes:
    rows = []
    for item in results:
        rows.append(
            {
                "Origin": origin,
                "Departure Date": outbound_date,
                "Destination Country": item["country"],
                "Destination City": item["city"],
                "Airport": item["airport_code"],
                "Price EUR": item["price"],
                "Stops": item["stops"],
                "Airlines": item["airlines"],
                "Duration": format_duration(item["duration_mins"]),
                "Departure Time": item["departure_time"],
                "Arrival Time": item["arrival_time"],
                "Layovers": item["layover_text"],
                "Search URL": item["booking_url"],
            }
        )

    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Flights")
    output.seek(0)
    return output.getvalue()


def render_cards(results: list[dict]) -> None:
    grouped = group_by_country(results)

    for country, items in grouped.items():
        flag = COUNTRY_FLAGS.get(country, "🌍")
        cheapest = min(r["price"] for r in items)

        st.markdown(
            f'<div class="country-section">'
            f'  <span class="country-flag">{flag}</span>'
            f'  <span class="country-name">{country}</span>'
            f'  <span class="country-count">{len(items)} {"city" if len(items) == 1 else "cities"}</span>'
            f'  <span class="country-cheapest">From {format_price(cheapest)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        cards_html = []
        for item in items:
            city = item.get("city", "Unknown destination")
            airport_code = item.get("airport_code", "")
            price = item.get("price")
            stops = item.get("stops", 0)
            airlines = item.get("airlines", "—")
            duration_mins = item.get("duration_mins")
            layover_text = item.get("layover_text", "—")
            departure_time = item.get("departure_time", "—")
            arrival_time = item.get("arrival_time", "—")
            booking_url = item.get("booking_url", "#")

            # Stops badge
            if stops == 0:
                stop_badge = '<span class="badge badge-direct">✈ Direct</span>'
            elif stops == 1:
                stop_badge = '<span class="badge">1 stop</span>'
            else:
                stop_badge = f'<span class="badge">{stops} stops</span>'

            # Duration badge
            dur_badge = f'<span class="badge">⏱ {format_duration(duration_mins)}</span>'

            # Price display
            price_html = (
                f'<div class="card-price">{format_price(price)}</div>'
                f'<div class="card-price-label">one way</div>'
                if price is not None
                else '<div class="card-price-unavailable">Fare unavailable</div>'
            )

            # Layover row (only if not direct)
            layover_row = (
                f'<div class="card-meta">'
                f'  <span class="card-meta-label">Layover</span>'
                f'  <span class="card-meta-value">{layover_text}</span>'
                f'</div>'
                if stops > 0 else ""
            )

            card_html = (
                f'<div class="dest-card">'
                f'  <div class="card-top">'
                f'    <div class="card-city">{city}</div>'
                f'    <div class="card-code">{airport_code}</div>'
                f'  </div>'
                f'  <div class="card-country">{country}</div>'
                f'  <div class="card-divider"></div>'
                f'  <div class="card-badges">{stop_badge}{dur_badge}</div>'
                f'  <div class="times-row">'
                f'    <span>{departure_time}</span>'
                f'    <div class="times-line"></div>'
                f'    <span>{arrival_time}</span>'
                f'  </div>'
                f'  <div class="card-meta">'
                f'    <span class="card-meta-label">Airline</span>'
                f'    <span class="card-meta-value">{airlines}</span>'
                f'  </div>'
                f'  {layover_row}'
                f'  <div class="card-footer">'
                f'    <div>{price_html}</div>'
                f'    <a class="book-btn" href="{booking_url}" target="_blank">'
                f'      View fares ›'
                f'    </a>'
                f'  </div>'
                f'</div>'
            )
            cards_html.append(card_html)

        st.markdown('<div class="card-grid">' + "".join(cards_html) + '</div>', unsafe_allow_html=True)


# ── App entry point ──────────────────────────────────────────────────────────

if "intro_shown" not in st.session_state:
    st.session_state.intro_shown = False

now = datetime.now(ZoneInfo(TIMEZONE))

# Inject fonts + CSS (no dark mode toggle — clean light theme)
st.markdown(get_theme_css(), unsafe_allow_html=True)

# Greeting screen
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

all_departure_airports = load_departure_airports()

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown(
    '''
    <div class="hero-eyebrow">North America → Europe</div>
    <h1 class="hero-title">Explore <em>Europe</em><br>from anywhere</h1>
    <p class="hero-subtitle">Choose a departure airport in the USA or Canada and explore Europe +
    Istanbul with filters, export, and quick handoff links.</p>
    ''',
    unsafe_allow_html=True,
)

# ── Search panel ─────────────────────────────────────────────────────────────
# Use Streamlit's native bordered container so widgets actually render inside it
with st.container(border=True):
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    with row1_col1:
        departure_country = st.selectbox(
            "Country",
            ["United States", "Canada"],
            index=0,
        )

    country_airports = get_airport_options_for_country(all_departure_airports, departure_country)

    if country_airports:
        labels = [a["label"] for a in country_airports]
        code_by_label = {a["label"]: a["code"] for a in country_airports}
        with row1_col2:
            selected_label = st.selectbox(
                "Departure Airport",
                labels,
                index=0,
            )
        origin = code_by_label[selected_label]
    else:
        origin = None
        with row1_col2:
            st.selectbox("Departure Airport", ["No airports found"], disabled=True)

    with row1_col3:
        default_date = (now + timedelta(days=30)).date()
        outbound_date = st.date_input(
            "Departure Date",
            value=default_date,
            min_value=(now + timedelta(days=1)).date(),
        )

    with st.expander("Advanced filters", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1:
            search_scope = st.selectbox(
                "Search Scope",
                ["Major airports only", "Full Europe"],
                index=0,
                help="Major airports is faster and lighter on API usage.",
            )
        with f2:
            stop_label = st.selectbox(
                "Stops",
                list(STOP_OPTIONS.keys()),
                index=0,
            )
            stops_param = STOP_OPTIONS[stop_label]
        with f3:
            sort_by = st.selectbox(
                "Sort Results",
                SORT_OPTIONS,
                index=0,
                key="sort_by_value",
            )

        all_destination_countries = sorted({d["country"] for d in EUROPE_DESTINATIONS})
        selected_destination_countries = st.multiselect(
            "Destination Countries",
            all_destination_countries,
            default=all_destination_countries,
        )

        f4, f5 = st.columns(2)
        with f4:
            max_price_enabled = st.toggle("Set max price", value=False)
        with f5:
            max_price = st.number_input(
                "Max Price (€)",
                min_value=50,
                step=50,
                value=500,
                disabled=not max_price_enabled,
            )

    st.markdown(
        '<p class="controls-note">Popular departure airports appear first. Results are grouped by destination country and city, and may include connecting flights depending on the stops filter.</p>',
        unsafe_allow_html=True,
    )

    btn_left, btn_mid, btn_right = st.columns([1.5, 1, 1.5])
    with btn_mid:
        search = st.button("Search flights", use_container_width=True, disabled=origin is None)


# ── Results ──────────────────────────────────────────────────────────────────
if search:
    if not API_KEY:
        st.error("Missing SERPAPI_KEY in Streamlit secrets.")
    elif origin is None:
        st.error("No valid departure airport found.")
    elif not selected_destination_countries:
        st.error("Please select at least one destination country.")
    else:
        destination_pool = get_destination_pool(search_scope, selected_destination_countries)

        if not destination_pool:
            st.warning("No destination airports match the current filters.")
        else:
            max_workers = 10 if search_scope == "Major airports only" else 8
            price_limit = max_price if max_price_enabled else None

            with st.spinner("Searching destinations..."):
                results = get_destinations(
                    origin=origin,
                    outbound_date=outbound_date.isoformat(),
                    destination_pool=destination_pool,
                    stops_param=stops_param,
                    max_price=price_limit,
                    sort_by=sort_by,
                    max_workers=max_workers,
                )

            st.markdown(
                f'<div class="results-header">Destinations from {origin}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="sub-header">{outbound_date.isoformat()} &nbsp;·&nbsp; {search_scope} &nbsp;·&nbsp; {stop_label}</div>',
                unsafe_allow_html=True,
            )

            if results:
                cheapest = min(r["price"] for r in results)
                st.markdown(
                    f'<div class="summary-bar">✓ &nbsp;{len(results)} cities found &nbsp;·&nbsp; Cheapest from {format_price(cheapest)}</div>',
                    unsafe_allow_html=True,
                )

                export_bytes = results_to_excel(results, origin, outbound_date.isoformat())
                dl_left, dl_mid, dl_right = st.columns([1.5, 1, 1.5])
                with dl_mid:
                    st.download_button(
                        "⬇ Download Excel",
                        data=export_bytes,
                        file_name=f"flight_explorer_{origin}_{outbound_date.isoformat()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

                render_cards(results)
            else:
                st.info("No destinations found for the selected airport, date, and filters.")
