import os
import uuid
import asyncio
import gradio as gr
from temporalio.client import Client, WorkflowHandle
from workflows import AgentWorkflow
from agent_client import get_client  # async def get_client() -> Client

WORKFLOW_ID = "agent-session-" + str(uuid.uuid4())
workflow_handle: WorkflowHandle | None = None

# Welcome
WELCOME_TEXT = (
    "Welcome to LA Travels! 👋\n\n"
    "I'm your dedicated airline agent, specializing in travel to and from the Los Angeles area. "
    "To get started, please provide your destination city along with your preferred departure and "
    "return dates. I'll find you the best routes and prices available."
)

async def chat_agent(user_message, history):
    global workflow_handle, WORKFLOW_ID

    client: Client = await get_client()

    # Start or signal the workflow
    if workflow_handle is None:
        workflow_handle = await client.start_workflow(
            AgentWorkflow.run,
            id=WORKFLOW_ID,
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "airline-agent"),
            start_signal="user_message",
            start_signal_args=[user_message],
        )
    else:
        await workflow_handle.signal("user_message", user_message)

    # Wait for ready
    while not await workflow_handle.query("is_ready"):
        await asyncio.sleep(0.5)

    # Fetch history
    conv = await workflow_handle.query("get_history")
    assistant_message = ""

    for msg in reversed(conv):
        actor = msg.get("actor")
        content = msg.get("message")

        # Skip planning stubs if tool
        if (
            actor == "tool"
            and isinstance(content, dict)
            and "tool" in content
            and ("input" in content or "tool_input" in content)
        ):
            continue

        # Flight list
        if actor == "tool" and isinstance(content, list):
            lines = ["✈️ I found the following flights:"]
            for f in content:
                lines.append(
                    f"- Flight {f['id']}: {f['origin']}→{f['destination']}, "
                    f"{f['departure_date']}→{f['return_date']} at ${f['price']}"
                )
            assistant_message = "\n".join(lines)
            break

        # Booking confirmation
        if actor == "tool" and isinstance(content, dict):
            if "receipt_url" in content:
                assistant_message = f"✅ Your booking is confirmed! Receipt: {content['receipt_url']}"
                # Reset session for new booking
                workflow_handle = None
                WORKFLOW_ID = "agent-session-" + str(uuid.uuid4())
            else:
                assistant_message = content.get("error", str(content))
            break

        # LLM reply
        if actor == "llm":
            assistant_message = content
            break

    return {"text": assistant_message}

# UI Interface
iface = gr.ChatInterface(
    fn=chat_agent,
    title="Airline Agent AI (Temporal)",
    description=WELCOME_TEXT,
    type="messages",
).queue()

iface.launch()
