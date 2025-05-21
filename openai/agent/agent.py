from agents import Agent, function_tool
from agent_tools.find_flights import find_flights
from agent_tools.book_flight import book_flight

CITY_TO_IATA = {
    "new york": "NYC",
    "munich": "MUC",
    "san francisco": "SFO",
    "paris": "CDG",
    "chicago": "ORD",
}

@function_tool
def find_flights_tool(
    destination: str,
    departure_date: str,
    return_date: str,
    origin: str = "LAX",
) -> dict:
    """Find mock flights from LAX to supported destinations."""
    dest_code = CITY_TO_IATA.get(destination.strip().lower(), destination.strip().upper())
    return find_flights(origin, dest_code, departure_date, return_date)

@function_tool
def book_flight_tool(flight_id: str, price: str) -> dict:
    return book_flight(flight_id, price)

agent = Agent(
    name="LA Airline Agent",
    instructions="""
    You are a helpful airline assistant. All flights depart from LAX.

    1) When the user gives a city name, you may pass either the city name
    or its IATA code; the tool wrapper will translate it.

    2) After find_flights_tool returns, list each option as
    “Flight ID: N – $price” and ask the user to reply with just the ID
    number.

    3) When the next user turn is only that number, look it up in
    `flights` (in context) and call book_flight_tool(flight_id, price).

    4) If booking succeeds, reply with:
    ✅ Your flight is booked! Invoice: {invoice_url}
    """,
    tools=[find_flights_tool, book_flight_tool],
    model="gpt-4o",
)