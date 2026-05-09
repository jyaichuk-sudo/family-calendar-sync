import streamlit as st
import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date
import time
import pytz

# --- INITIAL SETUP ---
st.set_page_config(page_title="Week at a Glance", page_icon="🗓️", layout="wide")

# Replace these with your actual GitHub info
USERNAME = "jyaichuk-sudo"
REPO = "family-calendar-sync"
LAT, LON = "42.1034", "-76.2624"

# Points to Raw GitHub to avoid the GitHub Pages cache delay
RAW_BASE = f"https://raw.githubusercontent.com/{USERNAME}/{REPO}/main"
ICS_URL = f"{RAW_BASE}/family_master.ics"
CD_URL = f"{RAW_BASE}/countdowns.txt"

# --- CSS TUNING ---
st.markdown("""
    <style>
    /* Force Summary to stay horizontal on mobile */
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
        min-height: 1.5rem;
    }
    .weather-sub {
        font-size: 0.8rem;
        font-weight: bold;
        color: #555;
    }
    .countdown-card {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_weather():
    try:
        # 1. Get the hourly forecast URL
        p_res = requests.get(f"https://api.weather.gov/points/{LAT},{LON}").json()
        h_url = p_res['properties']['forecastHourly']
        h_res = requests.get(h_url).json()
        
        # 2. Store data indexed by "YYYY-MM-DD HH:00"
        hourly_data = {}
        for p in h_res['properties']['periods']:
            # The API gives ISO format: 2026-05-09T18:00:00-04:00
            # We simplify to "2026-05-09 18" for easy matching
            timestamp = p['startTime'][:13].replace('T', ' ')
            prob = p.get('probabilityOfPrecipitation', {}).get('value', 0)
            
            # Map description to icons
            desc = p['shortForecast'].lower()
            if 'snow' in desc: icon = "❄️"
            elif 'thunder' in desc or 't-storm' in desc: icon = "⚡"
            elif 'rain' in desc or 'showers' in desc: icon = "💧"
            elif 'cloud' in desc: icon = "☁️"
            else: icon = "☀️"

            hourly_data[timestamp] = {
                "temp": f"{p['temperature']}°",
                "precip": f"{prob}%" if prob and prob > 0 else "",
                "icon": icon,
                "desc": p['shortForecast']
            }
        return hourly_data
    except Exception as e:
        st.error(f"Weather Error: {e}")
        return {}

def main():
    st.title("🗓️ Family Week at a Glance")
    
    # Cache buster ensures we see updates the second they are saved in Admin
    cache_buster = f"?v={int(time.time())}"

    # --- 1. LOAD COUNTDOWNS ---
    countdowns = []
    try:
        cd_res = requests.get(CD_URL + cache_buster)
        if cd_res.status_code == 200:
            for line in cd_res.text.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    name = parts[0].strip()
                    try:
                        target = datetime.strptime(parts[1].strip(), '%Y-%m-%d').date()
                        diff = (target - date.today()).days
                        if diff >= 0: countdowns.append((name, diff))
                    except: continue
    except: pass

    if countdowns:
        cd_cols = st.columns(len(countdowns))
        for i, (name, days) in enumerate(countdowns):
            with cd_cols[i]:
                st.markdown(f"""
                <div class="countdown-card">
                    <div style="font-size: 0.8rem; color: #555;">{name}</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #ff4b4b;">{days} Days</div>
                </div>
                """, unsafe_allow_html=True)
        st.write("")

    # --- 2. LOAD CALENDAR & WEATHER ---
    weather = get_weather()
    res = requests.get(ICS_URL + cache_buster)
    cal = Calendar.from_ical(res.content) if res.status_code == 200 else None
    
    today = date.today()
    days = [today + timedelta(days=i) for i in range(7)]
    daily_events = {d: [] for d in days}

    # Define your local timezone
    local_tz = pytz.timezone("America/New_York")

    if cal:
        for ev in cal.walk('VEVENT'):
            start = ev.get('dtstart').dt
            
            # 1. TIMEZONE CONVERSION LOGIC
            if isinstance(start, datetime):
                # If the time is in UTC (has a 'Z' or offset), convert to NY time
                if start.tzinfo is not None:
                    start = start.astimezone(local_tz)
                else:
                    # If the time is "floating" (no TZ), assume it's already local
                    start = local_tz.localize(start)
            
            # 2. ASSIGN TO DAY
            d = start.date() if isinstance(start, datetime) else start
            if d in daily_events:
                summary = str(ev.get('summary'))
                loc = str(ev.get('location', ''))
                emoji = summary[-1] if len(summary) > 0 else "📅"
                
                daily_events[d].append({
                    "summary": summary, 
                    "emoji": emoji, 
                    "location": loc,
                    "dt_obj": start,
                    # Display the newly converted local time
                    "time": start.strftime("%-I:%M %p") if isinstance(start, datetime) else "All Day"
                })

    # --- 3. WEEKLY SUMMARY (Horizontal Cards) ---
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

    # --- 4. DAILY DETAILS (Responsive List) ---
    st.subheader("Daily Details")
    for d in days:
        with st.container():
            col_a, col_b = st.columns([1, 4])
            with col_a:
                st.markdown(f"### {d.strftime('%a')}")
                st.caption(d.strftime('%b %d'))
            with col_b:
for ev in events:
    with st.container(border=True):
        # 1. Create the lookup key for this event's hour
        # If it's 2:30 PM on May 9, we look for "2026-05-09 14"
        weather_info = ""
        if ev['time'] != "All Day":
            # We need the original start object we saved earlier
            # Let's assume you're using the 'start' datetime object from earlier logic
            # You'll want to add 'dt_obj': start to your daily_events list in the loop above
            event_hour_key = ev['dt_obj'].strftime('%Y-%m-%d %H')
            
            if event_hour_key in weather:
                w = weather[event_hour_key]
                weather_info = f" | {w['icon']} {w['temp']}"
                if w['precip']:
                    weather_info += f" ({w['precip']} 💧)"

        # 2. Display the event with the weather snippet
        st.markdown(f"**{ev['time']}** — {ev['summary']}{weather_info}")
        
        if ev.get('location') and ev.get('location') != 'None':
            st.markdown(f'<p style="font-size:0.85rem; color:#666; margin-top:2px;">📍 {ev["location"]}</p>', unsafe_allow_html=True)
            st.divider()

if __name__ == "__main__":
    main()
