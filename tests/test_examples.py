"""Tests for core/examples.py -- hook and comment example helpers."""
import pytest

from core.examples import (
    get_hook_examples, get_comment_examples, get_examples,
    _EXAMPLES, _GLOBAL_EXAMPLES,
)


class TestGetExamplesRegionAware:
    def test_global_mode_draws_from_global_pool(self):
        picks = get_examples(2, seed=7, global_mode=True)
        assert len(picks) == 2
        assert all(p in _GLOBAL_EXAMPLES for p in picks)

    def test_nigerian_mode_draws_from_nigerian_pool(self):
        picks = get_examples(2, seed=7, global_mode=False)
        assert len(picks) == 2
        assert all(p in _EXAMPLES for p in picks)

    def test_deterministic_with_seed(self):
        a = get_examples(2, seed=99, global_mode=True)
        b = get_examples(2, seed=99, global_mode=True)
        assert a == b

    def test_default_is_nigerian_pool(self):
        # Backwards-compatible default: no global_mode kwarg behaves as before.
        picks = get_examples(2, seed=7)
        assert all(p in _EXAMPLES for p in picks)

    def test_tops_up_when_pool_too_small(self):
        # Asking for more than a single pool holds still returns that many.
        picks = get_examples(8, seed=1, global_mode=True)
        assert len(picks) == 8

    def test_global_examples_have_no_nigerian_markers(self):
        """Region-neutral pool must not leak naira / Lagos context."""
        blob = "\n".join(_GLOBAL_EXAMPLES).lower()
        for marker in ["naira", "lagos", "ikeja", "lekki", "yaba", "₦", "n450,000"]:
            assert marker not in blob


class TestGetHookExamples:
    def test_returns_requested_count(self):
        result = get_hook_examples(3)
        assert len(result) == 3

    def test_large_n_returns_all_available(self):
        result = get_hook_examples(100)
        assert len(result) > 0
        assert len(result) <= 100
        # Should not crash, just returns all available

    def test_deterministic_with_seed(self):
        a = get_hook_examples(3, seed=42)
        b = get_hook_examples(3, seed=42)
        assert a == b

    def test_all_items_are_nonempty_strings(self):
        result = get_hook_examples(8)
        for item in result:
            assert isinstance(item, str)
            assert len(item.strip()) > 0


class TestGetCommentExamples:
    def test_returns_requested_count(self):
        result = get_comment_examples(2)
        assert len(result) == 2

    def test_large_n_returns_all_available(self):
        result = get_comment_examples(100)
        assert len(result) > 0
        assert len(result) <= 100

    def test_deterministic_with_seed(self):
        a = get_comment_examples(2, seed=42)
        b = get_comment_examples(2, seed=42)
        assert a == b

    def test_all_items_are_nonempty_strings(self):
        result = get_comment_examples(4)
        for item in result:
            assert isinstance(item, str)
            assert len(item.strip()) > 0
