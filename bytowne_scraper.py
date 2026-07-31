from datetime import datetime, timedelta
import requests
from ics import Calendar, Event

FEED_URL = "https://tickets.bytowne.ca/websales/feed.ashx?guid=3e656b43-cd16-45ba-86a1-d2392fd70869&format=json&showslist=true"


def fetch_and_build_ics():
  # Standard browser header to bypass default python-requests blocking
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  print(f"Fetching data from: {FEED_URL}")
  response = requests.get(FEED_URL, headers=headers, timeout=15)
  response.raise_for_status()

  data = response.json()

  # Handle Agile Ticketing JSON structure variants
  raw_events = []
  if isinstance(data, list):
    raw_events = data
  elif isinstance(data, dict):
    aoe = data.get("ArrayOfEvent", data)
    if isinstance(aoe, dict):
      raw_events = aoe.get("Event", [])
    elif isinstance(aoe, list):
      raw_events = aoe

  # Single item edge case
  if isinstance(raw_events, dict):
    raw_events = [raw_events]

  print(f"Extracted {len(raw_events)} raw events from feed.")

  cal = Calendar()

  for item in raw_events:
    if not isinstance(item, dict):
      continue

    title = item.get("Name") or item.get("EventName") or "ByTowne Movie"
    description = item.get("ShortDescription") or item.get("Description") or ""
    start_str = item.get("StartDate") or item.get("StartDateTime")

    if not start_str:
      continue

    # Parse ISO timestamp string
    try:
      # Clean trailing Z if present for naive datetime parsing
      clean_start = start_str.rstrip("Z")
      start_dt = datetime.fromisoformat(clean_start)
    except ValueError:
      continue

    # Estimate ~2h duration if no EndDate provided
    end_str = item.get("EndDate") or item.get("EndDateTime")
    if end_str:
      try:
        end_dt = datetime.fromisoformat(end_str.rstrip("Z"))
      except ValueError:
        end_dt = start_dt + timedelta(hours=2)
    else:
      end_dt = start_dt + timedelta(hours=2)

    event = Event()
    event.name = title
    event.begin = start_dt
    event.end = end_dt
    event.description = description
    event.location = "ByTowne Cinema, 325 Rideau St, Ottawa, ON"

    cal.events.add(event)

  print(f"Successfully generated ICS calendar with {len(cal.events)} events.")

  with open("bytowne.ics", "w", encoding="utf-8") as f:
    f.write(cal.serialize())


if __name__ == "__main__":
  fetch_and_build_ics()
