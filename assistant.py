from agno.agent import Agent
from agno.models.groq import Groq
from agno.db.sqlite import SqliteDb
import config
from tools import file_ops
from tools.web_search import web_search
from skills import load_skills


class AgnoAssistant:
    def __init__(self, write_confirm_callback=None):
        file_ops.write_confirm_callback = write_confirm_callback

        db = SqliteDb(db_file=str(config.DATA_DIR / "agent.db"))

        skills = load_skills()

        self.agent = Agent(
            model=Groq(
                id="meta-llama/llama-4-scout-17b-16e-instruct",
                api_key=config.GROQ_API_KEY,
                retry_with_guidance_limit=3,
            ),
            db=db,
            tools=[
                file_ops.read_file,
                file_ops.write_file,
                file_ops.list_directory,
                file_ops.search_files,
                web_search,
            ] + skills,
            update_memory_on_run=True,
            instructions=[
                "You are Jarvis, a helpful personal AI assistant running as a desktop popup app.",
                "Be concise and direct — the user is interacting via a small window.",
                f"The user's home directory is: {config.HOME_DIR}",
                f"You can access these directories: {', '.join(config.ALLOWED_DIRECTORIES)}",
                f"IMPORTANT: Always use FULL ABSOLUTE paths starting with {config.HOME_DIR}. Never use ~ or placeholder usernames.",
                "When the user asks you to remember something, confirm that you'll remember it.",
                "When creating files, always use absolute paths from the allowed directories listed above.",
                "Use the web_search tool for any question about current events, news, prices, or anything that needs up-to-date information.",
                "For weather questions, use the get_weather tool with the city name. If the user doesn't specify a city, ask them which city they want weather for.",
            ],
            markdown=True,
        )

    def chat_stream(self, message, on_chunk=None):
        full_text = ""
        try:
            response = self.agent.run(message, stream=True)
            for event in response:
                if event.content:
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
