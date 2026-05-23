"""Tests for core/examples.py -- hook and comment example helpers."""
import pytest

from core.examples import get_hook_examples, get_comment_examples


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
