import requests
from icalendar import Calendar

def merge():
    master_cal = Calendar()
    master_cal.add('prodid', '-//Family Sync//EN')
    master_cal.add('version', '2.0')

    with open("calendars.txt", "r") as f:
        lines = f.readlines()

    for line in lines:
        if ':' not in line: continue
        meta, url = line.strip().split(':', 1)
        name, emoji = meta.split('|', 1) if '|' in meta else (meta, "📅")
        
        try:
            res = requests.get(url.replace('webcal://', 'https://'))
            if res.status_code == 200:
                cal = Calendar.from_ical(res.content)
                for event in cal.walk('VEVENT'):
                    summary = event.get('summary', 'No Title')
                    # Tag the event with name and emoji
                    event['summary'] = f"{summary} ({name}) {emoji}"
                    # Ensure location is passed through
                    # (No changes needed to the object itself, it will copy over)
                    master_cal.add_component(event)
        except Exception as e:
            print(f"Error {name}: {e}")

    with open("family_master.ics", "wb") as f:
        f.write(master_cal.to_ical())

if __name__ == "__main__":
    merge()
    
