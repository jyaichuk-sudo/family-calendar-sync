import streamlit as st
import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Week at a Glance", page_icon="🗓️", layout="wide")

# --- CSS FOR COMPACT SUMMARY ---
st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"]:first-of-type {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
    }
    [data-testid="stHorizontalBlock"]:first-of-type > div {
        min-width: 100px !important; 
    }
    .emoji-row {
        font-size: 1.2rem;
        margin-top: -5px;
        margin-bottom: 5px;
        min-height: 1.5rem;
    }
    .weather-sub {
        font-size: 0.8rem;
        font-weight: bold;
        color: #555;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIG ---
ICS_URL = "https://jyaichuk-sudo.github.io/family-calendar-sync/family_master.ics"
LAT = "42.1034"
LON = "-76.2624"

st.title("🗓️ Family Week at a Glance")

@st.cache_data(ttl=3600)
def get_weather():
    try:
        p_res = requests.get(f"https://api.weather.gov/points/{LAT},{LON}").json()
        f_res = requests.get(p_res['properties']['forecast']).json()
        data = {}
        for p in f_res['properties']['periods']:
            d = p['startTime'][:10]
            if d not in data: 
                data[d] = {"high": "--", "low": "--", "precip": 0, "icon": "☀️"}
            
            if p['isDaytime']:
                data[d]['high'] = f"{p['temperature']}°"
                prob = p.get('probabilityOfPrecipitation', {}).get('value', 0)
                data[d]['precip'] = prob if prob else 0
                
                desc = p['shortForecast'].lower()
                if 'snow' in desc: data[d]['icon'] = "❄️"
                elif 'thunder' in desc or 't-storm' in desc: data[d]['icon'] = "⚡"
                elif 'rain' in desc or 'showers' in desc: data[d]['icon'] = "💧"
                elif 'cloud' in desc: data[d]['icon'] = "☁️"
                else: data[d]['icon'] = "☀️"
            else:
                data[d]['low'] = f"{p['temperature']}°"
        return data
    except: return None

def main():
    res = requests.get(ICS_URL)
    cal = Calendar.from_ical(res.content) if res.status_code == 200 else None
    weather = get_weather()
    
    today = date.today()
    days = [today + timedelta(days=i) for i in range(7)]
    daily_events = {d: [] for d in days}

    if cal:
        for ev in cal.walk('VEVENT'):
            start = ev.get('dtstart').dt
            d = start.date() if isinstance(start, datetime) else start
            if d in daily_events:
                summary = str(ev.get('summary'))
                # Pull the emoji from the end of the summary
                emoji = summary[-1] if len(summary) > 0 else "📅"
                daily_events[d].append({"summary": summary, "emoji": emoji, "time": start.strftime("%-I:%M %p") if isinstance(start, datetime) else "All Day"})

    # --- TOP SUMMARY SECTION ---
    st.subheader("Weekly Summary")
    summary_cols = st.columns(7)
    for i, d in enumerate(days):
        with summary_cols[i]:
            d_key = d.strftime('%Y-%m-%d')
            w = weather.get(d_key, {"high": "--", "low": "--", "precip": 0, "icon": "☀️"})
            
            # Extract unique emojis
            emojis = "".join(list(dict.fromkeys([e['emoji'] for e in daily_events[d]])))
            
            with st.container(border=True):
                st.markdown(f"**{d.strftime('%a')}**")
                # Emojis on their own line with custom CSS class
                st.markdown(f'<p class="emoji-row">{emojis if emojis else "✨"}</p>', unsafe_allow_html=True)
                st.markdown(f"**{w['high']}** / {w['low']}")
                
                precip_text = f" {w['precip']}%" if w['precip'] > 0 else ""
                st.markdown(f'<p class="weather-sub">{w["icon"]}{precip_text}</p>', unsafe_allow_html=True)

    st.divider()

    # --- DETAILED VIEW SECTION ---
    detail_cols = st.columns(7)
    for i, d in enumerate(days):
        with detail_cols[i]:
            st.markdown(f"### {d.strftime('%a')}")
            st.caption(d.strftime('%b %d'))
            
            for ev in sorted(daily_events[d], key=lambda x: (x['time'] != "All Day", x['time'])):
                with st.container(border=True):
                    st.markdown(f"**{ev['time']}**")
                    st.markdown(f"{ev['summary']}")

            st.write("") 
            d_key = d.strftime('%Y-%m-%d')
            if weather and d_key in weather:
                w = weather[d_key]
                with st.expander("🌤️ Details", expanded=False):
                    st.write(f"**{w['high']}** / {w['low']}")
                    st.caption(f"{w['icon']} Forecast active")

if __name__ == "__main__":
    main()
    
