import requests
from ics import Calendar, Event
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

FEED_URL = "https://tickets.bytowne.ca/websales/feed.ashx?guid=3e656b43-cd16-45ba-86a1-d2392fd70869&format=json&showslist=true&"
LOCAL_TZ = ZoneInfo("America/Toronto")

def fetch_and_build_ics():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"Fetching data from: {FEED_URL}")
    response = requests.get(FEED_URL, headers=headers, timeout=15)
    response.raise_for_status()

    data = response.json()
    shows = data.get("ArrayOfShows", [])
    
    cal = Calendar()
    event_count = 0

    for show in shows:
        if not isinstance(show, dict):
            continue

        show_title = show.get("Name", "ByTowne Movie")
        show_description = show.get("ShortDescription", "").strip()
        info_link = show.get("InfoLink", "")
        showings = show.get("CurrentShowings", [])

        for showing in showings:
            if not isinstance(showing, dict):
                continue

            start_str = showing.get("StartDate")
            if not start_str or showing.get("DateTBD"):
                continue

            try:
                # Parse naive datetime and attach local timezone explicitly
                naive_start = datetime.fromisoformat(start_str)
                start_dt = naive_start.replace(tzinfo=LOCAL_TZ)
            except ValueError:
                continue

            # Handle EndDate or Duration
            end_str = showing.get("EndDate")
            duration_mins = showing.get("Duration")

            if end_str:
                try:
                    naive_end = datetime.fromisoformat(end_str)
                    end_dt = naive_end.replace(tzinfo=LOCAL_TZ)
                except ValueError:
                    end_dt = start_dt + timedelta(hours=2)
            elif duration_mins and duration_mins.isdigit():
                end_dt = start_dt + timedelta(minutes=int(duration_mins))
            else:
                end_dt = start_dt + timedelta(hours=2)

            # Build location
            venue = showing.get("Venue", {})
            venue_name = venue.get("Name", "ByTowne Cinema")
            address = venue.get("Address1", "325 Rideau Street")
            city = venue.get("City", "Ottawa")
            state = venue.get("State", "ON")
            zip_code = venue.get("Zip", "K1N 5Y4")
            full_location = f"{venue_name}, {address}, {city}, {state} {zip_code}"

            buy_link = showing.get("LegacyPurchaseLink", "")
            full_description = showing.get("ShortDescription", "").strip() or show_description
            if buy_link:
                full_description += f"\n\n🎟️ Tickets: {buy_link}"
            if info_link:
                full_description += f"\nℹ️ Info: {info_link}"

            event = Event()
            event.name = f"🎬 {show_title}"
            event.begin = start_dt
            event.end = end_dt
            event.description = full_description
            event.location = full_location

            cal.events.add(event)
            event_count += 1

    print(f"Successfully generated ICS calendar with {event_count} total showtimes.")

    with open("bytowne.ics", "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    fetch_and_build_ics()
