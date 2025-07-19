import pytest
from datetime import datetime, timezone, timedelta
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from helper import extract_json_from_llm_response, parse_date_to_utc


def test_extract_json_from_llm_response_valid():
    response = '{"key": "value"}'
    assert extract_json_from_llm_response(response) == {"key": "value"}


def test_extract_json_from_llm_response_with_markdown():
    response = '```json\n{"key": "value"}\n```'
    assert extract_json_from_llm_response(response) == {"key": "value"}


def test_extract_json_from_llm_response_invalid():
    response = '{"key": "value"'
    assert extract_json_from_llm_response(response) == {}


def test_extract_json_from_llm_response_empty():
    response = ""
    assert extract_json_from_llm_response(response) == {}


@pytest.mark.parametrize(
    "date_string, expected_format",
    [
        ("2023-10-27T10:00:00.123Z", True),
        ("2023-10-27T10:00:00.123456+05:30", True),
        ("2023-10-27T10:00:00.123", True),
        ("2023-10-27T10:00:00Z", True),
        ("2023-10-27T10:00:00+05:30", True),
        ("2023-10-27T10:00:00", True),
        ("2023-10-27 10:00:00", True),
        ("2023-10-27", True),
        ("October 27, 2023", True),
        ("27 October 2023", True),
    ],
)
def test_parse_date_to_utc_valid(date_string, expected_format):
    parsed_date_str = parse_date_to_utc(date_string)
    # check if the output is a valid isoformat string
    try:
        datetime.fromisoformat(parsed_date_str.replace("Z", "+00:00"))
        is_valid_iso = True
    except (ValueError, TypeError):
        is_valid_iso = False

    assert is_valid_iso == expected_format


def test_parse_date_to_utc_with_timezone():
    date_string = "2023-10-27T10:00:00+05:30"
    parsed_date_str = parse_date_to_utc(date_string)
    # Manually parse the expected date to ensure correctness
    expected_dt = datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc).astimezone(
        timezone.utc
    )
    expected_dt -= timedelta(hours=5, minutes=30)

    parsed_dt = datetime.fromisoformat(parsed_date_str.replace("Z", "+00:00"))

    # Compare datetime objects
    assert parsed_dt.year == 2023
    assert parsed_dt.month == 10
    assert parsed_dt.day == 27
    assert parsed_dt.hour == 4  # 10:00 - 5:30 = 4:30
    assert parsed_dt.minute == 30


def test_parse_date_to_utc_without_timezone():
    date_string = "2023-10-27T10:00:00"
    parsed_date_str = parse_date_to_utc(date_string)
    assert parsed_date_str == "2023-10-27T10:00:00+00:00"


def test_parse_date_to_utc_invalid_format():
    date_string = "invalid-date"
    assert parse_date_to_utc(date_string) == "invalid-date"


def test_parse_date_to_utc_empty_string():
    assert parse_date_to_utc("") == ""
