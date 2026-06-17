import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class TestConfig:
    def test_home_dir_matches_system(self):
        assert config.HOME_DIR == str(Path.home())

    def test_allowed_directories_under_home(self):
        for d in config.ALLOWED_DIRECTORIES:
            assert d.startswith(config.HOME_DIR), f"{d} is not under HOME_DIR"

    def test_data_dir_exists(self):
        assert config.DATA_DIR.exists()
        assert config.DATA_DIR.is_dir()

    def test_groq_api_key_loaded(self):
        assert isinstance(config.GROQ_API_KEY, str)

    def test_window_dimensions_positive(self):
        assert config.WINDOW_WIDTH > 0
        assert config.WINDOW_HEIGHT > 0

    def test_allowed_directories_not_empty(self):
        assert len(config.ALLOWED_DIRECTORIES) >= 1
