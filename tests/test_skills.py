import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.get_weather import run as get_weather


class TestGetWeather:
    @patch("skills.get_weather.DDGS")
    def test_returns_weather_results(self, mock_ddgs_cls):
        weather_results = [
            {"title": "London Weather", "body": "Partly cloudy, 18°C", "href": "https://weather.com"},
        ]
        mock_ddgs_cls.return_value.text.return_value = weather_results
        result = get_weather("London")
        assert "London Weather" in result
        assert "18°C" in result

    @patch("skills.get_weather.DDGS")
    def test_no_weather_results(self, mock_ddgs_cls):
        mock_ddgs_cls.return_value.text.return_value = []
        result = get_weather("Nonexistentville")
        assert "Could not find weather" in result

    @patch("skills.get_weather.DDGS")
    def test_handles_weather_error(self, mock_ddgs_cls):
        mock_ddgs_cls.return_value.text.side_effect = Exception("API down")
        result = get_weather("London")
        assert "Weather lookup error" in result

    @patch("skills.get_weather.DDGS")
    def test_query_includes_city_name(self, mock_ddgs_cls):
        mock_ddgs_cls.return_value.text.return_value = []
        get_weather("Tokyo")
        call_args = mock_ddgs_cls.return_value.text.call_args
        assert "Tokyo" in call_args[0][0]


class TestSkillLoader:
    def test_load_skills_finds_get_weather(self):
        from skills import load_skills
        skills = load_skills()
        names = [s.__name__ for s in skills]
        assert "get_weather" in names

    def test_loaded_skill_has_docstring(self):
        from skills import load_skills
        skills = load_skills()
        weather = [s for s in skills if s.__name__ == "get_weather"][0]
        assert "weather" in weather.__doc__.lower()
