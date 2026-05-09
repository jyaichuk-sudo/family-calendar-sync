import streamlit as st
import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

st.set_page_config(page_title="Week at a Glance", page_icon="🗓️", layout="wide")

# --- CONFIG ---
ICS_URL = "https://jyaichuk-sudo.github.io/family-calendar-sync/family_master.ics"
HOME_LAT, HOME_LON = 42.1034, -76.2624  # Owego, NY
LAT, LON = "42.1034", "-76.2624"

# --- HELPERS ---
geolocator = Nominatim(user_agent="family_dashboard_jyaichuk")

@st.cache_data(ttl=86400) # Cache coordinates for 24 hours
def get_coords(address):
    if not address or len(address) < 5: return None
    try:
        location = geolocator.geocode(address)
        if location: return (location.latitude, location.longitude)
    except: return None
    return None

@st.cache_data(ttl=3600) # Cache drive time for 1 hour
def get_drive_time(dest_coords):
    if not dest_coords: return None
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{HOME_LON},{HOME_LAT};{dest_coords[1]},{dest_coords[0]}?overview=false"
        res = requests.get(url).json()
        # Duration is in seconds, convert to minutes
        return round(res['routes'][0]['duration'] / 60)
    except: return None

# ... (keep get_weather() exactly as it was) ...
@st.cache_data(ttl=3600)
def get_weather():
    try:
        p_res = requests.get(f"https://api.weather.gov/points/{LAT},{LON}").json()
        f_res = requests.get(p_res['properties']['forecast']).json()
        data = {}
        for p in f_res['properties']['periods']:
            d = p['startTime'][:10]
            if d not in data: data[d] = {"high": "--", "low": "--", "precip": 0, "icon": "☀️", "full_desc": ""}
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
            else: data[d]['low'] = f"{p['temperature']}°"
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
                loc = str(ev.get('location', ''))
                emoji = summary[-1] if len(summary) > 0 else "📅"
                
                # Logic for Drive Time
                drive_min = None
                leave_time = None
                if loc and len(loc) > 5 and isinstance(start, datetime):
                    coords = get_coords(loc)
                    drive_min = get_drive_time(coords)
                    if drive_min:
                        # Calculate Leave Time (Event time minus drive time minus 5 min buffer)
                        leave_dt = start - timedelta(minutes=drive_min + 5)
                        leave_time = leave_dt.strftime("%-I:%M %p")

                daily_events[d].append({
                    "summary": summary, "emoji": emoji, "location": loc,
                    "time": start.strftime("%-I:%M %p") if isinstance(start, datetime) else "All Day",
                    "drive": drive_min, "leave": leave_time, "is_timed": isinstance(start, datetime)
                })

    # --- TOP SUMMARY (Keep existing code) ---
    st.subheader("Weekly Summary")
    summary_cols = st.columns(7)
    for i, d in enumerate(days):
        with summary_cols[i]:
            d_key = d.strftime('%Y-%m-%d')
            w = weather.get(d_key, {"high": "--", "low": "--", "precip": 0, "icon": "☀️"})
            emojis = "".join(list(dict.fromkeys([e['emoji'] for e in daily_events[d]])))
            with st.container(border=True):
                st.markdown(f"**{d.strftime('%a')}**")
                st.markdown(f'<p style="font-size:1.2rem; margin-bottom:5px;">{emojis if emojis else "✨"}</p>', unsafe_allow_html=True)
                st.markdown(f"**{w['high']}** / {w['low']}")
                prec_txt = f" {w['precip']}%" if w['precip'] > 0 else ""
                st.markdown(f'<p style="font-size:0.8rem; font-weight:bold;">{w["icon"]}{prec_txt}</p>', unsafe_allow_html=True)

    st.divider()

    # --- DETAILED VIEW (Drive Time Added Here) ---
    st.subheader("Daily Details")
    for d in days:
        with st.container():
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
                            if ev['location']:
                                st.markdown(f'<p style="font-size:0.85rem; color:#666;">📍 {ev["location"]}</p>', unsafe_allow_html=True)
                            
                            # DRIVE TIME ALERT
                            if ev['drive'] and ev['is_timed']:
                                st.info(f"🚗 **{ev['drive']} min drive.** Leave by **{ev['leave']}** to be early.")
                
                d_key = d.strftime('%Y-%m-%d')
                if weather and d_key in weather:
                    w = weather[d_key]
                    st.caption(f"🌤️ {w['icon']} {w.get('full_desc', '')}")
            st.divider()

if __name__ == "__main__":
    main()
    
