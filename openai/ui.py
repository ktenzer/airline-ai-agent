import gradio as gr
import asyncio, json
from agents import Runner
from agent.agent import agent

runner = Runner()

WELCOME_TEXT = (
    "Welcome to LA Travels! 👋\n\n"
    "I'm your dedicated airline agent for flights from LAX. "
    "Give me a destination city and travel dates, and I'll find flights. "
    "When you see the list, reply with just the Flight ID number to book."
)

# Conversation state
chat_state = {
    "flights": {},   
    "log": []    
}

# Chat handler
async def chat_agent(message: str, history):
    chat_state["log"].append(("user", message))

    context: dict = {}
    if chat_state["flights"]:
        context["flights"] = chat_state["flights"]
    transcript = "\n".join(f"{role.upper()}: {text}" for role, text in chat_state["log"]) + "\n"

    result = await runner.run(agent, input=transcript, context=context)
    reply = result.final_output

    for step in getattr(result, "steps", []):
        tool = getattr(step, "tool_name", "")
        output = getattr(step, "output", {}) or {}

        if tool == "find_flights_tool":
            flights = output.get("flights", [])
            if isinstance(flights, list) and flights:
                chat_state["flights"] = {str(f["id"]): f for f in flights}

        if tool == "book_flight_tool" and output.get("status") == "success":
            chat_state["flights"].clear()

    chat_state["log"].append(("assistant", reply))

    return reply

# UI
iface = gr.ChatInterface(
    fn=lambda m, h: asyncio.run(chat_agent(m, h)),
    title="Airline Agent AI (OpenAI Agent SDK)",
    description=WELCOME_TEXT,
    type="messages",
).queue()

iface.launch()