REVIEW_SYSTEM_PROMPT = """You create review materials. Return JSON object only."""


def build_review_user_prompt(topic: str, evaluation: dict) -> str:
    return (
        "JSON only. Required keys: flashcards(array), oxQuestions(array), blankQuestions(array).\n"
        f"topic={topic}\nevaluation={evaluation}"
    )
