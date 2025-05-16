import gradio as gr
from agent.agent import graph

# Welcome
WELCOME_TEXT = (
    "Welcome to LA Travels! 👋\n\n"
    "I'm your dedicated airline agent, specializing in travel to and from the Los Angeles area. "
    "To get started, please provide your destination city along with your preferred departure and "
    "return dates. I'll find you the best routes and prices available."
)

# Store conversation state between turns
chat_state = {
    "intermediate_steps": []
}

def chat_agent(message, history):
    result = graph.invoke({
        "input": message,
        "output": None,
        "intermediate_steps": [],
        "history": history 
    })
    print("DEBUG RESULT:", result) 

    # Update memory
    chat_state["intermediate_steps"] = result.get("intermediate_steps", [])
    return result.get("output", "Sorry, something went wrong.")

iface = gr.ChatInterface(
    fn=chat_agent,
    title="Airline Agent AI (LangGraph)",
    description=WELCOME_TEXT,
    type="messages",
).queue()
iface.launch()