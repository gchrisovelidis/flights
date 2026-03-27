import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(
    page_title="Flight Explorer",
    layout="wide",
)

API_KEY = "YOUR_SERPAPI_KEY"  # <-- replace later

TIMEZONE = ZoneInfo("Europe/Athens")

# -----------------------
# GREETING
# -----------------------
def get_greeting():
    now = datetime.now(TIMEZONE).hour

    if 0 <= now < 7:
        return "Τι κάνεις εδώ τέτοια ώρα;"
    elif 7 <= now < 12:
        return "Καλημέρα!"
    else:
        return "Καλησπέρα!"

# -----------------------
# SERPAPI FUNCTION
# -----------------------
@st.cache_data(ttl=86400)
def get_destinations(origin):
    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_travel_explore",
        "departure_id": origin,
        "api_key": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []

    if "destinations" in data:
        for d in data["destinations"]:
            results.append({
                "city": d.get("city"),
                "price": d.get("price"),
                "country": d.get("country")
            })

    return results

# -----------------------
# STYLING
# -----------------------
st.markdown("""
<style>
.logo-container {
    text-align: center;
    margin-top: 10px;
    margin-bottom: 10px;
}
.greeting {
    text-align: center;
    font-size: 42px;
    font-weight: 600;
    margin-top: 10px;
    margin-bottom: 30px;
    animation: fadeIn 1.5s ease-in;
}
.card {
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 15px;
    background-color: rgba(240,240,240,0.08);
}
@keyframes fadeIn {
    from {opacity: 0;}
    to {opacity: 1;}
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# HEADER (LOGO + GREETING)
# -----------------------
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image("sig_logo.png", width=180)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="greeting">{get_greeting()}</div>',
    unsafe_allow_html=True
)

# -----------------------
# SEARCH
# -----------------------
st.subheader("✈️ Find destinations")

col1, col2 = st.columns([1, 2])

with col1:
    origin = st.selectbox(
        "Departure Airport",
        ["JFK", "LHR", "ATH", "CDG", "FRA"]
    )

    search = st.button("Search")

# -----------------------
# RESULTS
# -----------------------
with col2:
    if search:
        results = get_destinations(origin)

        if results:
            st.markdown(f"### Destinations from {origin}")

            for r in results:
                st.markdown(f"""
                <div class="card">
                    ✈️ <b>{r['city']}</b><br>
                    🌍 {r['country']}<br>
                    💰 From €{r['price']}
                </div>
                """, unsafe_allow_html=True)

        else:
            st.warning("No destinations found.")