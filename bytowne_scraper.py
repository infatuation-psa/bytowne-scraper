import requests
from ics import Calendar, Event
from datetime import datetime, timezone
import json

FEED_URL = "https://tickets.bytowne.ca/websales/feed.ashx?guid=3e656b43-cd16-45ba-86a1-d2392fd70869&format=json&showslist=true"

def parse_bytowne():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print(f"Fetching JSON feed from {FEED_URL}...")
    response = requests.get(FEED_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch feed: HTTP {response.status_code}")
        return

    data = response.json()
    cal = Calendar()
    
    shows = data.get("CurrentShows", [])
    event_count = 0

    for show in shows:
        title = show.get("Name", "Untitled Film")
        
        for evt in show.get("Events", []):
            # Skip if date is TBD or start time is missing
            if evt.get("DateTBD") or not evt.get("StartDate"):
                continue

            # Parse start and end times (ISO 8601 strings, e.g. "2026-08-05T21:15:00")
            start_dt = datetime.fromisoformat(evt.get("StartDate"))
            
            if evt.get("EndDate"):
                end_dt = datetime.fromisoformat(evt.get("EndDate"))
            else:
                # Fallback to duration (in minutes) if EndDate isn't provided
                duration_mins = int(evt.get("Duration", 120))
                end_dt = start_dt + timedelta(minutes=duration_mins)

            # Extract Venue info
            venue_info = evt.get("Venue", {})
            venue_name = venue_info.get("Name", "ByTowne Cinema")
            address = venue_info.get("Address1", "325 Rideau Street")
            city = venue_info.get("City", "Ottawa")
            state = venue_info.get("State", "ON")
            zip_code = venue_info.get("Zip", "K1N 5Y4")
            
            full_location = f"{venue_name}, {address}, {city}, {state} {zip_code}"

            # Extract Description & Links
            description_text = evt.get("ShortDescription", "").strip()
            ticket_link = evt.get("LegacyPurchaseLink", "")
            
            # Build detailed description body
            description_body = f"{description_text}\n\n🎟️ Tickets: {ticket_link}" if ticket_link else description_text

            # Create iCal Event
            event = Event()
            event.name = f"🎬 {title}"
            event.begin = start_dt
            event.end = end_dt
            event.location = full_location
            event.description = description_body
            
            cal.events.add(event)
            event_count += 1
            print(f"Added: {title} on {start_dt.strftime('%Y-%m-%d %I:%M %p')}")

    print(f"\nTotal events added to calendar: {event_count}")

    # Write output to bytowne.ics
    with open("bytowne.ics", "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    parse_bytowne()
