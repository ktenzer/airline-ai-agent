import os
import openai
from dotenv import load_dotenv
from agent_tools.find_flights import find_flights
from agent_tools.book_flight import book_flight
import json

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.base_url = "http://localhost:10501/v1/"  

tools = {
    "find_flights": find_flights,
    "book_flight": book_flight
}

function_specs = [
    {
        "type": "function",
        "function": {
            "name": "find_flights",
            "description": "Find mock flights from Los Angeles using IATA airport codes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "departure_date": {"type": "string"},
                    "return_date": {"type": "string"}
                },
                "required": ["origin", "destination", "departure_date", "return_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": "Book a selected flight using Stripe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_id": {"type": "string"},
                    "price": {"type": "string"}
                },
                "required": ["flight_id", "price"]
            }
        }
    }
]

def call_openai(messages):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=function_specs,
        tool_choice="auto"
    )
    return response

def handle_message(message, history):
    messages = [
        {"role": "system", "content": "You are a helpful airline assistant. Help users book round-trip flights by asking clarifying questions and using tools."}
    ] + history + [{"role": "user", "content": message}]

    response = call_openai(messages)
    choice = response.choices[0].message

    if choice.tool_calls:
        tool_call = choice.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        if tool_name in tools:
            result = tools[tool_name](**tool_args)
            print(f"[TOOL RESULT] {tool_name}: {result}")
            # Append function call and result to history
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tool_call]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(result)
            })
            second_response = call_openai(messages)
            return second_response.choices[0].message.content
        else:
            return f"⚠️ Unknown tool: {tool_name}"

    return choice.content or "⚠️ No response"