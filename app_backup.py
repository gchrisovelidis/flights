import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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

ORIGIN_AIRPORTS = [
    "JFK", "LAX", "EWR", "MIA", "YYZ"
]

DESTINATIONS = [
    {"airport_code": "ATH", "city": "Athens", "country": "Greece"},
    {"airport_code": "SKG", "city": "Thessaloniki", "country": "Greece"},
    {"airport_code": "HER", "city": "Heraklion", "country": "Greece"},
    {"airport_code": "CFU", "city": "Corfu", "country": "Greece"},
    {"airport_code": "LHR", "city": "London", "country": "United Kingdom"},
    {"airport_code": "LGW", "city": "London", "country": "United Kingdom"},
    {"airport_code": "MAN", "city": "Manchester", "country": "United Kingdom"},
    {"airport_code": "CDG", "city": "Paris", "country": "France"},
    {"airport_code": "ORY", "city": "Paris", "country": "France"},
    {"airport_code": "NCE", "city": "Nice", "country": "France"},
    {"airport_code": "FRA", "city": "Frankfurt", "country": "Germany"},
    {"airport_code": "MUC", "city": "Munich", "country": "Germany"},
    {"airport_code": "BER", "city": "Berlin", "country": "Germany"},
    {"airport_code": "AMS", "city": "Amsterdam", "country": "Netherlands"},
    {"airport_code": "BRU", "city": "Brussels", "country": "Belgium"},
    {"airport_code": "ZRH", "city": "Zurich", "country": "Switzerland"},
    {"airport_code": "VIE", "city": "Vienna", "country": "Austria"},
    {"airport_code": "FCO", "city": "Rome", "country": "Italy"},
    {"airport_code": "MXP", "city": "Milan", "country": "Italy"},
    {"airport_code": "NAP", "city": "Naples", "country": "Italy"},
    {"airport_code": "MAD", "city": "Madrid", "country": "Spain"},
    {"airport_code": "BCN", "city": "Barcelona", "country": "Spain"},
    {"airport_code": "AGP", "city": "Malaga", "country": "Spain"},
    {"airport_code": "PMI", "city": "Palma", "country": "Spain"},
    {"airport_code": "LIS", "city": "Lisbon", "country": "Portugal"},
    {"airport_code": "OPO", "city": "Porto", "country": "Portugal"},
    {"airport_code": "IST", "city": "Istanbul", "country": "Turkey"},
    {"airport_code": "SAW", "city": "Istanbul", "country": "Turkey"},
    {"airport_code": "DXB", "city": "Dubai", "country": "United Arab Emirates"},
    {"airport_code": "DOH", "city": "Doha", "country": "Qatar"},
    {"airport_code": "CAI", "city": "Cairo", "country": "Egypt"},
    {"airport_code": "BKK", "city": "Bangkok", "country": "Thailand"},
    {"airport_code": "SIN", "city": "Singapore", "country": "Singapore"},
    {"airport_code": "HND", "city": "Tokyo", "country": "Japan"},
    {"airport_code": "NRT", "city": "Tokyo", "country": "Japan"},
    {"airport_code": "ICN", "city": "Seoul", "country": "South Korea"},
    {"airport_code": "BOS", "city": "Boston", "country": "United States"},
    {"airport_code": "ORD", "city": "Chicago", "country": "United States"},
    {"airport_code": "SFO", "city": "San Francisco", "country": "United States"},
    {"airport_code": "YUL", "city": "Montreal", "country": "Canada"},
]


