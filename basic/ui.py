import gradio as gr
from agent.agent import handle_message

WELCOME_TEXT = (
    "Welcome to LA Travels! 👋\n\n"
    "I'm your dedicated airline agent, specializing in travel to and from the Los Angeles area. "
    "To get started, please provide your destination city along with your preferred departure and "
    "return dates. I'll find you the best routes and prices available."
)

# Track history
chat_state = {
    "history": [],
}

def chat_agent(message, history):
    full_history = chat_state["history"]
    assistant_reply = handle_message(message, full_history)
    full_history.append({"role": "user", "content": message})
    full_history.append({"role": "assistant", "content": assistant_reply})
    return assistant_reply

iface = gr.ChatInterface(
    fn=chat_agent,
    title="Airline Agent AI (Pure Python)",
    description=WELCOME_TEXT,
    type="messages",
).queue()

iface.launch()