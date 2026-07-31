import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from dateutil import parser
from datetime import datetime, timedelta
import re

# Agile Ticketing direct list endpoint for ByTowne Cinema
SCHEDULE_URL = "https://tickets.bytowne.ca/websales/pages/list.aspx?epguid=3e656b43-cd16-45ba-86a1-d2392fd70869&"

def parse_bytowne():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Fetching showtimes from {SCHEDULE_URL}...")
    response = requests.get(SCHEDULE_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to load page, HTTP status: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    cal = Calendar()
    current_year = datetime.now().year
    
    # Extract page text line by line to reliably capture Date -> Film -> Time streams
    text_content = soup.get_text(separator="\n")
    lines = [line.strip() for line in text_content.split("\n") if line.strip()]
    
    current_date_str = None
    event_count = 0

    # Match dates like "Friday Jul 24th", "Saturday Jul 25th", "Sunday Aug 2nd"
    date_pattern = re.compile(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+([A-Za-z]{3})\s+(\d{1,2})(?:st|nd|rd|th)?', re.IGNORECASE)
    
    # Match showtimes like "7:00 PM", "12:45 PM", "9:30 PM"
    time_pattern = re.compile(r'^(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))$')

    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line is a Date Header
        date_match = date_pattern.match(line)
        if date_match:
            # Reconstruct clean date string e.g. "Jul 24 2026"
            month = date_match.group(2)
            day = date_match.group(3)
            current_date_str = f"{month} {day} {current_year}"
            i += 1
            continue

        # If we have an active date context, look for Film Title + Showtime pairs
        if current_date_str and i + 1 < len(lines):
            possible_title = line
            possible_time = lines[i + 1]

            time_match = time_pattern.match(possible_time)
            if time_match:
                # Ignore non-film UI text
                if possible_title not in ["More", "Buy Tickets", "Sign In", "Cart"]:
                    raw_time = time_match.group(1)
                    full_datetime_str = f"{current_date_str} {raw_time}"
                    
                    try:
                        start_dt = parser.parse(full_datetime_str)
                        end_dt = start_dt + timedelta(hours=2) # Estimate 2 hr runtime

                        event = Event()
                        event.name = f"🎬 {possible_title}"
                        event.begin = start_dt
                        event.end = end_dt
                        event.location = "ByTowne Cinema, 325 Rideau St, Ottawa, ON K1N 5Y4"
                        event.description = "ByTowne Cinema Screening"
                        
                        cal.events.add(event)
                        event_count += 1
                        print(f"Added: {possible_title} on {full_datetime_str}")
                    except Exception as e:
                        print(f"Error parsing date '{full_datetime_str}': {e}")
                
                i += 2
                continue

        i += 1

    print(f"\nTotal events added to calendar: {event_count}")

    # Write output to bytowne.ics
    with open("bytowne.ics", "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    parse_bytowne()
