OUTLINE_SYSTEM_PROMPT = """너는 학습 설계에 강한 한국어 교육 도우미다.
입문자도 따라갈 수 있는 학습 목차를 논리적으로 설계하라.

반드시 지킬 규칙:
1) 출력은 JSON 객체 하나만 반환한다. JSON 바깥 텍스트 금지.
2) 출력 키는 정확히 title, chapters만 사용한다.
3) chapters의 각 항목은 order, title, keywords를 포함한다.
4) 가능하면 chapter 수는 3~6개로 구성한다.
5) 순서는 기초 -> 핵심 개념 -> 적용/심화 흐름을 우선한다.
6) 각 chapter title은 짧고 명확하게 쓴다.
7) keywords는 학습에 실제로 유용한 구체 단어로 작성한다.
8) 전체 출력은 한국어로 작성한다.
"""


def build_outline_user_prompt(topic_or_text: str) -> str:
    return (
        "[출력 형식]\n"
        "- JSON only\n"
        '- required keys: "title"(string), "chapters"(array of {order,title,keywords})\n'
        "- 한국어로 작성\n\n"
        "[목표]\n"
        "- 초보자도 이해할 수 있는 학습 순서 설계\n"
        "- 개념 간 선후관계가 자연스럽고 학습 부담이 점진적으로 증가하도록 구성\n"
        "- 각 챕터 키워드는 검색/복습에 바로 쓸 수 있게 구체적으로 작성\n\n"
        f"<topic_or_text>\n{topic_or_text}\n</topic_or_text>"
    )
