import streamlit as st
import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Week at a Glance", page_icon="🗓️", layout="wide")

# --- CONFIG ---
ICS_URL = "https://jyaichuk-sudo.github.io/family-calendar-sync/family_master.ics"
LAT = "42.1034"
LON = "-76.2624"

st.title("🗓️ Family Week at a Glance")

@st.cache_data(ttl=3600)
def get_weather():
    try:
        points_url = f"https://api.weather.gov/points/{LAT},{LON}"
        point_res = requests.get(points_url).json()
        forecast_url = point_res['properties']['forecast']
        forecast_res = requests.get(forecast_url).json()
        periods = forecast_res['properties']['periods']
        
        weather_data = {}
        for p in periods:
            d_str = p['startTime'][:10]
            if d_str not in weather_data:
                weather_data[d_str] = {"high": "--", "low": "--", "desc": "", "precip": 0}
            if p['isDaytime']:
                weather_data[d_str]['high'] = f"{p['temperature']}°"
                weather_data[d_str]['desc'] = p['shortForecast']
            else:
                weather_data[d_str]['low'] = f"{p['temperature']}°"
        return weather_data
    except:
        return None

def get_calendar_events():
    try:
        response = requests.get(ICS_URL)
        return Calendar.from_ical(response.content)
    except:
        return None

def main():
    cal = get_calendar_events()
    weather = get_weather()
    
    today = date.today()
    days_to_show = [today + timedelta(days=i) for i in range(7)]
    daily_events = {d: [] for d in days_to_show}

    if cal:
        for component in cal.walk('VEVENT'):
            dtstart = component.get('dtstart').dt
            event_date = dtstart.date() if isinstance(dtstart, datetime) else dtstart
            event_time = dtstart.strftime("%-I:%M %p") if isinstance(dtstart, datetime) else "All Day"
            if event_date in daily_events:
                daily_events[event_date].append({"time": event_time, "summary": component.get('summary')})

    # --- TOP SUMMARY SECTION ---
    st.subheader("Weekly Summary")
    summary_cols = st.columns(7)
    
    for i, day in enumerate(days_to_show):
        with summary_cols[i]:
            day_str = day.strftime('%Y-%m-%d')
            w = weather.get(day_str, {"high": "--", "low": "--"}) if weather else {"high": "--", "low": "--"}
            has_events = "🟢" if daily_events[day] else ""
            
            # Create a stylized summary box
            with st.container(border=True):
                st.markdown(f"**{day.strftime('%a')}** {has_events}")
                st.markdown(f"**{w['high']}** / {w['low']}")
    
    st.divider()

    # --- DETAILED VIEW SECTION ---
    detail_cols = st.columns(7)

    for i, day in enumerate(days_to_show):
        with detail_cols[i]:
            # 1. DATE HEADER
            st.markdown(f"### {day.strftime('%a')}")
            st.caption(day.strftime('%b %d'))
            
            # 2. EVENTS SECTION
            events = sorted(daily_events[day], key=lambda x: (x['time'] != "All Day", x['time']))
            if not events:
                st.write("✨ *Clear day*")
            else:
                for event in events:
                    with st.container(border=True):
                        st.markdown(f"**{event['time']}**")
                        st.markdown(f"**{event['summary']}**")
            
            st.write("") 

            # 3. WEATHER SECTION
            day_str = day.strftime('%Y-%m-%d')
            if weather and day_str in weather:
                w = weather[day_str]
                with st.expander("🌤️ Forecast", expanded=False): # Closed by default to keep clean
                    st.write(f"**{w['high']}** / {w['low']}")
                    st.caption(f"{w['desc']}")
            else:
                st.caption("Weather N/A")

if __name__ == "__main__":
    main()
