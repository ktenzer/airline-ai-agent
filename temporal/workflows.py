from temporalio import workflow
from datetime import timedelta
from typing import List, Dict, Any

with workflow.unsafe.imports_passed_through():
    from activities import (
        run_agent,
        find_flights,
        book_flight
    )

# Agent Workflow
@workflow.defn
class AgentWorkflow:
    def __init__(self):
        # Pending user messages
        self._pending: List[str] = []
        # Full conversation history
        self.history: List[Dict[str, Any]] = []
        # Ready flag for UI polling
        self.ready: bool = True

    @workflow.run
    async def run(self):
        while True:
            # Wait for next user turn
            await workflow.wait_condition(lambda: len(self._pending) > 0)
            user_msg = self._pending.pop(0)

            self.ready = False
            self.history.append({"actor": "user", "message": user_msg})

            # Get planner decision
            events = await workflow.execute_activity(
                run_agent,
                args=(self.history,),
                start_to_close_timeout=timedelta(seconds=30),
            )
            evt = events[0]

            if evt.get("actor") == "tool":
                tool_name = evt["tool"]
                tool_input = evt.get("tool_input", {})

                # Record the plan
                self.history.append({
                    "actor": "tool",
                    "message": {"tool": tool_name, "input": tool_input}
                })

                # Execute Tool via activity
                if tool_name == "find_flights_tool":
                    obs = await workflow.execute_activity(
                        find_flights,
                        args=(
                            tool_input["origin"],
                            tool_input["destination"],
                            tool_input["departure_date"],
                            tool_input["return_date"],
                        ),
                        schedule_to_close_timeout=timedelta(seconds=30),
                    )
                    # Record the flights list
                    self.history.append({"actor": "tool", "message": obs})

                    # Get an LLM follow-up and continue
                    llm_events = await workflow.execute_activity(
                        run_agent,
                        args=(self.history,),
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                    for e in llm_events:
                        self.history.append(e)

                elif tool_name == "book_flight_tool":
                    obs = await workflow.execute_activity(
                        book_flight,
                        args=(
                            tool_input["flight_id"],
                            tool_input["price"],
                        ),
                        schedule_to_close_timeout=timedelta(seconds=30),
                    )
                    # Record booking result
                    self.history.append({"actor": "tool", "message": obs})

                    # Complete workflow after booking
                    self.ready = True
                    return

                else:
                    # Tool unknown
                    obs = {"error": f"Unknown tool: {tool_name}"}
                    self.history.append({"actor": "tool", "message": obs})

            else:
                # LLM reply
                self.history.append(evt)

            self.ready = True

    @workflow.signal
    def user_message(self, msg: str) -> None:
        """Signal handler to enqueue a new user message."""
        self._pending.append(msg)

    @workflow.query
    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieve the full conversation history."""
        return self.history

    @workflow.query
    def is_ready(self) -> bool:
        """Check if the workflow is ready for the next user message."""
        return self.ready