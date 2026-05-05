from __future__ import annotations

import json
import re


class JsonParseError(ValueError):
    pass


FENCE_RE = re.compile(r"```json|```", re.IGNORECASE)


def parse_json_object(text: str) -> dict:
    cleaned = FENCE_RE.sub("", text).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise JsonParseError("No JSON object boundary found")
    candidate = cleaned[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise JsonParseError(str(exc)) from exc
    if not isinstance(parsed, dict):
        raise JsonParseError("JSON root must be object")
    return parsed


def retry_message(parse_error: str) -> str:
    return (
        "이전 응답은 JSON 파싱에 실패했습니다. "
        "JSON 객체만 반환하세요. 다른 텍스트를 포함하지 마세요. "
        f"파싱 오류: {parse_error}"
    )
