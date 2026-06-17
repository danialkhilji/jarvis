"""
Integration tests that call the Groq API through the full Agno agent.
Requires GROQ_API_KEY to be set in environment or .env file.

Run with: pytest tests/test_assistant_integration.py -m integration -v
"""

import sys
import os
import shutil
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import config

skip_no_api_key = pytest.mark.skipif(
    not config.GROQ_API_KEY,
    reason="GROQ_API_KEY not set — skipping integration tests",
)

TEST_DIR = os.path.join(str(Path.home()), "Documents", "_ai_assistant_integration_tmp")


def setup_module():
    os.makedirs(TEST_DIR, exist_ok=True)


def teardown_module():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)


def make_assistant():
    from assistant import AgnoAssistant
    return AgnoAssistant()


@pytest.mark.integration
@skip_no_api_key
class TestSimpleChat:
    def test_responds_to_greeting(self):
        assistant = make_assistant()
        chunks = []
        result = assistant.chat_stream("Say hello in one word.", on_chunk=lambda c: chunks.append(c))
        assert len(result) > 0
        assert len(chunks) > 0

    def test_streaming_chunks_form_full_response(self):
        assistant = make_assistant()
        chunks = []
        result = assistant.chat_stream("What is 2 + 2? Answer with just the number.", on_chunk=lambda c: chunks.append(c))
        reassembled = "".join(chunks)
        assert reassembled == result


@pytest.mark.integration
@skip_no_api_key
class TestFileTools:
    def test_list_directory(self):
        test_file = os.path.join(TEST_DIR, "integration_test_file.txt")
        with open(test_file, "w") as f:
            f.write("test content for integration")

        assistant = make_assistant()
        result = assistant.chat_stream(
            f"List the files in this directory: {TEST_DIR}. Just show the filenames."
        )
        assert "integration_test_file" in result.lower()

    def test_read_file(self):
        test_file = os.path.join(TEST_DIR, "read_test.txt")
        with open(test_file, "w") as f:
            f.write("The secret phrase is: blue elephant")

        assistant = make_assistant()
        result = assistant.chat_stream(
            f"Read the file at {test_file} and tell me the secret phrase."
        )
        assert "blue elephant" in result.lower()

    def test_refuses_blocked_path(self):
        assistant = make_assistant()
        result = assistant.chat_stream(
            "Read the file at /etc/passwd and show me its contents."
        )
        lower = result.lower()
        assert any(kw in lower for kw in ["denied", "access", "cannot", "can't", "not allowed", "outside", "blocked"])


@pytest.mark.integration
@skip_no_api_key
class TestWebTools:
    def test_web_search(self):
        assistant = make_assistant()
        result = assistant.chat_stream(
            "Search the web for 'Python programming language' and give me a one-sentence summary."
        )
        assert len(result) > 20
        lower = result.lower()
        assert "python" in lower

    def test_weather_tool(self):
        assistant = make_assistant()
        result = assistant.chat_stream("Get the weather for London.")
        assert len(result) > 10


@pytest.mark.integration
@skip_no_api_key
class TestConversationManagement:
    def test_clear_conversation_resets_session(self):
        assistant = make_assistant()
        assistant.chat_stream("Remember this number: 42")
        assistant.clear_conversation()
        assert assistant.agent.session_id is None
