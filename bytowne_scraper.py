import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from dateutil import parser
from datetime import datetime, timedelta

# ByTowne's direct ticketing schedule endpoint
SCHEDULE_URL = "https://tickets.bytowne.ca/websales/pages/list.aspx?epguid=3e656b43-cd16-45ba-86a1-d2392fd70869&"

def parse_bytowne():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(SCHEDULE_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    cal = Calendar()
    
    # ByTowne structures their online schedule as a calendar grid or item list
    # Look for table/container cells containing days and film links
    day_cells = soup.find_all(["td", "div"], class_=lambda c: c and ("Day" in c or "Calendar" in c or "Date" in c))
    
    # Fallback to general link parsing if class structure shifts slightly
    # The site uses structured elements with film names and time strings (e.g., "7:00 PM")
    film_entries = soup.find_all("a", href=lambda h: h and "details.aspx" in h)
    
    current_year = datetime.now().year

    for entry in film_entries:
        # Get film title
        title = entry.get_text(strip=True)
        if not title or title.lower() == "more":
            continue
            
        # The parent or sibling elements contain the date & time strings
        parent = entry.parent
        time_text = parent.get_text(" ", strip=True)
        
        # Example extracted string: "Friday Jul 3rd Couture 4:00 PM"
        # We parse out the time string (e.g. "4:00 PM") and date context
        try:
            # Locate time patterns like "7:00 PM" or "1:30 PM"
            import re
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', time_text)
            date_match = re.search(r'([A-Za-z]+\s+[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?)', time_text)
            
            if time_match and date_match:
                raw_date = date_match.group(1)
                raw_time = time_match.group(1)
                
                # Combine into ISO format
                full_datetime_str = f"{raw_date} {current_year} {raw_time}"
                start_dt = parser.parse(full_datetime_str)
                
                # Assume standard film duration ~ 2 hours
                end_dt = start_dt + timedelta(hours=2)

                event = Event()
                event.name = f"🎬 {title}"
                event.begin = start_dt
                event.end = end_dt
                event.location = "ByTowne Cinema, 325 Rideau St, Ottawa, ON K1N 5Y4"
                event.description = "ByTowne Cinema Screening"
                
                cal.events.add(event)
        except Exception:
            continue

    # Export to .ics format
    with open("bytowne.ics", "w") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    parse_bytowne()
