"""Tests for the Home Daily Brief topic parser (app._extract_brief_topics)."""
import importlib.util
import os

import pytest

_APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")


@pytest.fixture(scope="module")
def appmod():
    """Import app.py once (bare mode) so we can test its pure helpers."""
    spec = importlib.util.spec_from_file_location("appmod_under_test", _APP_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestExtractBriefTopics:
    def test_splits_on_em_dash_and_colon(self, appmod):
        summary = (
            "## Timely topics right now\n"
            "- AI contract review for SMEs — regulators issued guidance\n"
            "- Data protection fines: three new cases this month\n"
            "## Post this week\nLead with the numbers.\n"
        )
        topics = appmod._extract_brief_topics(summary)
        assert "AI contract review for SMEs" in topics
        assert "Data protection fines" in topics
        # The 'Post this week' section must NOT contribute topics
        assert all("Lead with" not in t for t in topics)

    def test_handles_numbered_and_bold_and_bullets(self, appmod):
        summary = (
            "## Timely topics right now\n"
            "1. **Remote work policy shifts**\n"
            "* Layoffs in fintech\n"
            "• Funding winter takes\n"
        )
        topics = appmod._extract_brief_topics(summary)
        assert "Remote work policy shifts" in topics
        assert "Layoffs in fintech" in topics
        assert "Funding winter takes" in topics

    def test_respects_max_n(self, appmod):
        summary = "## Timely topics right now\n" + "\n".join(
            f"- Topic number {i}" for i in range(10)
        )
        assert len(appmod._extract_brief_topics(summary, max_n=3)) == 3

    def test_empty_and_garbage_return_empty(self, appmod):
        assert appmod._extract_brief_topics("") == []
        assert appmod._extract_brief_topics(None) == []
        assert appmod._extract_brief_topics("no headers here, just text") == []

    def test_ignores_topics_when_section_absent(self, appmod):
        summary = "## Something else\n- not a timely topic\n"
        assert appmod._extract_brief_topics(summary) == []

    def test_auth_required_defaults_true(self, appmod, monkeypatch):
        """REQUIRE_AUTH defaults to True (gated) and respects falsey overrides."""
        monkeypatch.delenv("REQUIRE_AUTH", raising=False)
        assert appmod._auth_required() is True
        monkeypatch.setenv("REQUIRE_AUTH", "false")
        assert appmod._auth_required() is False
        monkeypatch.setenv("REQUIRE_AUTH", "0")
        assert appmod._auth_required() is False
        monkeypatch.setenv("REQUIRE_AUTH", "true")
        assert appmod._auth_required() is True
