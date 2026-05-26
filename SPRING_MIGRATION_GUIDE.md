# Spring 서버 수정 가이드

AI 서버의 `/v1/grading/score` 요청 스펙이 변경되었습니다.
아래 내용을 반영해주세요.

---

## 변경 핵심: keywords 구조 변경

### 기존
```json
{
  "keywords": ["민주주의", "주권", "참정권"]
}
```

### 변경 후
```json
{
  "keywords": [
    { "term": "민주주의", "variants": ["democracy", "민주정치", "민주제도"] },
    { "term": "주권",    "variants": ["sovereignty", "주권재민", "국민주권"] },
    { "term": "참정권",  "variants": ["voting rights", "선거권", "투표권"] }
  ]
}
```

`term` : 핵심 키워드  
`variants` : LLM이 생성한 동의어/유사표현 목록 (없으면 빈 배열 `[]`)

---

## 1. LlmService.java — 프롬프트 수정

`generateQuestions()` 메서드의 시스템 프롬프트에서 keywords 생성 규칙을 아래로 교체하세요.

### 기존 프롬프트 (keywords 부분)
```
"keywords": ["key1", "key2"]
Keyword rules: 6~10 keywords total. Each keyword must be a single word or short phrase...
```

### 변경 후 프롬프트
```
"keywords": [{"term": "핵심어", "variants": ["동의어1", "동의어2"]}]
Keyword rules:
- 6~10 keywords total.
- Each keyword must have 1~3 variants (synonyms, related expressions, Korean/English equivalents).
- variants must NOT duplicate the term itself.
- No parentheses, no slash notation in term or variants.
```

### 예시 (LlmService.java 시스템 프롬프트 교체 부분)
```java
"Format: {\"questions\": [{\"question\": \"...\", " +
"\"modelAnswers\": [\"answer variant 1\", \"answer variant 2\", \"answer variant 3\"], " +
"\"keywords\": [{\"term\": \"핵심어\", \"variants\": [\"동의어1\", \"동의어2\"]}]}]} " +
"Keyword rules: 6~10 keywords. Each keyword has term + 1~3 variants " +
"(synonyms, Korean/English equivalents). No parentheses or slash notation."
```

---

## 2. LlmService.java — JSON 파싱 수정

`generateQuestions()` 에서 keywords를 파싱하는 부분을 수정하세요.

### 기존
```java
List<String> keywords = new ArrayList<>();
for (JsonNode kw : item.path("keywords")) keywords.add(kw.asText());
result.add(new QuestionData(question, modelAnswers, keywords));
```

### 변경 후
```java
List<KeywordDto> keywords = new ArrayList<>();
for (JsonNode kw : item.path("keywords")) {
    String term = kw.path("term").asText();
    List<String> variants = new ArrayList<>();
    for (JsonNode v : kw.path("variants")) variants.add(v.asText());
    keywords.add(new KeywordDto(term, variants));
}
result.add(new QuestionData(question, modelAnswers, keywords));
```

---

## 3. QuestionData 레코드 수정

```java
// 기존
public record QuestionData(String question, List<String> modelAnswers, List<String> keywords) {}

// 변경 후
public record QuestionData(String question, List<String> modelAnswers, List<KeywordDto> keywords) {}

// KeywordDto 추가 (같은 파일 또는 별도 파일)
public record KeywordDto(String term, List<String> variants) {}
```

---

## 4. EvaluationQuestion.java — keywords 컬럼 저장 형식 변경

keywords를 DB에 저장할 때 기존 `["key1","key2"]` 대신 아래 형식으로 저장하세요.

```json
[{"term":"민주주의","variants":["democracy","민주정치"]},{"term":"주권","variants":["sovereignty"]}]
```

ObjectMapper로 직렬화/역직렬화하면 됩니다.

---

## 5. ScoringService.java — AI 서버 요청 바디 수정

```java
// 기존
Map<String, Object> body = Map.of(
    "question", question,
    "modelAnswers", modelAnswers,
    "studentAnswer", userAnswer,
    "keywords", keywordList  // List<String>
);

// 변경 후
Map<String, Object> body = Map.of(
    "question", question,
    "modelAnswers", modelAnswers,
    "studentAnswer", userAnswer,
    "keywords", keywordDtoList  // List<KeywordDto> — Jackson이 자동으로 {"term":...,"variants":[...]} 형태로 직렬화
);
```

---

## 요약

| 파일 | 변경 내용 |
|------|-----------|
| `LlmService.java` | 프롬프트: keywords를 `{term, variants}` 구조로 생성 지시 |
| `LlmService.java` | 파싱: `kw.asText()` → `kw.path("term")` + `kw.path("variants")` |
| `QuestionData` | `List<String> keywords` → `List<KeywordDto> keywords` |
| `KeywordDto` | 신규 추가: `record KeywordDto(String term, List<String> variants)` |
| `EvaluationQuestion.java` | keywords 저장 형식: `["k1"]` → `[{"term":"k1","variants":[...]}]` |
| `ScoringService.java` | AI 서버 요청 시 `KeywordDto` 리스트 전달 |
