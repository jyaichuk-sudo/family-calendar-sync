import os
import requests
from icalendar import Calendar

def merge():
    # This pulls your hidden links from GitHub's vault
    links_raw = os.getenv("CALENDAR_LINKS", "")
    master_cal = Calendar()
    master_cal.add('prodid', '-//Family Sync//EN')
    master_cal.add('version', '2.0')

    for line in links_raw.strip().split('\n'):
        if ':' not in line: continue
        name, url = line.split(':', 1)
        url = url.replace('webcal://', 'https://').strip()
        
        try:
            res = requests.get(url)
            if res.status_code == 200:
                cal = Calendar.from_ical(res.content)
                for event in cal.walk('VEVENT'):
                    # Tagging the event so you know the source
                    event['summary'] = f"{event.get('summary')} ({name})"
                    master_cal.add_component(event)
                print(f"Synced {name}")
        except Exception as e:
            print(f"Error {name}: {e}")

    with open("family_master.ics", "wb") as f:
        f.write(master_cal.to_ical())

if __name__ == "__main__":
    merge()
  
