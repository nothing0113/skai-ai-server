# skai-ai-server

skAI 프로젝트에서 사용하는 **외부 AI 전용 서버**입니다.  
Spring 서버가 이 저장소를 직접 import해서 쓰는 구조가 아니라, **HTTP API로 호출하는 별도 서버**로 사용합니다.

기본 provider는 **OpenRouter**입니다.  
로컬 테스트가 필요할 때만 선택적으로 **OMLX**를 사용할 수 있습니다.

---

## 1. 이 저장소가 하는 일

이 서버는 skAI에서 필요한 AI 기능을 따로 분리해서 제공합니다.

주요 역할:
- 문장 임베딩 생성
- LLM 채팅 응답 생성
- 답변 채점
- dense / sparse / keyword 기반 점수 계산

즉 구조는 아래와 같습니다.

- Spring 서버 → `skai-ai-server` 호출
- `skai-ai-server` → OpenRouter 또는 OMLX 호출

이렇게 분리해두면 장점이 있습니다.
- Spring 서버는 AI 모델 구현 세부사항을 몰라도 됨
- provider 교체가 쉬움
- Docker 배포가 쉬움
- 동료가 로컬에서 바로 실행하기 쉬움

---

## 2. 전체 아키텍처

```text
Spring Server
  -> HTTP
skai-ai-server (FastAPI)
  -> OpenRouter (기본)
  -> OMLX (선택, 로컬 테스트용)
```

핵심 원칙:
- 이 서버는 **stateless** 여야 함
- 세션/DB/사용자 상태 저장 없음
- 실패 시 조용히 fallback 하지 말고 **명시적으로 에러 반환**

---

## 3. 폴더 구조

```text
app/
  main.py                # FastAPI 엔드포인트 진입점
  config.py              # provider / model / base URL 환경변수 설정
  schemas.py             # 요청/응답 스키마
  services/
    embeddings.py        # dense 임베딩 처리
    sparse.py            # sparse 유사도 처리
    keyword.py           # 키워드 정규화/확장/매칭
    grading.py           # 최종 채점 점수 계산
    llm.py               # LLM(OpenRouter/OMLX) 호출

tests/
  test_api.py            # API / 설정 / 채점 관련 테스트

.github/workflows/
  docker-publish.yml     # GHCR 이미지 자동 빌드/푸시

Dockerfile               # 컨테이너 이미지 빌드
Docker-compose.yml       # 로컬 실행용 compose
.env.example             # 기본 환경변수 예시
README.md                # 현재 문서
```

---

## 4. 내부 기능 설명

### 4-1. 임베딩 (`/v1/embeddings`)
- 입력 문장 리스트를 받아 dense embedding을 생성합니다.
- 현재 dense 모델 이름은 `dragonkue/snowflake-arctic-embed-l-v2.0-ko` 기준입니다.
- Spring 채점 로직에서 semantic similarity 계산에 사용됩니다.

### 4-2. 채팅 (`/v1/llm/chat`)
- 메시지 목록을 받아 LLM 응답을 생성합니다.
- 기본 provider는 OpenRouter입니다.
- 테스트 환경에서는 OMLX로 바꿔 사용할 수 있습니다.

### 4-3. 채점 (`/v1/grading/score`)
- 질문, 모범답안, 학생답안, 키워드를 입력받아 점수를 계산합니다.
- 내부적으로 다음 요소를 합산합니다.
  - dense score
  - sparse score
  - keyword score
- 현재 가중치 구조는 skAI 기준을 따릅니다.

### 4-4. sparse / keyword / grading
- `sparse.py`: sparse 유사도 계산
- `keyword.py`: 키워드 확장, 정규화, 매칭
- `grading.py`: dense/sparse/keyword를 합산하여 최종 점수 산출

---

## 5. 제공 API

이 서버에서 유지해야 하는 핵심 API는 아래입니다.

- `GET /health`
- `GET /v1/models`
- `POST /v1/embeddings`
- `POST /v1/llm/chat`
- `POST /v1/grading/score`

### 5-1. health
```bash
curl -s http://localhost:8000/health
```

### 5-2. chat 예시
```bash
curl -s -X POST http://localhost:8000/v1/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"안녕"}]}'
```

