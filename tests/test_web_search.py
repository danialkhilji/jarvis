import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.web_search import web_search

MOCK_RESULTS = [
    {"title": "Result One", "body": "First result body text.", "href": "https://example.com/1"},
    {"title": "Result Two", "body": "Second result body text.", "href": "https://example.com/2"},
]


class TestWebSearch:
    @patch("tools.web_search.DDGS")
    def test_returns_formatted_results(self, mock_ddgs_cls):
        mock_ddgs_cls.return_value.text.return_value = MOCK_RESULTS
        result = web_search("test query")
        assert "Result One" in result
        assert "Result Two" in result
        assert "https://example.com/1" in result

    @patch("tools.web_search.DDGS")
    def test_no_results(self, mock_ddgs_cls):
        mock_ddgs_cls.return_value.text.return_value = []
        result = web_search("obscure query")
        assert "No results found" in result

    @patch("tools.web_search.DDGS")
    def test_handles_api_error(self, mock_ddgs_cls):
        mock_ddgs_cls.return_value.text.side_effect = Exception("Network timeout")
        result = web_search("test query")
        assert "Search error" in result
        assert "Network timeout" in result
