# mathknot-server

MathKnot 백엔드 API — **FastAPI + DDD(모듈형 레이어드) + Postgres**.

OCR/채점 프롬프트·LLM 키를 서버에 은닉하기 위한 자체 백엔드. (배경: 모노레포
`docs/concept.md`, `docs/260602_plan.md`)

현재 구현 범위: **회원가입 + 로그인(JWT)**.

---

## 빠른 시작

```bash
# 0) (최초 1회) 의존성 설치 — uv 가 .venv 를 자동 생성/관리
uv sync

# 1) 환경변수 준비
cp .env.example .env        # JWT_SECRET_KEY 등 필요 시 수정

# 2) 로컬 Postgres 기동
docker compose up -d

# 3) DB 마이그레이션
uv run alembic upgrade head

# 4) 서버 실행
uv run uvicorn app.main:app --reload
#  → http://localhost:8000/docs  (Swagger UI)
#  → http://localhost:8000/health

# 테스트 (인메모리 SQLite, Postgres 불필요)
uv run pytest
```

> uv 미설치 시: https://docs.astral.sh/uv/getting-started/installation/

---

## ⚠️ 개발 규칙 — 테스트 케이스 갱신 필수

**기능을 추가·변경할 때는 반드시 해당 테스트 케이스(`tests/`)도 함께 갱신한다.**

- 새 엔드포인트/유스케이스를 추가하면 → happy-path + 주요 에러 케이스 테스트를 추가한다.
- 기존 동작(요청/응답 스키마, 도메인 규칙, 상태코드 등)을 바꾸면 → 관련 테스트를 같이 수정한다.
- 커밋/PR 전 `uv run pytest` 가 **전부 통과**하는지 확인한다. 테스트 없는 기능 변경은 미완료로 간주.

> 테스트는 인메모리 SQLite로 돌아 Postgres 없이 실행된다(`tests/conftest.py`). 라우터~리포지토리
> 전 계층을 검증하므로, 동작이 바뀌면 테스트가 깨져 회귀를 잡아준다 — 그 신호를 죽이지 말 것.

---

## API (v1)

베이스 경로: `/api/v1`

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/auth/signup` | 회원가입 (pending 유저 생성) |
| POST | `/api/v1/auth/login` | 로그인 → access/refresh JWT 발급 |
| GET | `/health` | 헬스체크 + 앱 버전 |

회원가입 예시:

```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"a@b.com","password":"supersecret","full_name":"홍길동","role":"student","grade":"9"}'
```

신규 유저는 항상 `approval_status="pending"` 으로 생성된다(관리자 승인 후 활성).
`role` 은 가입 시 `student` / `teacher` 만 선택 가능(`admin`/`owner` 는 불가).

---

## 아키텍처 (DDD · 모듈형)

> 설계 결정의 상세 근거(왜 헥사고날은 안 쓰는지, core/modules 구분, entities/models/schemas
> 차이, 모듈 작명 등)는 [`docs/architecture.md`](docs/architecture.md) 참고.

바운디드 컨텍스트를 `app/modules/<context>/` 로 나눈다. DDD 전술 패턴
(엔티티 · 값 객체 · 리포지토리 · 서비스)은 유지하되, 헥사고날(모든 외부 의존성을
포트/어댑터로 추상화) 같은 무거운 간접화는 쓰지 않는다 — 모듈 안은 파일 단위로
납작하게 둔다.

```
app/
├── main.py                  # FastAPI 앱 팩토리 + /health
├── api/
│   └── v1.py                # 모든 모듈의 v1 라우터를 /api/v1 로 집약
├── core/                    # 횡단 관심사 (프레임워크/인프라 공용)
│   ├── config.py            # pydantic-settings 설정
│   ├── database.py          # async 엔진/세션, DeclarativeBase, get_session
│   ├── security.py          # 비밀번호 해싱(argon2) + JWT(PyJWT)
│   └── exceptions.py        # AppError 베이스 + 예외 핸들러
└── modules/
    └── identity/            # 회원/인증 컨텍스트
        ├── entities.py      # User 엔티티 + 값객체(Role/ApprovalStatus) + 도메인 예외 (순수)
        ├── models.py        # UserModel (SQLAlchemy ORM)
        ├── repository.py    # UserRepository (구체) + ORM↔엔티티 매핑
        ├── service.py       # AuthService (유스케이스) — repo + core.security 직접 사용
        ├── schemas.py       # Pydantic 요청/응답
        ├── router.py        # HTTP 라우터 (현재 v1)
        └── dependencies.py  # 의존성 와이어링
