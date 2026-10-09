# mathknot-server — 아키텍처

> 작성일: 2026-06-26
> 범위: 백엔드 서버(`mathknot-server/`)의 전반 구조 · 설계 결정 · 그 근거
> 실행/설치 방법은 [`../README.md`](../README.md) 참고 (이 문서는 "왜 이렇게 생겼는가"에 집중)
> 제품 배경은 모노레포 [`docs/concept.md`](../../docs/concept.md), [`docs/260602_plan.md`](../../docs/260602_plan.md) 참고

---

## 1. 한 줄 정의

MathKnot 백엔드 — **FastAPI + DDD(모듈형) + Postgres**. OCR/채점 프롬프트·LLM 키를
서버에 은닉하기 위한 자체 API 서버. 현재 구현 범위는 **회원가입 + 로그인(JWT)**.

## 2. 기술 스택

| 영역 | 선택 | 근거 / 문서 |
|---|---|---|
| 웹 프레임워크 | FastAPI | RN 친화 REST, async, 자동 OpenAPI — https://fastapi.tiangolo.com/ |
| 설정 | pydantic-settings | `.env`/환경변수 타입 안전 로딩 — https://docs.pydantic.dev/latest/concepts/pydantic_settings/ |
| ORM | SQLAlchemy 2.0 (async) | 표준 async ORM — https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html |
| DB 드라이버 | asyncpg | 비동기 Postgres 드라이버 |
| 마이그레이션 | Alembic (async env) | 스키마 버전 관리 — https://alembic.sqlalchemy.org/ |
| 비밀번호 해싱 | pwdlib (argon2) | FastAPI 공식 튜토리얼 권장(구 passlib 대체) — https://fastapi.tiangolo.com/tutorial/security/ |
| JWT | PyJWT | access/refresh 토큰 — https://pyjwt.readthedocs.io/ |
| 패키지/가상환경 | uv | venv 자동 관리 + 빠름 — https://docs.astral.sh/uv/ |

## 3. 아키텍처 개요

### 3.1 채택한 것 / 채택하지 않은 것

**DDD(도메인 주도 설계)의 전술 패턴은 채택**한다:

- 바운디드 컨텍스트(모듈) 단위 분할
- 도메인 엔티티 · 값 객체 (프레임워크/DB 무관, 순수 파이썬)
- Repository 패턴 (도메인 ↔ ORM 매핑)
- 서비스 레이어 (유스케이스 오케스트레이션)

**헥사고날(Ports & Adapters)의 무거운 간접화는 채택하지 않는다**:

- ❌ 모든 외부 의존성을 포트(Protocol/ABC)로 추상화 + 어댑터로 구현
- ❌ `domain/application/infrastructure/interfaces` 4계층 폴더 분리

> 의도적인 절충이다. DDD의 핵심(도메인 모델 분리, 컨텍스트 경계)은 가져가되,
> 인증/CRUD 수준에선 비용만 큰 포트/어댑터 추상화는 생략해 모듈 안을 파일 단위로
> 납작하게 둔다. 채점(`grading`)처럼 도메인 로직이 복잡해지는 컨텍스트는 *그 모듈에
> 한해* 도메인 서비스/포트를 더 두며 국소적으로 무게를 올릴 수 있다.

### 3.2 전체 디렉토리 구조

