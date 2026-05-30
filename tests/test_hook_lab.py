"""Tests for hook_lab — hook parsing, scoring/ranking, and prompt building."""
import pytest

import hook_lab as hl


class TestParseHooks:
    def test_delimited_mode_drops_preamble_and_noise(self):
        raw = (
            "Here are your hooks:\n"
            "1. Contrarian :: Everyone says post daily. We post twice a week and tripled reach.\n"
            "- Specific Number :: We lost 40 million naira over one late proposal. Here's the math.\n"
            "Hope these help!\n"
        )
        hooks = hl.parse_hooks(raw)
        texts = [h["hook"] for h in hooks]
        # The two real, delimited hooks survive; preamble + sign-off are dropped.
        assert len(hooks) == 2
        assert any("post twice a week" in t for t in texts)
        assert all("Here are your hooks" not in t for t in texts)
        assert all("Hope these help" not in t for t in texts)
        assert hooks[0]["pattern"] == "Contrarian"

    def test_loose_fallback_when_no_delimiter(self):
        raw = (
            "Everyone said it would fail. It didn't, and the numbers prove it.\n"
            "We turned down our biggest deal last week. Here's why.\n"
        )
        hooks = hl.parse_hooks(raw)
        assert len(hooks) == 2
        assert all(h["pattern"] == "Hook" for h in hooks)

    def test_dedupe_and_length_filters(self):
        raw = (
            "A :: short\n"                       # too short → dropped
            "B :: A perfectly good hook line here.\n"
            "C :: A perfectly good hook line here.\n"  # duplicate → dropped
        )
        hooks = hl.parse_hooks(raw)
        assert len(hooks) == 1
        assert hooks[0]["hook"] == "A perfectly good hook line here."

    def test_empty_and_none(self):
        assert hl.parse_hooks("") == []
        assert hl.parse_hooks(None) == []

    def test_strips_wrapping_quotes(self):
        hooks = hl.parse_hooks('Bold Claim :: "This is the hook in quotes that is long enough."')
        assert hooks[0]["hook"].startswith("This is the hook")
        assert '"' not in hooks[0]["hook"][:1]


class TestScoreAndRank:
    def test_ranks_clean_above_flawed(self):
        hooks = [
            {"pattern": "Question", "hook": "Are you struggling to grow on LinkedIn?"},  # question → penalised
            {"pattern": "Specific", "hook": "We tripled reach in 60 days by posting less."},
        ]
        ranked = hl.score_and_rank(hooks)
        # Clean statement should rank at or above the question hook.
        assert ranked[0]["score"] >= ranked[1]["score"]
        assert all("score" in h and "grade" in h for h in ranked)

    def test_scores_in_valid_range(self):
        hooks = [{"pattern": "X", "hook": "A reasonable, specific hook with stakes."}]
        ranked = hl.score_and_rank(hooks)
        assert 0 <= ranked[0]["score"] <= 100


class TestBuildPrompt:
    def test_includes_topic_and_format(self):
        p = hl.build_hooks_prompt("losing a client", "fintech", "founders", count=6)
        assert "losing a client" in p
        assert "fintech" in p
        assert "PATTERN :: HOOK" in p

    def test_research_block_injected(self):
        p = hl.build_hooks_prompt("x", "y", "z", count=4, research="<<R>> short hooks win <<R>>")
        assert "short hooks win" in p


def test_hook_patterns_contract():
    assert len(hl.HOOK_PATTERNS) >= 8
    assert "Contrarian" in hl.HOOK_PATTERNS
