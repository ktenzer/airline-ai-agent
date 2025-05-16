import os
import random
from datetime import datetime as dt
import dateparser
import stripe
from dotenv import load_dotenv
from temporalio import activity
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import tool, create_tool_calling_agent
from langchain_core.agents import AgentFinish, AgentAction
from typing import Any, Dict, List

# Load OpenAI key for agent
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize LLM
llm = ChatOpenAI(model="gpt-4", temperature=0, api_key=OPENAI_API_KEY)
# Load environment variables
stripe.api_key = os.getenv("STRIPE_API_KEY")

# Mock routes
MOCK_ROUTES = [
    {"origin": "LAX", "destination": "NYC"},
    {"origin": "LAX", "destination": "MUC"},
    {"origin": "LAX", "destination": "SFO"},
    {"origin": "LAX", "destination": "CDG"},
    {"origin": "LAX", "destination": "ORD"}
]

# Helper for date parsing
def parse_date(date_str: str) -> str:
    dt_obj = dateparser.parse(
        date_str,
        settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": dt.now()}
    )
    if not dt_obj:
        return None
    return dt_obj.strftime("%Y-%m-%d")

# Find flights activity
@activity.defn
async def find_flights(origin: str, destination: str, departure_date: str, return_date: str) -> Any:
    origin_code = origin.strip().upper()
    destination_code = destination.strip().upper()
    depart = parse_date(departure_date)
    ret = parse_date(return_date)
    if not depart or not ret:
        return {"error": "❌ Could not parse one or both dates."}
    valid = any(
        r["origin"] == origin_code and r["destination"] == destination_code
        for r in MOCK_ROUTES
    )
    if not valid:
        return {
            "error": "We currently only support mock routes from LAX to a few destinations.",
            "supported_destinations": [r["destination"] for r in MOCK_ROUTES if r["origin"] == "LAX"]
        }
    flights: List[Dict[str, Any]] = []
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
    return flights

# Book flight activity
@activity.defn
async def book_flight(flight_id: str, price: str) -> Any:
    try:
        amount = int(float(price.replace('$', '')) * 100)
    except ValueError:
        return {"error": "❌ Invalid price format."}
    try:
        customer = stripe.Customer.create(source="tok_visa")
        charge = stripe.Charge.create(
            amount=amount,
            currency='usd',
            description=f"Flight booking for {flight_id}",
            customer=customer.id
        )
        return {"receipt_url": charge.receipt_url}
    except Exception as e:
        return {"error": f"❌ Stripe error: {str(e)}"}

# Tools
@tool
def find_flights_tool(origin: str, destination: str, departure_date: str, return_date: str) -> AgentAction:
    """Plan the invocation for the find_flights activity."""
    return AgentAction(
        tool="find_flights_tool",
        tool_input={
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date
        }
    )

@tool
def book_flight_tool(flight_id: str, price: str) -> AgentAction:
    """Plan the invocation for the book_flight activity."""
    return AgentAction(
        tool="book_flight_tool",
        tool_input={"flight_id": flight_id, "price": price}
    )

TOOLS = [find_flights_tool, book_flight_tool]

# LLM Conversation
@activity.defn
async def run_agent(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Extract last user message
    last_input = next((h["message"] for h in reversed(history) if h["actor"] == "user"), None)
    if last_input is None:
        return []

    # Map to LangChain roles
    mapped_history: List[tuple[str, Any]] = []
    for msg in history:
        content = msg.get("message")
        if msg.get("actor") == "user":
            mapped_history.append(("user", content))
        elif msg.get("actor") == "llm":
            mapped_history.append(("assistant", content))
        elif msg.get("actor") == "tool":
            # Strip braces from observation
            c = str(content).replace("{", "").replace("}", "")
            mapped_history.append(("assistant", f"Observation: {c}"))

    # Build prompts
    prompt_content = [
        ("system", "You are an airline assistant, specializing in finding trips from the Los Angeles area. You understand that users may refer to airports by city names or typos; normalize names like 'New York', 'New York City' to 'NYC' and 'Los Angeles' to 'LAX'. Use IATA codes for routing decisions. Use tools when needed.")
    ] + mapped_history + [
        ("user", last_input),
        ("placeholder", "{agent_scratchpad}")
    ]
    prompt = ChatPromptTemplate.from_messages(prompt_content)
    agent = create_tool_calling_agent(llm=llm, tools=TOOLS, prompt=prompt)

    # Invoke with all vars
    result = agent.invoke({
        "input": last_input,
        "intermediate_steps": [],
        "error": "",
        "agent_scratchpad": ""
    })

    # Return LLM or tool event
    if isinstance(result, AgentFinish):
        return [{"actor": "llm", "message": result.return_values.get("output", "⚠️ No response")}]
    action = result[-1]
    return [{"actor": "tool", "tool": action.tool, "tool_input": action.tool_input}]