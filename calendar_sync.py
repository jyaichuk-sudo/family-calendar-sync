import requests
from icalendar import Calendar

def merge():
    master_cal = Calendar()
    master_cal.add('prodid', '-//Family Sync//EN')
    master_cal.add('version', '2.0')

    # Now reading from your new text file
    try:
        with open("calendars.txt", "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Error: calendars.txt not found.")
        return

    for line in lines:
        line = line.strip()
        if not line or ':' not in line: continue
        
        name, url = line.split(':', 1)
        url = url.replace('webcal://', 'https://').strip()
        
        try:
            res = requests.get(url)
            if res.status_code == 200:
                cal = Calendar.from_ical(res.content)
                for event in cal.walk('VEVENT'):
                    # Keeps the source name in brackets
                    summary = event.get('summary', 'No Title')
                    event['summary'] = f"{summary} ({name})"
                    master_cal.add_component(event)
                print(f"✅ Synced {name}")
        except Exception as e:
            print(f"❌ Error {name}: {e}")

    with open("family_master.ics", "wb") as f:
        f.write(master_cal.to_ical())

if __name__ == "__main__":
    merge()
    
