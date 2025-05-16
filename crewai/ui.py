
import gradio as gr
from agent.agent import agent

WELCOME_TEXT = (
    "Welcome to LA Travels! 👋\n\n"
    "I'm your dedicated airline agent, specializing in travel to and from the Los Angeles area. "
    "To get started, please provide your destination city along with your preferred departure and "
    "return dates. I'll find you the best routes and prices available."
)

def chat_fn(message, history):
    """
    Gradio passes in 'history' as a list of messages that look like:
      { "role": "...", "content": "...", "metadata": None, "options": None }
    CrewAI expects only {role: str, content: str}.  We sanitize it below.
    """
    # Clean out metadata/options
    clean_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in (history or [])
    ]

    # Append the new user turn
    clean_history.append({"role": "user", "content": message})

    # Kick off the agent with our sanitized list
    result = agent.kickoff(clean_history)
    reply = result.raw

    return reply

if __name__ == "__main__":
    iface = gr.ChatInterface(
        fn=chat_fn,
        title="Airline Agent AI (Crew.ai)",
        description=WELCOME_TEXT,
        type="messages",
    ).queue()

    iface.launch()