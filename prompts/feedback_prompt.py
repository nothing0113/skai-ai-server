FEEDBACK_SYSTEM_PROMPT = """You provide concise educational feedback in Korean. Return JSON object only."""


def build_feedback_user_prompt(score: float, level: str, missing_keywords: list[str], weak_concepts: list[str]) -> str:
    return (
        "JSON only. Required keys: feedback(string).\n"
        f"score={score}\nlevel={level}\nmissingKeywords={missing_keywords}\nweakConcepts={weak_concepts}"
    )
