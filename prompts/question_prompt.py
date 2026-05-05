QUESTION_SYSTEM_PROMPT = """You create quiz questions. Return JSON object only."""


def build_question_user_prompt(topic: str, outline: dict, history: list[dict]) -> str:
    return (
        "JSON only. Required keys: questions(array). "
        "Each question item: questionId, question, modelAnswer, keywords(array).\n"
        f"topic={topic}\noutline={outline}\nhistory={history}"
    )