```

설계 규칙:

- **entities.py** — 도메인 엔티티/값객체. 프레임워크/DB/보안 라이브러리에 의존하지
  않는 순수 파이썬. DB 없이 단위테스트 가능. (도메인 ↔ ORM 은 별도 표현이며 repository 가 매핑)
- **service.py** — 유스케이스 오케스트레이션. 헥사고날 포트 없이 리포지토리와
  `core.security` 를 직접 사용한다. (포트/어댑터 간접화는 의도적으로 생략)
- **repository.py** — Repository 패턴(구체 클래스). ORM ↔ 도메인 엔티티 매핑 담당.
  커밋은 `get_session` 의존성이 요청 경계에서 처리.
- **schemas.py** — Pydantic 스키마는 도메인 모델과 분리해 API 계약을 안정화.

새 컨텍스트(예: `problems`, `grading`)는 `app/modules/<name>/` 으로 같은 패턴을
복제해 추가하고, 라우터를 `app/api/v1.py` 에 등록한다.

> 비고: 채점(`grading`)처럼 도메인 로직이 복잡한 컨텍스트는, 필요해지면 그 모듈에
> 한해 도메인 서비스/포트를 더 두는 식으로 *국소적으로* 무게를 올릴 수 있다.

---

## 버전 관리 전략

**API 버전 (URL path versioning)**
- 경로 prefix 로 버전을 노출: `/api/v1/...`.
- 한 버전 안에서는 **하위 호환(additive)** 변경만 한다(필드 추가 등).
- 호환 불가능한 변경은 모듈에 `router_v2.py`(필요 시 `schemas_v2.py`)를 추가하고
  `app/api/v2.py` 에서 `/api/v2` 로 별도 마운트. v1 은 클라이언트 마이그레이션까지 유지.
- v1/v2 라우터 파일이 분리돼 있어 버전 간 코드가 섞이지 않는다.

**앱/릴리스 버전**
- `pyproject.toml` 의 `version` 과 `APP_VERSION`(설정)이 단일 출처.
  `/health` 응답과 OpenAPI(`/docs`)에 노출된다.
- 릴리스는 git 태그(`v0.1.0`)로 표기(SemVer).

**DB 스키마 버전**
- Alembic 리비전으로 관리. 마이그레이션 파일: `migrations/versions/`.
- 스키마 변경 시:
  ```bash
  uv run alembic revision --autogenerate -m "설명"
  uv run alembic upgrade head
  ```

---

## 기술 스택 / 참고 문서

| 영역 | 선택 | 문서 |
|---|---|---|
| 웹 프레임워크 | FastAPI | https://fastapi.tiangolo.com/ |
| 설정 | pydantic-settings | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ |
| ORM | SQLAlchemy 2.0 (async) | https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html |
| 드라이버 | asyncpg | https://magicstack.github.io/asyncpg/ |
| 마이그레이션 | Alembic | https://alembic.sqlalchemy.org/ |
| 비밀번호 해싱 | pwdlib (argon2) | https://fastapi.tiangolo.com/tutorial/security/ |
| JWT | PyJWT | https://pyjwt.readthedocs.io/ |
| 패키지/가상환경 | uv | https://docs.astral.sh/uv/ |

---

## 다음 단계 (TODO)

- [ ] `GET /api/v1/auth/me` — access token 으로 현재 유저 조회 (OAuth2 Bearer 의존성)
- [ ] `POST /api/v1/auth/refresh` — refresh token 으로 access token 재발급
- [ ] 관리자 승인 흐름(approval_status 전이) — mathup `auth-role-academy-class.md` 참고
- [ ] `problems` / `grading` 컨텍스트 (OCR + Claude 채점 파이프라인)
