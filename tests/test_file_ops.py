import sys
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from tools import file_ops
from tools.file_ops import (
    _resolve_path,
    _is_path_allowed,
    read_file,
    write_file,
    list_directory,
    search_files,
)

TEST_DIR = os.path.join(str(Path.home()), "Documents", "_ai_assistant_test_tmp")


def setup_module():
    os.makedirs(TEST_DIR, exist_ok=True)
    file_ops.write_confirm_callback = None


def teardown_module():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)


class TestResolvePath:
    def test_expands_tilde(self):
        result = _resolve_path("~/Documents")
        assert result == os.path.join(str(Path.home()), "Documents")

    def test_absolute_path_unchanged(self):
        path = os.path.join(str(Path.home()), "Documents", "test.txt")
        assert _resolve_path(path) == path

    def test_resolves_to_absolute(self):
        result = _resolve_path("relative/path.txt")
        assert os.path.isabs(result)


class TestIsPathAllowed:
    def test_allowed_directory(self):
        path = os.path.join(str(Path.home()), "Documents", "file.txt")
        assert _is_path_allowed(path) is True

    def test_desktop_allowed(self):
        path = os.path.join(str(Path.home()), "Desktop", "file.txt")
        assert _is_path_allowed(path) is True

    def test_downloads_allowed(self):
        path = os.path.join(str(Path.home()), "Downloads", "file.txt")
        assert _is_path_allowed(path) is True

    def test_root_path_blocked(self):
        assert _is_path_allowed("/etc/passwd") is False

    def test_home_root_blocked(self):
        assert _is_path_allowed(str(Path.home())) is False

    def test_system_path_blocked(self):
        assert _is_path_allowed("/usr/local/bin/python") is False

    def test_tilde_expansion_allowed(self):
        assert _is_path_allowed("~/Documents/file.txt") is True

    def test_tilde_expansion_blocked(self):
        assert _is_path_allowed("~/secret_dir/file.txt") is False


class TestReadFile:
    def test_reads_existing_file(self):
        filepath = os.path.join(TEST_DIR, "readable.txt")
        with open(filepath, "w") as f:
            f.write("hello world")
        result = read_file(filepath)
        assert result == "hello world"

    def test_blocked_path(self):
        result = read_file("/etc/hosts")
        assert "Access denied" in result

    def test_missing_file(self):
        result = read_file(os.path.join(TEST_DIR, "nonexistent.txt"))
        assert "not found" in result.lower() or "error" in result.lower()

    def test_truncates_large_file(self):
        filepath = os.path.join(TEST_DIR, "large.txt")
        with open(filepath, "w") as f:
            f.write("x" * 15000)
        result = read_file(filepath)
        assert len(result) < 15000
        assert "truncated" in result.lower()


class TestWriteFile:
    def test_writes_to_allowed_path(self):
        filepath = os.path.join(TEST_DIR, "output.txt")
        result = write_file(filepath, "test content")
        assert "success" in result.lower() or "written" in result.lower() or "wrote" in result.lower()
        with open(filepath) as f:
            assert f.read() == "test content"

    def test_blocked_path(self):
        result = write_file("/tmp/blocked.txt", "content")
        assert "Access denied" in result

    def test_creates_parent_directories(self):
        filepath = os.path.join(TEST_DIR, "sub", "dir", "nested.txt")
        result = write_file(filepath, "nested content")
        assert os.path.exists(filepath)
        with open(filepath) as f:
            assert f.read() == "nested content"

    def test_confirm_callback_deny(self):
        file_ops.write_confirm_callback = lambda path, content: False
        filepath = os.path.join(TEST_DIR, "denied.txt")
        result = write_file(filepath, "should not write")
        assert "cancel" in result.lower() or "denied" in result.lower()
        assert not os.path.exists(filepath)
        file_ops.write_confirm_callback = None

    def test_confirm_callback_allow(self):
        file_ops.write_confirm_callback = lambda path, content: True
        filepath = os.path.join(TEST_DIR, "allowed.txt")
        result = write_file(filepath, "approved content")
        assert os.path.exists(filepath)
        file_ops.write_confirm_callback = None


class TestListDirectory:
    def test_lists_files(self):
        filepath = os.path.join(TEST_DIR, "listme.txt")
        with open(filepath, "w") as f:
            f.write("content")
        result = list_directory(TEST_DIR)
        assert "listme.txt" in result

    def test_shows_file_indicator(self):
        filepath = os.path.join(TEST_DIR, "indicator.txt")
        with open(filepath, "w") as f:
            f.write("x")
        result = list_directory(TEST_DIR)
        assert "[FILE]" in result

    def test_shows_dir_indicator(self):
        subdir = os.path.join(TEST_DIR, "subdir_test")
        os.makedirs(subdir, exist_ok=True)
        result = list_directory(TEST_DIR)
        assert "[DIR]" in result

    def test_blocked_path(self):
        result = list_directory("/etc")
        assert "Access denied" in result


class TestSearchFiles:
    def test_finds_matching_files(self):
        filepath = os.path.join(TEST_DIR, "findme.md")
        with open(filepath, "w") as f:
            f.write("markdown")
        result = search_files(TEST_DIR, "*.md")
        assert "findme.md" in result

    def test_no_matches(self):
        result = search_files(TEST_DIR, "*.xyz_nonexistent")
        assert "no files matching" in result.lower() or "no matches" in result.lower() or result.strip() == ""

    def test_blocked_path(self):
        result = search_files("/usr", "*.py")
        assert "Access denied" in result

    def test_skips_hidden_directories(self):
        hidden_dir = os.path.join(TEST_DIR, ".hidden")
        os.makedirs(hidden_dir, exist_ok=True)
        filepath = os.path.join(hidden_dir, "secret.txt")
        with open(filepath, "w") as f:
            f.write("hidden")
        result = search_files(TEST_DIR, "secret.txt")
        assert ".hidden" not in result
