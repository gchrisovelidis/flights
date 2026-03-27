import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Flight Explorer",
    layout="wide",
)

API_KEY = "YOUR_SERPAPI_KEY"
TIMEZONE = ZoneInfo("Europe/Athens")


def get_greeting():
    now = datetime.now(TIMEZONE).hour
    if 0 <= now < 7:
        return "Τι κάνεις εδώ τέτοια ώρα;"
    elif 7 <= now < 12:
        return "Καλημέρα!"
    else:
        return "Καλησπέρα!"


@st.cache_data(ttl=86400)
def get_destinations(origin):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_travel_explore",
        "departure_id": origin,
        "api_key": API_KEY
    }

    response = requests.get(url, params=params, timeout=30)
    data = response.json()

    results = []
    if "destinations" in data:
        for d in data["destinations"]:
            results.append({
                "city": d.get("city"),
                "country": d.get("country"),
                "price": d.get("price")
            })
    return results


st.markdown("""
<style>
footer {visibility: hidden;}
header {visibility: hidden;}
#MainMenu {visibility: hidden;}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

.hero-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-top: 8px;
    margin-bottom: 60px;
}

.hero-logo {
    display: flex;
    justify-content: center;
    margin-bottom: 26px;
}

.hero-greeting {
    text-align: center;
    font-size: clamp(56px, 6vw, 96px);
    font-weight: 700;
    line-height: 1.05;
    color: #1f2430;
    letter-spacing: -0.02em;
    animation: fadeInUp 1.2s ease;
    margin: 0;
}

.search-wrap {
    max-width: 460px;
    margin-top: 20px;
}

.section-title {
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 18px;
    color: #1f2430;
}

.card {
    padding: 18px;
    border-radius: 16px;
    margin-bottom: 14px;
    background: rgba(240, 242, 246, 0.85);
    border: 1px solid rgba(0,0,0,0.06);
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(16px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (prefers-color-scheme: dark) {
    .hero-greeting,
    .section-title {
        color: #f5f7fb;
    }

    .card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
    }
}
</style>
""", unsafe_allow_html=True)


st.markdown('<div class="hero-wrap">', unsafe_allow_html=True)
st.markdown('<div class="hero-logo">', unsafe_allow_html=True)
st.image("sig_logo.png", width=220)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f'<h1 class="hero-greeting">{get_greeting()}</h1>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)


left, right = st.columns([1, 1.8])

with left:
    st.markdown('<div class="search-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">✈️ Find destinations</div>', unsafe_allow_html=True)

    origin = st.selectbox(
        "Departure Airport",
        ["JFK", "LHR", "ATH", "CDG", "FRA"]
    )

    search = st.button("Search")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    if search:
        with st.spinner("Searching destinations..."):
            results = get_destinations(origin)

        if results:
            st.markdown(f"### Destinations from {origin}")
            for r in results:
                price_text = f"💰 From €{r['price']}" if r["price"] else "💰 Price unavailable"
                country_text = r["country"] if r["country"] else "Country unavailable"
                city_text = r["city"] if r["city"] else "Destination unavailable"

                st.markdown(f"""
                <div class="card">
                    <b>✈️ {city_text}</b><br>
                    🌍 {country_text}<br>
                    {price_text}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No destinations found.")