def get_theme_css(dark_mode: bool) -> str:
    if dark_mode:
        bg = "#0B1220"
        greeting_bg = "#0B1220"
        card_bg = "#111827"
        card_border = "#1F2937"
        shadow = "0 10px 24px rgba(0, 0, 0, 0.28)"
        title = "#F8FAFC"
        subtitle = "#94A3B8"
        muted = "#94A3B8"
        pill_bg = "#172554"
        pill_text = "#93C5FD"
        fare = "#60A5FA"
        button_bg = "#1D4ED8"
        button_text = "#FFFFFF"
        input_bg = "#111827"
        input_text = "#F8FAFC"
        input_border = "#334155"
    else:
        bg = "#F6F7FB"
        greeting_bg = "#F6F7FB"
        card_bg = "#FFFFFF"
        card_border = "#E6EAF2"
        shadow = "0 6px 20px rgba(15, 23, 42, 0.04)"
        title = "#162033"
        subtitle = "#667085"
        muted = "#667085"
        pill_bg = "#EEF4FF"
        pill_text = "#1F5FAE"
        fare = "#1F5FAE"
        button_bg = "#1D4ED8"
        button_text = "#FFFFFF"
        input_bg = "#FFFFFF"
        input_text = "#162033"
        input_border = "#D0D5DD"

    return f"""
    <style>
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}

    .stApp {{
        background: {bg};
    }}

    [data-testid="stAppViewContainer"] {{
        background: {bg};
    }}

    .block-container {{
        max-width: 100% !important;
        padding-top: 0 !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }}

    .greeting-screen {{
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: {greeting_bg};
    }}

    .greeting-text {{
        font-size: 112px;
        font-weight: 800;
        line-height: 1;
        color: {title};
        text-align: center;
        animation: fadeInOut 4s ease-in-out forwards;
        padding: 0 30px;
        letter-spacing: -0.03em;
    }}

    @keyframes fadeInOut {{
        0%   {{ opacity: 0; transform: scale(0.96); }}
        20%  {{ opacity: 1; transform: scale(1); }}
        80%  {{ opacity: 1; transform: scale(1); }}
        100% {{ opacity: 0; transform: scale(1.02); }}
    }}

    .hero-title {{
        margin-top: 12px;
        font-size: 16px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: {subtitle};
        text-align: center;
    }}

    .hero-subtitle {{
        margin-top: 10px;
        margin-bottom: 30px;
        font-size: 18px;
        line-height: 1.5;
        color: {subtitle};
        text-align: center;
    }}

    .search-heading {{
        font-size: 34px;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.03em;
        color: {title};
        text-align: center;
        margin-bottom: 8px;
    }}

    .search-description {{
        font-size: 16px;
        line-height: 1.5;
        color: {subtitle};
        text-align: center;
        margin-bottom: 20px;
    }}

    .results-header {{
        font-size: 32px;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.03em;
        color: {title};
        text-align: center;
        margin-bottom: 20px;
    }}

    .card-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 18px;
    }}

    .destination-card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 22px;
        padding: 20px 20px 18px 20px;
        box-shadow: {shadow};
    }}

    .destination-city {{
        font-size: 24px;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.02em;
        color: {title};
        margin-bottom: 8px;
    }}

    .destination-code {{
        display: inline-block;
        font-size: 13px;
        font-weight: 800;
        color: {pill_text};
        background: {pill_bg};
        border-radius: 999px;
        padding: 5px 10px;
        margin-bottom: 12px;
        letter-spacing: 0.04em;
    }}

    .destination-country {{
        font-size: 15px;
        font-weight: 600;
        line-height: 1.4;
        color: {muted};
        margin-bottom: 10px;
    }}

    .destination-meta {{
        font-size: 14px;
        line-height: 1.5;
        color: {muted};
        margin-bottom: 6px;
    }}

    .destination-fare {{
        margin-top: 10px;
        font-size: 16px;
        font-weight: 800;
        color: {fare};
    }}

    .destination-fare.muted {{
        color: {muted};
    }}

    .controls-note {{
        font-size: 13px;
        color: {subtitle};
        text-align: center;
        margin-top: 10px;
    }}

    div[data-testid="stSelectbox"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stToggle"] label {{
        font-weight: 700;
        color: {title} !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: {input_bg} !important;
        color: {input_text} !important;
        border-color: {input_border} !important;
    }}

    div[data-testid="stDateInput"] input {{
        background-color: {input_bg} !important;
        color: {input_text} !important;
    }}

    div[data-testid="stButton"] button {{
        border-radius: 14px;
        padding: 0.72rem 1.7rem;
        font-weight: 700;
        font-size: 15px;
        background: {button_bg};
        color: {button_text};
        border: none;
    }}

    div[data-testid="stButton"] button:hover {{
        filter: brightness(1.05);
    }}

    @media (max-width: 900px) {{
        .greeting-text {{
            font-size: 64px;
            padding: 0 20px;
        }}

        .search-heading,
        .results-header {{
            font-size: 28px;
        }}

        .hero-subtitle {{
            font-size: 16px;
        }}

        .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
    }}
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


def parse_flight_result(data: dict, fallback: dict) -> dict | None:
    itineraries = []
    itineraries.extend(data.get("best_flights", []))
    itineraries.extend(data.get("other_flights", []))

    valid = []
    for itinerary in itineraries:
        price = itinerary.get("price")
        if price in [None, ""]:
            continue

        layovers = itinerary.get("layovers", []) or []
        flights = itinerary.get("flights", []) or []

        airline_names = []
        for flight in flights:
            airline = flight.get("airline")
            if airline and airline not in airline_names:
                airline_names.append(airline)

        valid.append(
            {
                "city": fallback["city"],
                "country": fallback["country"],
                "airport_code": fallback["airport_code"],
                "price": price,
                "stops": len(layovers),
                "airlines": ", ".join(airline_names[:2]) if airline_names else "—",
                "duration_mins": itinerary.get("total_duration"),
            }
        )

    if not valid:
        return None

    valid.sort(key=lambda x: x["price"])
    return valid[0]


@st.cache_data(ttl=21600, show_spinner=False)
def search_destination(origin: str, destination: dict, outbound_date: str) -> dict | None:
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
        "stops": 0,
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
        return parse_flight_result(data, destination)
    except Exception:
        return None


def get_destinations(origin: str, outbound_date: str) -> list[dict]:
    results = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(search_destination, origin, destination, outbound_date)
            for destination in DESTINATIONS
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    results.sort(key=lambda x: x["price"])
    return results


def format_duration(minutes: int | None) -> str:
    if not minutes:
        return "—"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


if "intro_shown" not in st.session_state:
    st.session_state.intro_shown = False

now = datetime.now(ZoneInfo(TIMEZONE))

top_left, top_right = st.columns([6, 1.2])
with top_right:
    dark_mode = st.toggle("Dark mode", value=False)

st.markdown(get_theme_css(dark_mode), unsafe_allow_html=True)

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

_, hero_col, _ = st.columns([1.2, 2, 1.2])

with hero_col:
    left_logo, center_logo, right_logo = st.columns([1, 2, 1])
    with center_logo:
        st.image("sig_logo.png", width=320)

    st.markdown('<div class="hero-title">Flight Explorer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Select a departure airport and explore direct or connecting destinations.</div>',
        unsafe_allow_html=True,
    )

_, search_col, _ = st.columns([1.1, 2.2, 1.1])

with search_col:
    st.markdown('<div class="search-heading">✈️ Find destinations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="search-description">Choose a starting airport and a departure date to discover available destinations worldwide.</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        origin = st.selectbox(
            "Departure Airport",
            ORIGIN_AIRPORTS,
            index=0,
        )

    with col2:
        default_date = (now + timedelta(days=30)).date()
        outbound_date = st.date_input(
            "Departure Date",
            value=default_date,
            min_value=(now + timedelta(days=1)).date(),
        )

    st.markdown(
        '<div class="controls-note">Results are sorted by cheapest fare found and may include connections.</div>',
        unsafe_allow_html=True,
    )

    btn_left, btn_mid, btn_right = st.columns([1.3, 1, 1.3])
    with btn_mid:
        search = st.button("Search", use_container_width=True)

if search:
    if not API_KEY:
        st.error("Missing SERPAPI_KEY in Streamlit secrets.")
    else:
        with st.spinner("Searching destinations..."):
            results = get_destinations(origin, outbound_date.isoformat())

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
                stops = item.get("stops", 0)
                airlines = item.get("airlines", "—")
                duration_mins = item.get("duration_mins")

                code_html = f'<div class="destination-code">{airport_code}</div>' if airport_code else ""
                fare_class = "destination-fare" if price not in [None, ""] else "destination-fare muted"
                fare_text = f"From €{price}" if price not in [None, ''] else "Fare unavailable"
                stop_text = "Direct" if stops == 0 else f"{stops} stop" if stops == 1 else f"{stops} stops"

                card_html = (
                    f'<div class="destination-card">'
                    f'<div class="destination-city">{city}</div>'
                    f'{code_html}'
                    f'<div class="destination-country">{country}</div>'
                    f'<div class="destination-meta"><strong>Routing:</strong> {stop_text}</div>'
                    f'<div class="destination-meta"><strong>Airline:</strong> {airlines}</div>'
                    f'<div class="destination-meta"><strong>Duration:</strong> {format_duration(duration_mins)}</div>'
                    f'<div class="{fare_class}">{fare_text}</div>'
                    f'</div>'
                )
                cards_html.append(card_html)

            st.markdown(
                '<div class="card-grid">' + "".join(cards_html) + '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No destinations found for the selected airport and date.")