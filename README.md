# airline-ai-agent
I built an Airline AI Agent using Temporal, LangGraph and CrewAI to compare each other and understand some of the strenghts and weaknesses.

This AI Airline Agent speacializes in finding and booking flights from Los Angeles to select locations. It uses two tools: find_flights which provides mocked flight destinations (New york, Munich, San Francisco, Chicago and Paris) and book_flight which uses the Stripe API to create a test payment.

## Requirements
- OpenAI API Key
- Stripe API Key
- Temporal Cloud or Development Server

## Temporal
Sign up for Temporal Cloud or use local environment.
```bash
$ brew install temporal
$ temporal server start-dev
```

Install Poetry Dependencies
```bash
$ poetry install
```

Update .env
```bash
$ cd temporal
$ cp .env.example .env
```

Start Temporal Worker
```bash
$ poetry run python worker.py
```

Start UI
```bash
$ poetry run python ui.py
```

Chat UI Conversation
![Chat UI](/images/chat.png)

History
![History](/images/history.png)

## LangGraph
Install Poetry Dependencies
```bash
$ poetry install
```

Update .env
```bash
$ cd langgraph
$ cp .env.example .env
```

Start UI
```bash
$ poetry run python ui.py
```

## CrewAI
Install Poetry Dependencies
```bash
$ cd crewai
$ poetry install
```

Update .env
```bash
$ cp .env.example .env
```

Start UI
```bash
$ poetry run python ui.py
```

## OpenAI
Install Poetry Dependencies
```bash
$ poetry install
```

Update .env
```bash
$ cp .env.example .env
```

Start UI
```bash
$ poetry run python ui.py
```
