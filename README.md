# Jarvis

A desktop popup AI assistant for macOS built with Python. Uses Groq's free API with the Agno framework for tool calling, memory, and streaming responses.

## Features

- Chat popup window with dark theme
- File operations (read, write, list, search) with directory sandboxing
- Web search via DuckDuckGo
- Weather lookup
- Conversation memory across sessions
- Streaming responses

## Setup

### 1. Install dependencies

```bash
conda activate ai_agents
pip install -r requirements.txt
```

### 2. Add your API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key at https://console.groq.com

### 3. Run the app

```bash
python main.py
```

## File Access

The assistant can only access files in these directories:

- `~/Documents`
- `~/Desktop`
- `~/Downloads`
- `~/Library/CloudStorage`

## Running Tests

Install pytest if you haven't already:

```bash
pip install pytest
```

Run unit tests (fast, no API key needed):

```bash
pytest tests/ -m "not integration" -v
```

Run integration tests (requires `GROQ_API_KEY`):

```bash
pytest tests/ -m integration -v
```

Run all tests:

```bash
pytest tests/ -v
```

## Project Structure

```
ai_assistant/
├── main.py            # Entry point
├── assistant.py       # Agno agent wrapper
├── config.py          # Configuration
├── .env               # API key (not committed)
├── tools/
│   ├── file_ops.py    # File read/write/list/search
│   └── web_search.py  # Web search and weather
├── ui/
│   ├── popup.py       # Chat window
│   └── theme.py       # Dark theme colors
├── tests/
│   ├── test_config.py
│   ├── test_file_ops.py
│   ├── test_web_search.py
│   └── test_assistant_integration.py
└── data/              # SQLite databases (auto-created)
```
