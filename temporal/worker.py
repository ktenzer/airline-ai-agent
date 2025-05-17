import os
import asyncio
from temporalio.worker import Worker
from workflows import AgentWorkflow
from activities import find_flights, book_flight, run_agent
from agent_client import get_worker_client


async def main():
    client = await get_worker_client()

    worker = Worker(
        client,
        task_queue=os.getenv("TEMPORAL_TASK_QUEUE"),
        workflows=[AgentWorkflow],
        activities=[find_flights, book_flight, run_agent]
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())