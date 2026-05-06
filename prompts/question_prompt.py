QUESTION_SYSTEM_PROMPT = """You generate reverse-explanation learning tasks, not generic quizzes. Return a single JSON object only."""


def build_question_user_prompt(topic: str, outline: dict, history: list[dict]) -> str:
    user_asks = []
    for item in history:
        role = str(item.get("role", "")).strip().lower()
        content = str(item.get("content", "")).strip()
        if role == "user" and content:
            user_asks.append(content)

    return (
        "JSON only. Required key: questions(array).\\n"
        "Each question item must include exactly: questionId, question, modelAnswer, keywords(array).\\n"
        "Task purpose: create reverse-explanation prompts the learner answers in their own words.\\n"
        "Behavior rules:\\n"
        "1) Primary grounding source is user asks from chat history.\\n"
        "2) If multiple user asks exist, prioritize recent asks and salient learning curiosities.\\n"
        "3) If history is sparse or no user asks exist, fallback to topic+outline.\\n"
        "4) Do NOT generate generic trivia or fact-recall quiz style items.\\n"
        "5) Questions should request explanation-focused responses, such as:\\n"
        "   - explain the concept back in your own words\\n"
        "   - explain cause/process/result\\n"
        "   - explain with an example or analogy\\n"
        "   - distinguish related concepts when relevant\\n"
        "6) modelAnswer should be concise but sufficient as a reference answer for evaluation.\\n"
        "7) keywords should be 3-7 short key terms aligned with modelAnswer.\\n"
        "8) Keep language aligned with the user language in history when possible.\\n"
        f"topic={topic}\\n"
        f"outline={outline}\\n"
        f"history={history}\\n"
        f"user_asks_chronological={user_asks}\\n"
        "recent_user_asks_last=true"
    )
