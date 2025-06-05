import requests
import time
import csv
import os
from datetime import datetime, timezone
import warnings

# Suppress urllib3 warning
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

# ——————————————
# 1) Replace the dynamic fetch logic with a fixed list of stop IDs:
# ——————————————
STOP_IDS = [
    "490008660N",  # Brixton Station
    "490008660M",  # Victoria Station (Grosvenor Gardens)
    "490000254E",  # Waterloo Station (Bus Station)
    "490000254F",  # Stratford Bus Station
    "490000254H",  # Elephant & Castle Bus Station
    "490009205H",  # Oxford Circus (Regent Street)
    "490008660S",  # Shepherd’s Bush Bus Station
    "490000235C",  # Clapham Junction (Bus Interchange)
    "490G000327",  # Camden Town Bus Station
    "490000047A",  # Lewisham Bus Station
]

# TfL API base URL
base_url = "https://api.tfl.gov.uk"

# ——————————————
# 2) Keep the helper functions for timetable lookups unchanged:
# ——————————————

def get_valid_stop_id(route_id, default_stop_id):
    sequence_url = f"{base_url}/Line/{route_id}/Route/Sequence/all"
    try:
        response = requests.get(sequence_url, timeout=10)
        response.raise_for_status()
        sequence = response.json()
        for section in sequence.get("orderedLineRoutes", []):
            for stop_point in section.get("naptanIds", []):
                if stop_point.startswith("490"):
                    return stop_point
        # No alternative stop found → return the default
        return default_stop_id
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch route sequence for {route_id}: {e}")
        return None
    finally:
        time.sleep(0.5)  # Sleep after each API call

def get_scheduled_times(route_id, stop_id):
    timetable_url = f"{base_url}/Line/{route_id}/Timetable/{stop_id}"
    try:
        response = requests.get(timetable_url, timeout=10)
        response.raise_for_status()
        timetable = response.json()
        schedules = timetable.get("timetable", {}).get("routes", [{}])[0].get("schedules", [])
        if not schedules:
            return []
        times = []
        for schedule in schedules:
            for journey in schedule.get("knownJourneys", []):
                arrival_time = f"{journey.get('hour')}:{journey.get('minute')}"
                times.append(arrival_time)
        return times
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch timetable for route {route_id} at stop {stop_id}: {e}")
        return []
    finally:
        time.sleep(2)  # Sleep after each API call

# ——————————————
# 3) Main logic: loop over our fixed STOP_IDS
# ——————————————
def fetch_bus_status():
    results = []

    for stop_id in STOP_IDS:
        arrivals_url = f"{base_url}/StopPoint/{stop_id}/Arrivals"
        try:
            resp = requests.get(arrivals_url, timeout=10)
            resp.raise_for_status()
            arrivals = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch arrivals for stop {stop_id}: {e}")
            arrivals = []  # <-- Important: set to empty list instead of None
            time.sleep(0.5)  # Sleep after failure too
            continue

        if not arrivals:
            print(f"No arrival data for stop {stop_id}.")
            time.sleep(0.5)
            continue

        # Process each arrival record:
        for arrival in arrivals:
            line_id = arrival.get("lineId", "N/A").upper()
            destination = arrival.get("destinationName", "N/A")
            vehicle_id = arrival.get("vehicleId", "N/A")
            expected_arrival = arrival.get("expectedArrival", "N/A")

            # Parse the expectedArrival timestamp into a datetime:
            try:
                actual_time = datetime.strptime(expected_arrival, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                print(f"Invalid arrival time for {line_id} at stop {stop_id}: {expected_arrival}")
                continue

            # Find a valid stop ID for timetable comparisons:
            valid_stop_id = get_valid_stop_id(line_id, stop_id)
            if not valid_stop_id:
                continue

            # Fetch scheduled times once per route/stop combo:
            scheduled_times = get_scheduled_times(line_id, valid_stop_id)
            if not scheduled_times:
                continue

            # Find the closest scheduled time to the actual arrival:
            closest_time = None
            min_delay = float("inf")
            current_date = actual_time.date()
            for sched_time in scheduled_times:
                try:
                    sched_dt = datetime.strptime(f"{current_date} {sched_time}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                    delay = (actual_time - sched_dt).total_seconds() / 60
                    if abs(delay) < abs(min_delay):
                        min_delay = delay
                        closest_time = sched_dt
                except ValueError:
                    continue

            if not closest_time:
                continue

            # On‐time if within ±5 minutes:
            on_time = "Yes" if abs(min_delay) <= 5 else "No"

            formatted_actual = actual_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            formatted_scheduled = closest_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            delay_min = f"{min_delay:.2f}"

            # Build the result dict:
            result = {
                "stop_id": stop_id,
                "route": line_id,
                "destination": destination,
                "vehicle_id": vehicle_id,
                "actual_arrival": formatted_actual,
                "scheduled_arrival": formatted_scheduled,
                "delay_minutes": delay_min,
                "on_time": on_time
            }
            results.append(result)

            # Print to console:
            print(f"Stop ID: {stop_id}")
            print(f"Route: {line_id}")
            print(f"Destination: {destination}")
            print(f"Vehicle ID: {vehicle_id}")
            print(f"Actual Arrival: {formatted_actual}")
            print(f"Scheduled Arrival: {formatted_scheduled}")
            print(f"Delay (minutes): {delay_min}")
            print(f"On Time: {on_time}")
            print("-" * 80)

        # Sleep between stop arrivals fetches
        time.sleep(5)

    return results






if __name__ == "__main__":
    fetch_bus_status()