---

## 6. 빠른 시작

### 6-1. 로컬 Python 실행
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .[test]
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6-2. 테스트 실행
```bash
source .venv/bin/activate
pytest -q
```

### 6-3. Docker 실행
```bash
docker compose up -d --build
```

---

## 7. 환경변수

기본값은 OpenRouter 기준입니다.

- `LLM_PROVIDER`: `openrouter` 또는 `omlx`
- `LLM_BASE_URL`: 기본 `https://openrouter.ai/api/v1`
- `OPENROUTER_API_KEY` 또는 `LLM_API_KEY`: OpenRouter 사용 시 필요
- `LLM_MODEL`: 기본 `google/gemma-4-26b-it`
- 선택 alias
  - `OPENROUTER_BASE_URL`
  - `OPENROUTER_MODEL`

OMLX 테스트 예시:
- `LLM_PROVIDER=omlx`
- `LLM_BASE_URL=http://127.0.0.1:11434/v1`
- `LLM_API_KEY=omlx-local`
- `LLM_MODEL=supergemma4`

---

## 8. Spring 서버와 연결하는 방법

Spring 쪽에서는 이 서버를 **외부 AI API 서버**처럼 연결하면 됩니다.

예시:
```env
OPENAI_BASE_URL=http://localhost:8000
```

중요:
- Spring 설정 키 이름이 `openai`처럼 보여도
- 실제 upstream provider는 OpenRouter일 수 있습니다
- 즉 Spring은 이 서버만 바라보면 됩니다

정리하면:
- Spring → `skai-ai-server`
- `skai-ai-server` → OpenRouter

---

## 9. 동료가 수정할 때 어디를 보면 되는가

### AI provider 설정을 바꾸고 싶을 때
- `app/config.py`
- `app/services/llm.py`

### API 엔드포인트를 보고 싶을 때
- `app/main.py`
- `app/schemas.py`

### 채점 로직을 보고 싶을 때
- `app/services/grading.py`
- `app/services/keyword.py`
- `app/services/sparse.py`
- `app/services/embeddings.py`

### 배포 방식을 보고 싶을 때
- `Dockerfile`
- `docker-compose.yml`
- `.github/workflows/docker-publish.yml`

---

## 10. Claude Code / AI 코딩 에이전트용 안내

이 저장소는 Claude Code 같은 코딩 에이전트가 읽고 바로 이해할 수 있게 아래 규칙을 지켜야 합니다.

- 이 repo는 **skAI 전용 외부 AI 서버**입니다
- Spring이 이 서버를 HTTP로 호출합니다
- 기본 provider는 **OpenRouter**입니다
- OMLX는 **로컬 테스트용 선택사항**입니다
- API shape를 임의로 바꾸면 안 됩니다
- 서버는 stateless를 유지해야 합니다
- provider/model 실패 시 silent fallback 금지
- grading semantics는 dense / sparse / keyword 구조를 유지해야 합니다

---

## 11. 절대 바꾸면 안 되는 계약

다음은 호환성 때문에 함부로 바꾸면 안 됩니다.

- 엔드포인트 유지
  - `/health`
  - `/v1/embeddings`
  - `/v1/llm/chat`
  - `/v1/grading/score`
- stateless 유지
- 실패 시 조용한 fallback 금지
- 채점 응답의 핵심 점수 구조와 evidence 필드 안정적으로 유지

즉, 테스트만 통과한다고 끝이 아니라 **Spring과의 계약 호환성**을 같이 봐야 합니다.

---

## 12. 배포

### 로컬 이미지 빌드
```bash
docker build -t skai-ai-server:local .
```

### 로컬 실행
```bash
docker compose up -d --build
```

### GitHub Container Registry
- `.github/workflows/docker-publish.yml`이 `main` 기준으로 GHCR publish를 수행합니다.
- 추후 동료는 컨테이너 이미지를 pull 받아 바로 사용할 수 있습니다.

---

## 13. 한 줄 요약

이 저장소는 **skAI에서 Spring 서버가 호출하는 외부 AI 서버**이며,  
기본 provider는 **OpenRouter**, 용도는 **임베딩 / 채팅 / 채점**입니다.