```
mathknot-server/
├── pyproject.toml            # 의존성 + 도구 설정 (uv, ruff, pytest)
├── .env.example              # 환경변수 템플릿 (.env 는 git 제외)
├── docker-compose.yml        # 로컬 Postgres
├── alembic.ini               # 마이그레이션 설정 (DB URL 은 env.py 가 주입)
├── README.md                 # 빠른 시작 / API 요약
├── docs/
│   └── architecture.md       # (이 문서)
├── migrations/               # Alembic (async)
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_create_users.py
├── app/
│   ├── main.py               # FastAPI 앱 팩토리 + /health
│   ├── api/
│   │   └── v1.py             # 모든 모듈의 v1 라우터를 /api/v1 로 집약
│   ├── core/                 # ── 횡단 관심사 (도메인 지식 없음) ──
│   │   ├── config.py         #   pydantic-settings 설정 (싱글턴)
│   │   ├── database.py       #   async 엔진/세션, DeclarativeBase, get_session
│   │   ├── security.py       #   비밀번호 해싱(argon2) + JWT(PyJWT)
│   │   └── exceptions.py     #   AppError 베이스 + 예외 핸들러
│   └── modules/              # ── 바운디드 컨텍스트 ──
│       └── identity/         #   회원 / 인증 / 접근
│           ├── entities.py   #   도메인 엔티티(User) + 값객체(Role/ApprovalStatus) + 예외
│           ├── models.py     #   SQLAlchemy ORM (UserModel)
│           ├── repository.py #   UserRepository(구체) + ORM↔엔티티 매핑
│           ├── service.py    #   AuthService (유스케이스)
│           ├── schemas.py    #   Pydantic 요청/응답 (API 계약)
│           ├── router.py     #   HTTP 라우터 (/auth/*, 현재 v1)
│           └── dependencies.py #  의존성 와이어링 (get_auth_service)
└── tests/
    ├── conftest.py           # 인메모리 SQLite + get_session 오버라이드
    └── test_auth.py          # 가입/로그인 happy-path + 에러 케이스
```

## 4. 핵심 설계 원칙

### 4.1 `core/` vs `modules/` — 무엇이 어디에 가나

판별 기준 한 가지: **"이 파일이 특정 도메인 타입(`User`, `Problem`…)을 import하는가?"**

- **import하지 않음** → 도메인 무지(domain-ignorance) → `core/` (횡단 기술 관심사)
- **import함** → 그 도메인 소속 → `modules/<context>/`

이 기준으로 `config`/`database`/`exceptions`/`security`가 전부 `core/`에 떨어진다.
예를 들어 `core/security.py`는 시그니처가 전부 평범한 문자열(`subject: str`,
`plain: str`)이라 identity 도메인을 전혀 모른다.

`core/`에 두는 두 번째 이유는 **모듈 간 결합 방지**다. 토큰 검증은 `identity`만
쓰는 게 아니라 보호된 라우트가 있는 *모든* 모듈(`problems`, `grading`…)이 쓴다.
security가 `identity/` 안에 있으면 `problems`가 토큰 디코드 하나 때문에 `identity`를
import하게 되어 identity가 사실상 공유 커널이 된다. `core/`에 두면 모든 모듈이
`core`만 바라보고(core는 누구에게도 의존하지 않음) **모듈끼리는 독립**을 유지한다.

> 의존성 방향:  `modules/* → core`,  `core → (없음)`,  `modules/* ↛ modules/*`

### 4.2 모듈 이름 = 바운디드 컨텍스트

모듈 디렉토리는 **하위 도메인(바운디드 컨텍스트)** 이름을 쓴다. 엔티티명도 라우트명도
아니다.

| 층위 | 이 프로젝트 | 설명 |
|---|---|---|
| 모듈 디렉토리 | `identity` | 바운디드 컨텍스트 (신원/인증/접근, ≈ IAM) |
| API prefix | `/auth` | HTTP 인터페이스 (한 컨텍스트가 여러 라우트 그룹 가능) |
| 엔티티 | `User` | 그 안의 도메인 객체 하나 (컨텍스트는 엔티티 여러 개를 품음) |

- **엔티티명(`user`)이 아닌 이유**: 컨텍스트는 곧 `RefreshToken`, `EmailVerification`
  등 여러 엔티티를 갖는다. `user/` 폴더에 토큰이 들어가면 어색하고, 엔티티당 폴더
  하나(package-by-entity)는 *함께 바뀌는 것들*을 잘게 흩뜨린다.
