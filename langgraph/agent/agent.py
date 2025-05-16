# agent/agent.py
import os
import json
from dotenv import load_dotenv
from typing import TypedDict, List, Any, Union
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import tool, create_tool_calling_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.agents import AgentFinish, AgentAction
from langchain_core.runnables import RunnableLambda

# Load environment variables
load_dotenv()

# === Tools ===
from agent_tools.find_flights import find_flights
from agent_tools.book_flight import book_flight

@tool
def find_flights_tool(origin: str, destination: str, departure_date: str, return_date: str):
    """Find mock flights from Los Angeles using IATA airport codes (e.g., LAX to NYC). Only LAX to NYC, MUC, SFO, CDG, ORD are supported."""
    return find_flights("LAX", destination, departure_date, return_date)

@tool
def book_flight_tool(flight_id: str, price: str):
    """Book a selected flight using Stripe API."""
    return book_flight(flight_id, price)

tools = [find_flights_tool, book_flight_tool]

# === LLM Setup ===
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# === Agent state ===
class AgentState(TypedDict):
    input: str
    output: Union[str, None]
    intermediate_steps: List[Any]
    history: List[dict]  # each dict is {role: user|assistant, content: str}

# === Agent logic node ===
def agent_node_fn(state: AgentState) -> AgentState:
    history = state.get("history", [])

    # Construct message history
    chat_messages = [
        ("system", "You are a helpful airline assistant. Help users book round-trip flights by asking clarifying questions and using tools.")
    ] + [(msg["role"], msg["content"]) for msg in history] + [
        ("user", state["input"]),
        ("placeholder", "{agent_scratchpad}")
    ]

    prompt = ChatPromptTemplate.from_messages(chat_messages)

    agent_with_prompt = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    result = agent_with_prompt.invoke({
        "input": state["input"],
        "intermediate_steps": state.get("intermediate_steps", [])
    })

    print("Agent result:", result)

    new_history = history + [{"role": "user", "content": state["input"]}]

    if isinstance(result, AgentFinish):
        output = result.return_values.get("output", "⚠️ No response")
        new_history.append({"role": "assistant", "content": output})
        return {
            **state,
            "output": output,
            "intermediate_steps": [],
            "history": new_history
        }

    elif isinstance(result, list):  # tool action
        return {
            **state,
            "output": "⏳ Working on your request...",
            "intermediate_steps": state["intermediate_steps"] + result,
            "history": new_history
        }

    return {
        **state,
        "output": "⚠️ Unexpected agent result",
        "history": new_history
    }

# === Tool executor node ===
def execute_tools(state: AgentState) -> AgentState:
    last_action = state["intermediate_steps"][-1]
    tool_name = last_action.tool
    tool_input = last_action.tool_input

    print(f"[TOOL EXECUTOR] Calling tool: {tool_name} with {tool_input}")

    for tool in tools:
        if tool.name == tool_name:
            observation = tool.invoke(tool_input)
            break
    else:
        observation = f"Tool {tool_name} not found."

    new_steps = state["intermediate_steps"][:-1] + [(last_action, observation)]

    return {
        **state,
        "output": None,
        "intermediate_steps": new_steps
    }

# === Graph ===
builder = StateGraph(state_schema=AgentState)
builder.add_node("agent", agent_node_fn)
builder.add_node("tool_executor", RunnableLambda(execute_tools))

# Updated router logic to prevent infinite loop
def router(state: AgentState):
    if state["output"] and state["output"].startswith("⏳"):
        return "tool_executor"
    return END

builder.set_entry_point("agent")
builder.add_conditional_edges(
    "agent",
    router,
    {"tool_executor", END}
)
builder.add_edge("tool_executor", "agent")
builder.set_finish_point("agent")

graph = builder.compile()