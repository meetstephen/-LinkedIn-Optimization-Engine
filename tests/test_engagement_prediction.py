"""Tests for _predict_engagement in post_generator.py."""
import pytest

from post_generator import _predict_engagement


class TestPredictEngagementScoreBounds:
    """Every score must be between 0 and 100 inclusive."""

    def test_empty_string(self):
        result = _predict_engagement("")
        assert 0 <= result["score"] <= 100
        assert isinstance(result["factors"], list)
        assert isinstance(result["summary"], str)

    def test_very_short_post(self):
        short = "This is a short post about nothing much."
        result = _predict_engagement(short)
        assert 0 <= result["score"] <= 100
        # Short posts should score lower on length
        length_factor = next(f for f in result["factors"] if f["name"] == "Length")
        assert length_factor["score"] < 15

    def test_score_within_bounds_for_long_post(self):
        long_post = "Word " * 800
        result = _predict_engagement(long_post)
        assert 0 <= result["score"] <= 100

    def test_score_within_bounds_various_inputs(self):
        inputs = [
            "Hello",
            "A" * 5000,
            "\n\n\n",
            "123 456 789",
            "No content here whatsoever",
        ]
        for text in inputs:
            result = _predict_engagement(text)
            assert 0 <= result["score"] <= 100, f"Failed for input: {text[:30]}"


class TestPredictEngagementSpecificity:
    """Posts with numbers and specifics should score higher on specificity."""

    def test_numbers_boost_specificity(self):
        post_with_numbers = (
            "We tracked 94 proposals last year.\n\n"
            "Win rate: 34%. Revenue from won deals: N14.2 million.\n\n"
            "The single variable that mattered most was response time. "
            "Proposals sent within 48 hours: 52% close rate. "
            "After 5 days: 11%.\n\n"
            "That gap cost us N8.3 million in lost revenue."
        )
        post_without_numbers = (
            "We tracked our proposals last year.\n\n"
            "The win rate was okay. Revenue from won deals was good.\n\n"
            "The single variable that mattered most was response time. "
            "Proposals sent quickly did better than ones sent late.\n\n"
            "That gap cost us a lot in lost revenue."
        )
        result_nums = _predict_engagement(post_with_numbers)
        result_no_nums = _predict_engagement(post_without_numbers)
        spec_nums = next(f for f in result_nums["factors"] if f["name"] == "Specificity")
        spec_no_nums = next(f for f in result_no_nums["factors"] if f["name"] == "Specificity")
        assert spec_nums["score"] > spec_no_nums["score"]


class TestPredictEngagementVulnerability:
    """Posts with vulnerability keywords should get emotional pull credit."""

    def test_vulnerability_keywords_boost_score(self):
        vulnerable_post = (
            "I failed at my first startup.\n\n"
            "I was scared to tell my investors. I made a mistake "
            "hiring too fast. I lost three key employees in one month.\n\n"
            "And honestly? I wasn't sure I could recover.\n\n"
            "But here is what quitting taught me about starting over."
        )
        neutral_post = (
            "My first startup had challenges.\n\n"
            "There were some personnel changes. The team shifted "
            "and priorities evolved over the course of several months.\n\n"
            "Eventually things improved.\n\n"
            "Here is what that experience taught me about starting over."
        )
        result_vuln = _predict_engagement(vulnerable_post)
        result_neutral = _predict_engagement(neutral_post)
        emo_vuln = next(f for f in result_vuln["factors"] if f["name"] == "Emotional Pull")
        emo_neutral = next(f for f in result_neutral["factors"] if f["name"] == "Emotional Pull")
        assert emo_vuln["score"] > emo_neutral["score"]


class TestPredictEngagementStructure:
    """Return dict has the expected shape."""

    def test_returns_five_factors(self):
        result = _predict_engagement("A test post with some words in it.")
        assert len(result["factors"]) == 5

    def test_factor_keys(self):
        result = _predict_engagement("A test post.")
        for factor in result["factors"]:
            assert "name" in factor
            assert "score" in factor
            assert "max" in factor
            assert "note" in factor

    def test_individual_factor_bounds(self):
        post = (
            "Three years ago I lost a N4M client.\n\n"
            "It happened on a Tuesday morning in Lagos.\n\n"
            "The contract had one clause I missed.\n\n"
            "Here is the thing. That clause cost me everything."
        )
        result = _predict_engagement(post)
        for factor in result["factors"]:
            assert 0 <= factor["score"] <= factor["max"]

    def test_deterministic(self):
        post = "Same input should always give same output. Numbers: 42, places: London."
        r1 = _predict_engagement(post)
        r2 = _predict_engagement(post)
        assert r1 == r2


class TestPredictEngagementPlaceDetection:
    """Place detection should work for any location, not just Nigerian ones."""

    def test_nigerian_places_detected(self):
        post = "We opened our new office in Lagos last month. " * 20
        result = _predict_engagement(post)
        spec = next(f for f in result["factors"] if f["name"] == "Specificity")
        assert spec["score"] >= 7  # baseline 5 + at least place bonus

    def test_international_places_detected(self):
        post = "Our team relocated to San Francisco last quarter. " * 20
        result = _predict_engagement(post)
        spec = next(f for f in result["factors"] if f["name"] == "Specificity")
        assert spec["score"] >= 7  # baseline 5 + at least place bonus

    def test_proper_noun_detection(self):
        # A post with a proper noun not in the known list but capitalized mid-sentence
        post = "Last week in Bangalore we closed a deal worth millions. " * 20
        result = _predict_engagement(post)
        spec = next(f for f in result["factors"] if f["name"] == "Specificity")
        assert spec["score"] >= 7  # baseline 5 + proper noun bonus
