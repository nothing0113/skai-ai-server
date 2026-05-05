import pytest

from utils.json_parser import JsonParseError, parse_json_object


def test_parse_json_with_fence_and_prose():
    text = "결과:\n```json\n{\"a\":1}\n```\n감사"
    assert parse_json_object(text) == {"a": 1}


def test_parse_json_fail():
    with pytest.raises(JsonParseError):
        parse_json_object("no json")
