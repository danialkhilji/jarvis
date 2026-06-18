import asyncio
import threading

from agno.agent import Agent
from agno.models.groq import Groq
from agno.db.sqlite import SqliteDb
from agno.run.agent import RunEvent
import config
from tools import file_ops
from tools.web_search import web_search
from skills import load_skills


class AgnoAssistant:
    def __init__(self, write_confirm_callback=None):
        file_ops.write_confirm_callback = write_confirm_callback

        db = SqliteDb(db_file=str(config.DATA_DIR / "agent.db"))
        skills = load_skills()

        all_tools = [
            file_ops.read_file,
            file_ops.write_file,
            file_ops.list_directory,
            file_ops.search_files,
            web_search,
        ] + skills

        self.agent = Agent(
            model=Groq(
                id="meta-llama/llama-4-scout-17b-16e-instruct",
                api_key=config.GROQ_API_KEY,
                retry_with_guidance_limit=3,
            ),
            db=db,
            tools=all_tools,
            stream_events=True,
            add_history_to_context=True,
            num_history_runs=10,
            instructions=[
                "You are JARVIS, a professional personal AI assistant inspired by Iron Man's J.A.R.V.I.S.",
                "Behavior: Address the user as 'Sir' when natural. Be concise, intelligent, calm, and proactive. Prefer action over lengthy explanations. Provide clear status updates when performing tasks. Only suggest next steps if genuinely necessary — do not pad responses. Avoid emojis, slang, and unnecessary verbosity.",
                f"Environment: Running as a desktop popup assistant. User home directory: {config.HOME_DIR}. Allowed directories: {', '.join(config.ALLOWED_DIRECTORIES)}.",
                f"Rules: Always use full absolute paths starting with {config.HOME_DIR}. Never use ~, relative paths, or placeholder usernames. When creating or modifying files, provide the absolute path. If the user asks you to remember something, respond: 'Understood, Sir. I'll remember that.' Use the web_search tool whenever current or time-sensitive information is required.",
                "Examples of tone: 'Certainly, Sir.' / 'Right away, Sir.' / 'Done, Sir.' / 'I've encountered an issue, Sir: [details]'",
            ],
            markdown=True,
        )

        # Persistent async event loop in a daemon thread (Tkinter mainloop is synchronous)
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True, name="jarvis-async").start()

    def chat_stream(self, message, on_chunk=None, on_tool_call=None):
        future = asyncio.run_coroutine_threadsafe(
            self._async_chat(message, on_chunk, on_tool_call), self._loop
        )
        return future.result()

    async def _async_chat(self, message, on_chunk=None, on_tool_call=None):
        full_text = ""
        try:
            async for event in self.agent.arun(message, stream=True):
                if event.event == RunEvent.tool_call_started.value:
                    if event.tool and on_tool_call:
                        on_tool_call(event.tool.tool_name, "started")
                elif event.event == RunEvent.tool_call_completed.value:
                    if event.tool and on_tool_call:
                        on_tool_call(event.tool.tool_name, "completed")
                elif event.event == RunEvent.tool_call_error.value:
                    if event.tool and on_tool_call:
                        on_tool_call(event.tool.tool_name, "error")
                elif event.event == RunEvent.run_content.value and event.content:
                    full_text += event.content
                    if on_chunk:
                        on_chunk(event.content)
        except Exception as e:
            error_msg = f"Error: {e}"
            if on_chunk:
                on_chunk(error_msg)
            full_text = error_msg
        return full_text

    def clear_conversation(self):
        self.agent.session_id = None
