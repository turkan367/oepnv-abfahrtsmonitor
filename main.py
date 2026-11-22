from datetime import datetime
from zoneinfo import ZoneInfo
import json
import requests
from fastapi import FastAPI

app = FastAPI()

VRR_API = "https://openservice.vrr.de/openservice/XML_DM_REQUEST"
GERMANY = ZoneInfo("Europe/Berlin")

@app.get("/departures")
def get_departures():
    params = {
        "outputFormat": "rapidJSON",
        "place_dm": "Dortmund",
        "type_dm": "stop",
        "name_dm": "Hbf",
        "mode": "direct"
    }

    response = requests.get(VRR_API, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    departures = []

    for event in data.get("stopEvents", []):
        transport = event["transportation"]

        departure_time = (
            event.get("departureTimeEstimated")
            or event["departureTimePlanned"]
        )

        departure = datetime.fromisoformat(
            departure_time.replace("Z", "+00:00")
        ).astimezone(GERMANY)

        minutes = max(
            0,
            int((departure - datetime.now(GERMANY)).total_seconds() / 60)
        )

        departures.append({
            "line": transport.get("number", transport["name"]),
            "destination": transport["destination"]["name"],
            "departure": departure.strftime("%H:%M"),
            "minutes": minutes
        })

    return departures

@app.get("/stops")
def get_stops(search: str = ""):
    params = {"limit": 20}

    if search.strip():
        params["where"] = (
            f"search(objektname, {json.dumps(search.strip(), ensure_ascii=False)})"
        )

    response = requests.get(
        DORTMUND_API,
        params=params,
        timeout=10
    )
    response.raise_for_status()

    data = response.json()

    stops = []

    for stop in data["results"]:
        stops.append({
            "name": stop["objektname"],
            "lines": stop["i_zusinfo"],
            "location": stop["geo_point_2d"]
        })

    return stops