import random
import datetime
import dateparser

MOCK_ROUTES = [
    {"origin": "LAX", "destination": "NYC"},
    {"origin": "LAX", "destination": "MUC"},
    {"origin": "LAX", "destination": "SFO"},
    {"origin": "LAX", "destination": "CDG"},
    {"origin": "LAX", "destination": "ORD"}
]

def parse_date(date_str: str) -> str:
    dt = dateparser.parse(
        date_str,
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.datetime.now()
        }
    )
    if not dt:
        return None

    return dt.strftime("%Y-%m-%d")

def find_flights(origin: str, destination: str, departure_date: str, return_date: str):
    print(f"[find_flights] Called with: {origin=}, {destination=}, {departure_date=}, {return_date=}")

    origin_code = origin.strip().upper()
    destination_code = destination.strip().upper()
    depart = parse_date(departure_date)
    ret = parse_date(return_date)

    print(f"[find_flights] Parsed dates: {depart=} {ret=}")

    if not depart or not ret:
        return {"error": "Could not parse one or both dates."}

    valid_route = any(
        route["origin"] == origin_code and route["destination"] == destination_code
        for route in MOCK_ROUTES
    )

    if not valid_route:
        print(f"[find_flights] Invalid route {origin_code}->{destination_code}")
        return {
            "error": "We currently only support mock routes from LAX to a few destinations.",
            "supported_destinations": [r["destination"] for r in MOCK_ROUTES if r["origin"] == "LAX"]
        }

    flights = []
    for i in range(1, 4):
        price = round(random.uniform(300, 500), 2)
        flights.append({
            "id": str(i),
            "origin": origin_code,
            "destination": destination_code,
            "departure_date": depart,
            "return_date": ret,
            "price": f"{price:.2f}",
            "currency": "USD"
        })

    print(f"[find_flights] Returning {len(flights)} flights")
    return flights