import math
from core.intent_detector import calculate_confidence


def test_single_domain():
    scores = {
        "career": 5,
        "health": 0,
        "finance": 0,
    }
    assert calculate_confidence(scores) == 1.0


def test_equal_scores():
    scores = {
        "career": 5,
        "health": 5,
        "finance": 5,
    }
    assert calculate_confidence(scores) == 0.0


def test_zero_scores():
    scores = {
        "career": 0,
        "health": 0,
        "finance": 0,
    }
    assert calculate_confidence(scores) == 0.0


def test_two_equal_domains():
    scores = {
        "career": 5,
        "health": 5,
        "finance": 0,
    }
    expected = 1 - math.log(2) / math.log(3)
    assert abs(calculate_confidence(scores) - round(expected, 3)) < 0.001


print("Confidence formula tests passed!")