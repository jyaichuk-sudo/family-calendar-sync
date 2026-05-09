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
        
        hourly_data = {}
        daily_extremes = {} 
        
        for p in h_res['properties']['periods']:
            # Key format: "YYYY-MM-DD HH"
            date_str = p['startTime'][:10]
            timestamp = p['startTime'][:13].replace('T', ' ')
            temp = p['temperature']
            prob = p.get('probabilityOfPrecipitation', {}).get('value', 0)
            
            # Map description to icons
            desc = p['shortForecast'].lower()
            if 'snow' in desc: icon = "❄️"
            elif 'thunder' in desc or 't-storm' in desc: icon = "⚡"
            elif 'rain' in desc or 'showers' in desc: icon = "💧"
            elif 'cloud' in desc: icon = "☁️"
            else: icon = "☀️"

            # Store hourly details
            hourly_data[timestamp] = {
                "temp": f"{temp}°",
                "precip": f"{prob}%" if prob and prob > 0 else "",
                "icon": icon,
                "desc": p['shortForecast']
            }

            # Track daily High/Low
            if date_str not in daily_extremes:
                daily_extremes[date_str] = {"high": temp, "low": temp}
            else:
                if temp > daily_extremes[date_str]["high"]: daily_extremes[date_str]["high"] = temp
                if temp < daily_extremes[date_str]["low"]: daily_extremes[date_str]["low"] = temp

        hourly_data["extremes"] = daily_extremes
        return hourly_data
    except Exception as e:
        st.error(f"Weather API Error: {e}")
        return {}

def main():
    st.title("🗓️ Family Week at a Glance")
    
    # Cache buster ensures we see updates instantly
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
    local_tz = pytz.timezone("America/New_York")

    if cal:
        for ev in cal.walk('VEVENT'):
            start = ev.get('dtstart').dt
            
            # Timezone Conversion
            if isinstance(start, datetime):
                if start.tzinfo is not None:
                    start = start.astimezone(local_tz)
                else:
                    start = local_tz.localize(start)
            
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
                    "time": start.strftime("%-I:%M %p") if isinstance(start, datetime) else "All Day"
                })

    # --- 3. WEEKLY SUMMARY ---
    st.subheader("Weekly Summary")
    summary_cols = st.columns(7)
    extremes = weather.get("extremes", {})

    for i, d in enumerate(days):
        with summary_cols[i]:
            d_key = d.strftime('%Y-%m-%d')
            day_icon_key = f"{d_key} 12" # Use noon for summary icon
            hour_info = weather.get(day_icon_key, {"icon": "☀️", "precip": ""})
            day_ex = extremes.get(d_key, {"high": "--", "low": "--"})
            
            emojis = "".join(list(dict.fromkeys([e['emoji'] for e in daily_events[d]])))
            with st.container(border=True):
                st.markdown(f"**{d.strftime('%a')}**")
                st.markdown(f'<p class="emoji-row">{emojis if emojis else "✨"}</p>', unsafe_allow_html=True)
                st.markdown(f"**{day_ex['high']}°** / {day_ex['low']}°")
                st.markdown(f'<p class="weather-sub">{hour_info["icon"]} {hour_info["precip"]}</p>', unsafe_allow_html=True)

    st.divider()

    # --- 4. DAILY DETAILS ---
    st.subheader("Daily Details")
    for d in days:
        with st.container():
            col_a, col_b = st.columns([1, 4])
            with col_a:
                st.markdown(f"### {d.strftime('%a')}")
                st.caption(d.strftime('%b %d'))
            with col_b:
                events = sorted(daily_events[d], key=lambda x: (x['time'] != "All Day", x['time']))
                if not events:
                    st.write("✨ *No scheduled events*")
                else:
                    for ev in events:
                        with st.container(border=True):
                            # Title line
                            st.markdown(f"**{ev['time']}** — {ev['summary']}")
                            
                            # Weather line (hourly check)
                            if ev['time'] != "All Day":
                                event_hour_key = ev['dt_obj'].strftime('%Y-%m-%d %H')
                                if event_hour_key in weather:
                                    w = weather[event_hour_key]
                                    precip_str = f" ({w['precip']} 💧)" if w['precip'] else ""
                                    st.markdown(f'<p style="font-size:0.9rem; color:#444; margin-bottom:0px;">{w["icon"]} {w["temp"]} - {w["desc"]}{precip_str}</p>', unsafe_allow_html=True)

                            # Location line
                            if ev.get('location') and ev.get('location') != 'None':
                                st.markdown(f'<p style="font-size:0.85rem; color:#666; margin-top:2px;">📍 {ev["location"]}</p>', unsafe_allow_html=True)
        st.divider()

if __name__ == "__main__":
    main()
