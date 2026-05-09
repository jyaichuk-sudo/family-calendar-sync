import streamlit as st
import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date
import re

st.set_page_config(page_title="Week at a Glance", page_icon="🗓️", layout="wide")

# CSS for horizontal summary
st.markdown("<style>[data-testid='stHorizontalBlock']:first-of-type {display: flex !important; flex-wrap: nowrap !important; overflow-x: auto !important;} [data-testid='stHorizontalBlock']:first-of-type > div {min-width: 100px !important;}</style>", unsafe_allow_html=True)

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
            if d not in data: data[d] = {"high": "--", "low": "--", "desc": ""}
            if p['isDaytime']:
                data[d]['high'] = f"{p['temperature']}°"
                data[d]['desc'] = p['shortForecast']
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
                # Extract emoji (last char usually)
                emoji = summary[-1] if len(summary) > 0 else "📅"
                daily_events[d].append({"summary": summary, "emoji": emoji, "time": start.strftime("%-I:%M %p") if isinstance(start, datetime) else "All Day"})

    # --- SUMMARY ---
    summary_cols = st.columns(7)
    for i, d in enumerate(days):
        with summary_cols[i]:
            w = weather.get(d.strftime('%Y-%m-%d'), {"high": "--", "low": "--"})
            # Get unique emojis for the day
            emojis = "".join(list(set([e['emoji'] for e in daily_events[d]])))
            with st.container(border=True):
                st.markdown(f"**{d.strftime('%a')}**")
                st.markdown(f"{emojis if emojis else '✨'}")
                st.markdown(f"<small>{w['high']}/{w['low']}</small>", unsafe_allow_html=True)

    st.divider()
    # --- DETAILS ---
    detail_cols = st.columns(7)
    for i, d in enumerate(days):
        with detail_cols[i]:
            st.markdown(f"### {d.strftime('%a')}")
            st.caption(d.strftime('%b %d'))
            for ev in sorted(daily_events[d], key=lambda x: (x['time'] != "All Day", x['time'])):
                with st.container(border=True):
                    st.markdown(f"**{ev['time']}**")
                    st.markdown(ev['summary'])

if __name__ == "__main__":
    main()