- **라우트명(`auth`)이 아닌 이유**: 디렉토리는 도메인 모델이지 HTTP 표면이 아니다.
  `auth`(인증)는 이 컨텍스트 책임의 일부일 뿐 — 신원/프로필/role/승인까지 포함하는
  Identity & Access가 더 정확하다.

작명 신호: **"이 폴더 안의 것들이 같은 이유로, 같은 시점에 바뀌는가?"** Yes면 한 컨텍스트다.

### 4.3 도메인의 세 가지 표현: entities / models / schemas

같은 "User"를 셋이 다르게 표현한다. 각자 다른 질문에 답하고, 바뀌는 이유도 다르다.

| | 파일 | 답하는 질문 | 의존성 | 바뀌는 이유 |
|---|---|---|---|---|
| **엔티티** | `entities.py` (`User`) | "사용자란 무엇이고 어떤 규칙을 따르나" | 없음 (순수) | 비즈니스 규칙 변경 |
| **모델** | `models.py` (`UserModel`) | "DB에 어떻게 저장되나" | SQLAlchemy/DB | 테이블 스키마 변경 |
| **스키마** | `schemas.py` (`*Request/*Response`) | "클라이언트와 어떤 JSON을 주고받나" | Pydantic/HTTP | API 계약 변경 |

분리의 효과를 가장 잘 보여주는 건 `password`다:

- `SignUpRequest.password` — 평문, `min_length=8` 검증 (입력에만)
- `UserResponse` — password 필드 **없음** (절대 응답에 안 나감)
- `entities.User.hashed_password` / `UserModel.hashed_password` — 해싱된 값만

