import os
from dotenv import load_dotenv

from crewai import Agent, LLM
from crewai.tools import tool

from agent_tools.find_flights import find_flights
from agent_tools.book_flight  import book_flight

load_dotenv(override=True)

@tool("find_flights")
def find_flights_tool(origin: str, destination: str, departure_date: str, return_date: str):
    """
    Find flights from origin to destination.
    Args:
      origin: airport code (e.g. LAX)
      destination: airport code (e.g. NYC)
      departure_date: YYYY-MM-DD or natural language date
      return_date: YYYY-MM-DD or natural language date
    """
    return find_flights(origin, destination, departure_date, return_date)

@tool("book_flight")
def book_flight_tool(flight_id: str, price: str):
    """
    Book a flight given flight_id and price; returns invoice_url or error.
    """
    return book_flight(flight_id, price)

# configure your LLM
llm = LLM(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
)

agent = Agent(
    role="LA Travels Agent",
    goal=(
        "Step 1: find flights from LAX to the requested city and present them with IDs, prices, and dates. "
        "Step 2: once the user picks a flight ID, book it via Stripe."
    ),
    backstory=(
        "You’re an AI assistant for LA Travels.  When the user first asks for flights, "
        "you must call the `find_flights` tool.  After it returns options, list each flight "
        "with its ID, price, departure and return dates, and then ask “Which flight ID would you like to book?”  "
        "Only once the user responds with something like “Book flight 2 at 350.00” should you call the `book_flight` tool.  "
        "Do not ever initiate a booking before the user explicitly selects an ID."
    ),
    llm=llm,
    tools=[find_flights_tool, book_flight_tool],
    verbose=True,
)