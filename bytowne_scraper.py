import requests
from ics import Calendar, Event
from datetime import datetime, timedelta

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
    
    # The list of showtimes is stored directly under 'ArrayOfEvent'
    events_list = data.get("ArrayOfEvent", [])
    event_count = 0

    for item in events_list:
        title = item.get("Name", "Untitled Film")
        
        # Skip if date is TBD or start date is missing
        if item.get("DateTBD") or not item.get("StartDate"):
            continue

        # Parse start and end times
        start_dt = datetime.fromisoformat(item.get("StartDate"))
        
        if item.get("EndDate"):
            end_dt = datetime.fromisoformat(item.get("EndDate"))
        else:
            # Fallback to 2-hour duration if EndDate missing
            end_dt = start_dt + timedelta(hours=2)

        # Extract Venue details
        venue_info = item.get("Venue", {})
        venue_name = venue_info.get("Name", "ByTowne Cinema")
        address = venue_info.get("Address1", "325 Rideau Street")
        city = venue_info.get("City", "Ottawa")
        state = venue_info.get("State", "ON")
        zip_code = venue_info.get("Zip", "K1N 5Y4")
        
        full_location = f"{venue_name}, {address}, {city}, {state} {zip_code}"

        # Extract Description & Buy Links
        description_text = item.get("ShortDescription", "").strip()
        buy_link = item.get("BuyLink", "")
        info_link = item.get("InfoLink", "")
        
        # Format clean body text with links
        description_body = description_text
        if buy_link:
            description_body += f"\n\n🎟️ Tickets: {buy_link}"
        if info_link:
            description_body += f"\nℹ️ Info: {info_link}"

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
