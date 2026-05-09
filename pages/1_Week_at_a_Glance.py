import streamlit as st
import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Week at a Glance", page_icon="🗓️", layout="wide")

# --- CSS TO FORCE HORIZONTAL SUMMARY ON MOBILE ---
st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"]:first-of-type {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
    }
    [data-testid="stHorizontalBlock"]:first-of-type > div {
        min-width: 110px !important; 
    }
    .precip-text {
        font-size: 0.75rem;
        color: #3498db;
        font-weight: bold;
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
                data[d] = {"high": "--", "low": "--", "desc": "", "precip": 0, "type": ""}
            
            if p['isDaytime']:
                data[d]['high'] = f"{p['temperature']}°"
                data[d]['desc'] = p['shortForecast']
                # Pull precipitation %
                prob = p.get('probabilityOfPrecipitation', {}).get('value', 0)
                data[d]['precip'] = prob if prob else 0
                
                # Extract simple type from description (Rain, Snow, Mix, etc)
                desc = p['shortForecast'].lower()
                if 'snow' in desc: data[d]['type'] = "Snow"
                elif 'rain' in desc: data[d]['type'] = "Rain"
                elif 'showers' in desc: data[d]['type'] = "Showers"
                elif 'thunder' in desc or 't-storms' in desc: data[d]['type'] = "T-Storms"
                elif 'ice' in desc or 'freezing' in desc: data[d]['type'] = "Ice"
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
                daily_events[d].append({"summary": summary, "emoji": emoji, "time": start.strftime("%-I:%M %p
                
