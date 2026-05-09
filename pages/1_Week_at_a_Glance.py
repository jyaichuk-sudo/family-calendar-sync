import streamlit as st
import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Week at a Glance", page_icon="🗓️", layout="wide")

# --- CSS TUNING ---
st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"]:first-of-type { display: flex !important; flex-wrap: nowrap !important; overflow-x: auto !important; }
    [data-testid="stHorizontalBlock"]:first-of-type > div { min-width: 100px !important; }
    .emoji-row { font-size: 1.2rem; margin-top: -5px; min-height: 1.5rem; }
    .weather-sub { font-size: 0.8rem; font-weight: bold; color: #555; }
    .countdown-card {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        border-left: 5px solid #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIG ---
USERNAME = "jyaichuk-sudo"
REPO = "family-calendar-sync"

# Points to Raw GitHub (Instant) rather than GitHub Pages (Delayed)
RAW_BASE = f"https://raw.githubusercontent.com/{USERNAME}/{REPO}/main"

ICS_URL = f"{RAW_BASE}/family_master.ics"
CD_URL = f"{RAW_BASE}/countdowns.txt"

LAT, LON = "42.1034", "-76.2624"

# (Keep your existing get_weather() and get_calendar_events() functions)
@st.cache_data(ttl=3600)
def get_weather():
    try:
        p_res = requests.get(f"https://api.weather.gov/points/{LAT},{LON}").json()
        f_res = requests.get(p_res['properties']['forecast']).json()
        data = {}
        for p in f_res['properties']['periods']:
            d = p['startTime'][:10]
            if d not in data: data[d] = {"high": "--", "low": "--", "precip": 0, "icon": "☀️"}
            if p['isDaytime']:
                data[d]['high'] = f"{p['temperature']}°"; prob = p.get('probabilityOfPrecipitation', {}).get('value', 0)
                data[d]['precip'] = prob if prob else 0; desc = p['shortForecast'].lower()
                if 'snow' in desc: data[d]['icon'] = "❄️"
                elif 'thunder' in desc: data[d]['icon'] = "⚡"
                elif 'rain' in desc or 'showers' in desc: data[d]['icon'] = "💧"
                else: data[d]['icon'] = "☀️"
            else: data[d]['low'] = f"{p['temperature']}°"
        return data
    except: return None

def main():
    # --- LOAD COUNTDOWNS ---
    countdowns = []
    try:
        cd_res = requests.get(CD_URL)
        if cd_res.status_code == 200:
            for line in cd_res.text.strip().split('\n'):
                if '|' in line:
                    name, d_str = line.split('|')
                    target = datetime.strptime(d_str.strip(), '%Y-%m-%d').date()
                    diff = (target - date.today()).days
                    if diff >= 0: countdowns.append((name, diff))
    except: pass

    # --- DISPLAY COUNTDOWNS ---
    if countdowns:
        cols = st.columns(len(countdowns))
        for i, (name, days) in enumerate(countdowns):
            with cols[i]:
                st.markdown(f"""
                <div class="countdown-card">
                    <div style="font-size: 0.8rem; color: #555;">{name}</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #ff4b4b;">{days} Days</div>
                </div>
                """, unsafe_allow_html=True)
        st.write("")

    # --- LOAD CALENDAR & WEATHER ---
    weather = get_weather()
    res = requests.get(ICS_URL)
    cal = Calendar.from_ical(res.content) if res.status_code == 200 else None
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
                daily_events[d].append({"summary": summary, "emoji": emoji, "time": start.strftime("%-I:%M %p") if isinstance(start, datetime) else "All Day"})

    # --- WEEKLY SUMMARY ---
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
                st.markdown(f'<p class="weather-sub">{w["icon"]} {str(w["precip"])+"%" if w["precip"] > 0 else ""}</p>', unsafe_allow_html=True)

    st.divider()
    # --- DETAILS ---
    for d in days:
        col_a, col_b = st.columns([1, 4])
        with col_a:
            st.markdown(f"### {d.strftime('%a')}")
            st.caption(d.strftime('%b %d'))
        with col_b:
            events = sorted(daily_events[d], key=lambda x: (x['time'] != "All Day", x['time']))
            if not events: st.write("✨ *No scheduled events*")
            else:
                for ev in events:
                    with st.container(border=True):
                        st.markdown(f"**{ev['time']}** — {ev['summary']}")
        st.divider()

if __name__ == "__main__":
    main()
    
