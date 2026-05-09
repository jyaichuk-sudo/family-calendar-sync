import streamlit as st
import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date
import pytz

st.set_page_config(page_title="Week at a Glance", page_icon="🗓️", layout="wide")

# --- CONFIG ---
# Replace with your actual GitHub Pages URL
ICS_URL = "https://jyaichuk-sudo.github.io/family-calendar-sync/family_master.ics"

st.title("🗓️ Family Week at a Glance")

def get_calendar_events():
    try:
        response = requests.get(ICS_URL)
        response.raise_for_status()
        cal = Calendar.from_ical(response.content)
        return cal
    except Exception as e:
        st.error(f"Could not load calendar: {e}")
        return None

def main():
    cal = get_calendar_events()
    if not cal:
        return

    # Set up our date range: Today + 6 days
    today = date.today()
    days_to_show = [today + timedelta(days=i) for i in range(7)]
    
    # Store events by date
    daily_events = {d: [] for d in days_to_show}

    for component in cal.walk():
        if component.name == "VEVENT":
            dtstart = component.get('dtstart').dt
            
            # Handle both datetime and date objects from ical
            if isinstance(dtstart, datetime):
                event_date = dtstart.date()
                event_time = dtstart.strftime("%-I:%M %p")
            else:
                event_date = dtstart
                event_time = "All Day"

            if event_date in daily_events:
                daily_events[event_date].append({
                    "time": event_time,
                    "summary": component.get('summary'),
                    "location": component.get('location', '')
                })

    # --- UI LAYOUT ---
    cols = st.columns(7)

    for i, day in enumerate(days_to_show):
        with cols[i]:
            # Day Header
            st.markdown(f"### {day.strftime('%a')}")
            st.caption(day.strftime('%b %d'))
            
            # --- FUTURE WEATHER SLOT ---
            # st.write("☀️ 72°F") 
            st.divider()

            # Events for this day
            events = sorted(daily_events[day], key=lambda x: x['time'])
            
            if not events:
                st.write("*No events*")
            
            for event in events:
                with st.container():
                    st.markdown(f"**{event['time']}**")
                    st.write(event['summary'])
                    if event['location']:
                        st.caption(f"📍 {event['location']}")
                    st.divider()

if __name__ == "__main__":
    main()
