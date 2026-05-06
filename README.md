# AI Server

## 설치
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## .env 설정
`.env.example`를 복사해 `.env`를 만들고 아래 기본값을 사용하세요.

```env
LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:11434/api/chat
LOCAL_LLM_MODEL=gemma4:26b
OPENROUTER_API_KEY=
OPENROUTER_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_MODEL=google/gemma-4-26b-a4b-it:free
DENSE_MODEL_NAME=dragonkue/snowflake-arctic-embed-l-v2.0-ko
SPARSE_MODEL_NAME=yjoonjang/splade-ko-v1
DEVICE=auto
```

## 실행
```bash
uvicorn main:app --reload --port 8000
```

## API 호출 예시 (Exact Request Shape)

### `/health`
```bash
curl -s -X GET http://localhost:8000/health
```

### `/outline`
```bash
curl -s -X POST http://localhost:8000/outline \
  -H 'Content-Type: application/json' \
  -d '{
    "topicOrText": "RAG 기초"
  }'
```

### `/chat`
```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "topic": "RAG",
    "outline": {
      "title": "RAG 학습",
      "chapters": [
        {"order": 1, "title": "개요", "keywords": ["retrieval", "generation"]}
      ]
    },
    "history": [
      {"role": "user", "content": "RAG가 뭐야?"},
      {"role": "assistant", "content": "검색 기반 생성 방식이야."}
    ],
    "message": "장점도 설명해줘"
  }'
```

### `/questions`
`/chat`에서 사용자가 실제로 물어본 질문/궁금증(`history`)을 우선으로, 역설명(Reverse-Explanation) 과제를 생성합니다. `history`가 충분하면 이를 주 근거로 쓰고, 부족하면 `topic + outline`을 보조로 사용합니다. 응답 형식은 동일하게 `{ "questions": [...] }`이며 각 항목은 `questionId`, `question`, `modelAnswer`, `keywords`를 유지합니다.

```bash
curl -s -X POST http://localhost:8000/questions \
  -H 'Content-Type: application/json' \
  -d '{
    "topic": "RAG",
    "outline": {
      "title": "RAG 학습",
      "chapters": [
        {"order": 1, "title": "개요", "keywords": ["retrieval", "generation"]}
      ]
    },
    "history": [
      {"role": "user", "content": "RAG에서 검색 단계가 왜 필요한지 잘 모르겠어"},
      {"role": "assistant", "content": "검색은 근거 문서를 찾기 위한 단계야."},
      {"role": "user", "content": "그럼 파인튜닝이랑은 어떤 점이 다른지도 설명해줘"}
    ]
  }'
```

### `/evaluate`
```bash
curl -s -X POST http://localhost:8000/evaluate \
  -H 'Content-Type: application/json' \
  -d '{
    "questions": [
      {
        "questionId": 1,
        "question": "RAG를 설명하세요.",
        "modelAnswer": "RAG는 검색 후 생성하는 방식입니다.",
        "keywords": ["검색", "생성"]
      }
    ],
    "answers": [
      "관련 문서를 검색한 뒤 답을 생성합니다."
    ]
  }'
```

### `/review-content`
```bash
curl -s -X POST http://localhost:8000/review-content \
  -H 'Content-Type: application/json' \
  -d '{
    "topic": "RAG",
    "evaluation": {
      "score": 72.5,
      "missingKeywords": ["임베딩"],
      "weakConcepts": ["리트리버 튜닝"]
    }
  }'
```

### `/review-schedule`
```bash
curl -s -X POST http://localhost:8000/review-schedule \
  -H 'Content-Type: application/json' \
  -d '{
    "score": 72.5,
    "n": 1,
    "ef": 2.5,
    "previousInterval": 6,
    "reviewedAt": "2026-05-05"
  }'
```

## Spring Boot 연동 URL 예시
- FastAPI base URL: `http://localhost:8000`
- Spring Boot에서 호출 예: `http://localhost:8000/evaluate`

## Troubleshooting
- `OPENROUTER_API_KEY`가 비어 있으면 OpenRouter 호출이 실패합니다.
- Ollama 로컬 모델 사용 시 `LOCAL_LLM_URL`과 `LOCAL_LLM_MODEL` 값이 실행 환경과 일치해야 합니다.
- `DEVICE=auto`는 CUDA 가능 시 `cuda`, 아니면 `cpu`로 동작합니다.
- 초기 실행에서는 임베딩/희소 모델 다운로드 때문에 시간이 걸릴 수 있습니다.
- LLM이 JSON 외 텍스트를 반환하면 1회 재시도 후 `LLM_JSON_PARSE_ERROR`를 반환합니다.
- `/review-schedule`의 `reviewedAt`는 `YYYY-MM-DD` 형식이어야 합니다.
