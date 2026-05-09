import streamlit as st
import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Week at a Glance", page_icon="🗓️", layout="wide")

# --- CSS FOR UI TUNING ---
st.markdown("""
    <style>
    /* Force the FIRST set of columns (Summary) to stay horizontal */
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
                data[d] = {"high": "--", "low": "--", "precip": 0, "icon": "☀️", "full_desc": ""}
            
            if p['isDaytime']:
                data[d]['high'] = f"{p['temperature']}°"
                data[d]['full_desc'] = p['shortForecast']
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
                emoji = summary[-1] if len(summary) > 0 else "📅"
                daily_events[d].append({
                    "summary": summary, 
                    "emoji": emoji, 
                    "time": start.strftime("%-I:%M %p") if isinstance(start, datetime) else "All Day"
                })

    # --- 1. WEEKLY SUMMARY (Horizontal/Non-Responsive) ---
    st.subheader("Weekly Summary")
    summary_cols = st.columns(7)
    for i, d in enumerate(days):
        with summary_cols[i]:
            d_key = d.strftime('%Y-%m-%d')
            w = weather.get(d_key, {"high": "--", "low": "--", "precip": 0, "icon": "☀️"})
            emojis = "".join(list(dict.fromkeys([e['emoji'] for e in daily_events[d]])))
            
            with st.container(border=True):
                st.markdown(f"**{d.strftime('%a')}**")
                st.markdown(f'<p class="emoji-row">{emojis if emojis else "✨"}</p>', unsafe_allow_html=True)
                st.markdown(f"**{w['high']}** / {w['low']}")
                precip_text = f" {w['precip']}%" if w['precip'] > 0 else ""
                st.markdown(f'<p class="weather-sub">{w["icon"]}{precip_text}</p>', unsafe_allow_html=True)

    st.divider()

    # --- 2. DETAILED VIEW (Responsive/Vertical on Mobile) ---
    st.subheader("Daily Details")
    
    # We use a loop WITHOUT st.columns here to allow natural stacking
    for d in days:
        with st.container():
            # Day Header
            col_a, col_b = st.columns([1, 4])
            with col_a:
                st.markdown(f"### {d.strftime('%a')}")
                st.caption(d.strftime('%b %d'))
            
            with col_b:
                # Events for the day
                events = sorted(daily_events[d], key=lambda x: (x['time'] != "All Day", x['time']))
                if not events:
                    st.write("✨ *No scheduled events*")
                else:
                    for ev in events:
                        with st.container(border=True):
                            st.markdown(f"**{ev['time']}** — {ev['summary']}")
                
                # Weather detail at bottom of day
                d_key = d.strftime('%Y-%m-%d')
                if weather and d_key in weather:
                    w = weather[d_key]
                    st.caption(f"🌤️ {w['icon']} {w.get('full_desc', 'Forecast active')}")
            
            st.divider()

if __name__ == "__main__":
    main()
    
