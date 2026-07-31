import requests
from ics import Calendar, Event
from datetime import datetime, timedelta

# ByTowne's exact Agile Tix JSON Feed URL
FEED_URL = "https://tickets.bytowne.ca/websales/feed.ashx?guid=3e656b43-cd16-45ba-86a1-d2392fd70869&format=json&showslist=true&"

def fetch_and_build_ics():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"Fetching data from: {FEED_URL}")
    response = requests.get(FEED_URL, headers=headers, timeout=15)
    response.raise_for_status()

    data = response.json()

    # Dig into Agile Ticketing's exact nested JSON structure:
    # Root -> "ArrayOfEvent" -> "Event" -> [ List of Event objects ]
    raw_events = []
    
    if isinstance(data, dict):
        array_of_event = data.get("ArrayOfEvent", {})
        if isinstance(array_of_event, dict):
            raw_events = array_of_event.get("Event", [])
        elif isinstance(array_of_event, list):
            raw_events = array_of_event

    # If Agile returns a single event object instead of a list
    if isinstance(raw_events, dict):
        raw_events = [raw_events]

    print(f"Extracted {len(raw_events)} raw events from feed.")

    cal = Calendar()

    for item in raw_events:
        if not isinstance(item, dict):
            continue

        title = item.get("Name", "ByTowne Movie")
        description = item.get("ShortDescription", "").strip()
        start_str = item.get("StartDate")
        
        # Skip if start time is missing or TBD
        if not start_str or item.get("DateTBD"):
            continue

        try:
            start_dt = datetime.fromisoformat(start_str.rstrip("Z"))
        except ValueError:
            continue

        # End date handling
        end_str = item.get("EndDate")
        if end_str:
            try:
                end_dt = datetime.fromisoformat(end_str.rstrip("Z"))
            except ValueError:
                end_dt = start_dt + timedelta(hours=2)
        else:
            end_dt = start_dt + timedelta(hours=2)

        # Build location
        venue = item.get("Venue", {})
        venue_name = venue.get("Name", "ByTowne Cinema")
        address = venue.get("Address1", "325 Rideau Street")
        city = venue.get("City", "Ottawa")
        state = venue.get("State", "ON")
        zip_code = venue.get("Zip", "K1N 5Y4")
        full_location = f"{venue_name}, {address}, {city}, {state} {zip_code}"

        # Build links
        buy_link = item.get("BuyLink", "")
        info_link = item.get("InfoLink", "")
        
        full_description = description
        if buy_link:
            full_description += f"\n\n🎟️ Tickets: {buy_link}"
        if info_link:
            full_description += f"\nℹ️ Info: {info_link}"

        # Create iCal event
        event = Event()
        event.name = f"🎬 {title}"
        event.begin = start_dt
        event.end = end_dt
        event.description = full_description
        event.location = full_location

        cal.events.add(event)

    print(f"Successfully generated ICS calendar with {len(cal.events)} events.")

    with open("bytowne.ics", "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    fetch_and_build_ics()