셋을 합쳤다면 해시가 응답에 새거나, DB 길이 제약이 API 검증에 끼어들거나, 도메인이
평문 비밀번호를 들게 된다. 분리했기에 "입력검증 / 도메인규칙 / 저장 / 출력"을 각각
통제한다. (cf. FastAPI [Extra Models](https://fastapi.tiangolo.com/tutorial/extra-models/))

> 이름 관례: 엔티티=도메인 모델, 모델=영속성 모델, 스키마=DTO(Data Transfer Object).
> `models`=ORM, `schemas`=Pydantic 은 FastAPI 진영의 표준 관례.

## 5. 요청 한 번의 흐름 (회원가입)

```
HTTP JSON
  │  ① 검증
  ▼
SignUpRequest (schemas)            "입력이 유효한가?"  ──┐
  │                                                      │ router.py
  ▼  ② service 호출 (kwargs)                             │
AuthService.sign_up (service)                            │
  │  ③ 도메인 규칙                                       │
  │     - 이메일 중복 검사 (repo.get_by_email)           │
  │     - User.register() → 항상 approval_status=pending │
  │     - core.security.hash_password(plain)             │
  ▼                                                      │
User (entities)  ──④ repository 매핑──▶ UserModel (models) ──INSERT──▶ DB
  ▲                                                      │
  └──⑤ repository 매핑◀── UserModel (저장 결과, id 포함)  │
  │                                                      │
  ▼  ⑥ 출력 매핑                                         │
UserResponse (schemas)             "내보낼 것만 선별"  ──┘
  │
  ▼
HTTP JSON (201)
```

규칙: **schema를 곧장 model로 꽂지 않는다.** 항상 `entities`를 가운데 두고
`service`가 도메인 규칙(중복 검사·pending 강제·해싱)을 거치도록 강제한다.
ORM↔엔티티 변환은 `repository.py`, schema↔엔티티 변환은 `router.py`가 담당한다.

트랜잭션은 `core/database.py`의 `get_session` 의존성이 **요청 경계**에서 처리한다
(핸들러 성공 시 commit, 예외 시 rollback). 리포지토리는 `flush`까지만 책임진다 →
한 요청의 여러 리포지토리 호출을 한 트랜잭션으로 묶기 쉽다.

## 6. 버전 관리 전략

**API 버전 — URL path versioning**
- 경로 prefix로 노출: `/api/v1/...` (`app/api/v1.py`가 모듈 라우터를 집약).
- 한 버전 안에서는 **하위 호환(additive)** 변경만 (필드 추가 등).
- 호환 불가능한 변경은 모듈에 `router_v2.py`(필요 시 `schemas_v2.py`)를 추가하고
  `app/api/v2.py`에서 `/api/v2`로 별도 마운트. v1은 클라이언트 마이그레이션까지 유지.

**앱/릴리스 버전**
- `pyproject.toml`의 `version` + 설정 `APP_VERSION`이 단일 출처.
  `/health` 응답과 OpenAPI(`/docs`)에 노출. 릴리스는 git 태그(`v0.1.0`, SemVer).

**DB 스키마 버전**
- Alembic 리비전(`migrations/versions/`). 변경 시:
  `uv run alembic revision --autogenerate -m "설명"` → `uv run alembic upgrade head`.

## 7. 새 바운디드 컨텍스트 추가하기

`problems`, `grading` 등을 추가할 때:

1. `app/modules/<name>/` 생성, 동일 파일명 세트를 복제:
   `entities.py · models.py · repository.py · service.py · schemas.py · router.py · dependencies.py`
2. ORM 모델을 `migrations/env.py`에서 import되게 한다(메타데이터 등록).
   `alembic revision --autogenerate`로 마이그레이션 생성.
3. 모듈의 `router`를 `app/api/v1.py`에 `include_router`로 등록.
4. 도메인이 복잡하면(예: 채점 로직) 그 모듈에 한해 도메인 서비스/포트를 추가.

**모듈 간 규칙**: 컨텍스트끼리 직접 import하지 않는다. 공유가 필요한 기술 관심사는
`core/`로, 도메인 협력이 필요하면 서비스 호출/이벤트 등 명시적 경계를 둔다.

## 8. 컨벤션 요약

- 모듈 파일명 세트는 **모든 컨텍스트에서 동일**하게 유지(consistent & predictable).
  cf. [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)
- 도메인(`entities`)은 프레임워크/DB/보안 라이브러리를 import하지 않는다.
- 예외는 `core.exceptions.AppError`를 상속 → `status_code`/`code`만 정의하면
  핸들러가 `{"error": {"code", "message"}}` JSON으로 자동 변환.
- 비밀번호는 평문 저장/응답 금지. 토큰 subject는 `str(user.id)`.
- 린트/포맷: `ruff` (`uv run ruff check .`, `uv run ruff format .`).
- **테스트 갱신 필수**: 기능 추가/변경 시 `tests/`도 함께 갱신하고, 커밋 전
  `uv run pytest` 전부 통과를 확인한다. 테스트 없는 기능 변경은 미완료로 간주. (README §개발 규칙)

## 9. 현재 상태 / 로드맵

**구현됨**
- `POST /api/v1/auth/signup` — 가입(pending 유저 생성), 이메일 중복 409
- `POST /api/v1/auth/login` — JWT access/refresh 발급, 자격 불일치 401
- `GET /health` — 헬스체크 + 앱 버전

**다음 (identity)**
- [ ] `GET /api/v1/auth/me` — access token → 현재 유저 (OAuth2 Bearer 의존성, `core`에 `get_current_user`)
- [ ] `POST /api/v1/auth/refresh` — refresh token으로 access 재발급
- [ ] 관리자 승인 흐름(approval_status 전이) — mathup `auth-role-academy-class.md` 참고

**향후 컨텍스트**
- [ ] `problems` — 문제 은행 (`/problems`)
- [ ] `grading` — OCR(Gemini) + Claude 채점 파이프라인 (`/attempts`)
- [ ] `organization` — 학원/학급(Academy/Class) 관리
