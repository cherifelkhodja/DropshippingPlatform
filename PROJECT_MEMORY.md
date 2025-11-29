# PROJECT MEMORY — Dropshipping Platform

> **Purpose**: Persistent memory file for AI assistants working on this project.
> **Last Updated**: Sprint 3.4 (Scoring Engine Complete)
> **Maintainer**: Claude Code / Tech Lead

---

## 1. META-INFORMATION

| Key | Value |
|-----|-------|
| **Project Name** | Dropshipping Platform |
| **Current Version** | v0.3.0-dev |
| **Current Sprint** | Sprint 3.4 — Scoring Engine Hardening (completed) |
| **Last Action** | Scoring module decoupled from Postgres/Celery, pagination fixed, tests added |
| **Architecture** | Hexagonal (Ports & Adapters) |
| **Python Version** | 3.11+ |
| **Package Manager** | uv (modern pyproject.toml) |
| **Coverage Threshold** | 60% (target: 85%) |

---

## 2. ARCHITECTURE STATE

### 2.1 Current Project Structure

```
DropshippingPlatform/
├── ARCHITECTURE.md              # Architecture guidelines (v2.0.0)
├── PROJECT_MEMORY.md            # This file
├── pyproject.toml               # Dependencies (runtime + dev)
├── Makefile                     # Dev workflow commands
├── alembic.ini                  # Alembic configuration
├── docker-compose.yml           # Production compose (postgres, app, redis, worker)
├── docker-compose.override.yml  # Dev overrides
├── .env.example                 # Environment template
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI
│
├── alembic/
│   ├── env.py                   # Async migrations env
│   └── versions/
│       └── 20241201_0001_*.py   # Initial migration
│
├── docker/
│   └── app.Dockerfile           # Multi-stage build
│
├── mockserver/
│   ├── server.py                # Flask mock for tests
│   └── requirements.txt
│
├── scripts/
│   └── start.sh                 # Docker entrypoint
│
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI app with lifespan, routers
│       │
│       ├── api/                 # API Layer (Sprint 2)
│       │   ├── __init__.py
│       │   ├── dependencies.py  # DI: repos, clients, use cases, task dispatcher
│       │   ├── exceptions.py    # Exception → HTTP status mapping
│       │   ├── routers/
│       │   │   ├── health.py    # GET /health
│       │   │   ├── keywords.py  # POST /api/v1/keywords/search
│       │   │   ├── pages.py     # GET /api/v1/pages, /pages/{id}
│       │   │   ├── scans.py     # GET /api/v1/scans/{id}
│       │   │   └── admin.py     # GET /api/v1/admin/pages/active, keywords/recent, scans
│       │   └── schemas/
│       │       ├── common.py    # HealthResponse, ErrorResponse
│       │       ├── keywords.py  # KeywordSearchRequest/Response
│       │       ├── pages.py     # PageResponse, PageListResponse
│       │       ├── scans.py     # ScanResponse
│       │       └── admin.py     # Admin DTOs for monitoring
│       │
│       ├── core/                # DOMAIN (protected)
│       │   ├── domain/
│       │   │   ├── entities/    # Page, Ad, Scan, KeywordRun, ShopifyProfile
│       │   │   ├── value_objects/  # Url, Country, Currency, etc.
│       │   │   └── errors.py    # Domain exceptions
│       │   ├── ports/           # Interfaces (Protocol)
│       │   └── usecases/        # Application logic
│       │
│       ├── adapters/
│       │   ├── inbound/         # (Future: CLI)
│       │   └── outbound/
│       │       ├── repositories/
│       │       │   ├── page_repository.py
│       │       │   ├── ads_repository.py
│       │       │   ├── scan_repository.py
│       │       │   └── keyword_run_repository.py
│       │       ├── meta/
│       │       │   ├── meta_ads_client.py
│       │       │   └── meta_ads_config.py
│       │       ├── scraper/
│       │       │   └── html_scraper.py
│       │       ├── sitemap/
│       │       │   └── sitemap_client.py
│       │       └── tasks/                 # Sprint 2
│       │           └── celery_task_dispatcher.py
│       │
│       └── infrastructure/
│           ├── db/
│           │   ├── database.py        # Async engine & session
│           │   ├── models/            # ORM models
│           │   └── mappers/           # Domain ↔ ORM mappers
│           ├── http/
│           │   └── base_http_client.py  # Shared HTTP with retry
│           ├── logging/               # Sprint 2.1
│           │   ├── __init__.py
│           │   ├── config.py          # Logging configuration
│           │   └── logger_adapter.py  # StandardLoggingAdapter
│           ├── celery/                # Sprint 2 + 2.1
│           │   ├── celery_app.py      # Celery configuration
│           │   ├── container.py       # Worker DI container
│           │   └── tasks.py           # Task definitions (connected to use cases)
│           └── settings/
│               └── runtime_settings.py  # Settings + SecuritySettings
│
└── tests/
    ├── conftest.py              # Fixtures + Fakes
    ├── domain/                  # Entity & VO tests
    ├── usecases/                # Use case tests
    ├── unit/                    # Unit tests
    │   └── adapters/outbound/tasks/
    │       └── test_celery_task_dispatcher.py
    └── integration/
        ├── conftest.py
        ├── test_db_repositories.py
        ├── test_html_scraper.py
        ├── test_sitemap_client.py
        ├── test_meta_ads_client.py
        ├── test_api_endpoints.py      # Sprint 2
        └── test_api_admin.py          # Sprint 2
```

### 2.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    API Layer (routers)                        │   │
│  │  /health │ /api/v1/keywords │ /api/v1/pages │ /api/v1/admin  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                │                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                 Dependency Injection                          │   │
│  │      Repos │ Clients │ Use Cases │ TaskDispatcher             │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         USE CASES                                    │
│   SearchAdsByKeyword │ AnalyseWebsite │ ExtractProductCount │ ...   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                   ┌────────────┼────────────┐
                   ▼            ▼            ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────┐
│     PORTS            │ │    PORTS             │ │   PORTS          │
│  (Repositories)      │ │  (HTTP Clients)      │ │  (TaskDispatcher)│
└──────────────────────┘ └──────────────────────┘ └──────────────────┘
          │                       │                        │
          ▼                       ▼                        ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────┐
│    ADAPTERS          │ │    ADAPTERS          │ │   ADAPTERS       │
│  PostgreSQL Repos    │ │  MetaAds, Scraper    │ │ CeleryDispatcher │
└──────────────────────┘ └──────────────────────┘ └──────────────────┘
          │                       │                        │
          ▼                       ▼                        ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────┐
│   PostgreSQL         │ │  External APIs       │ │  Redis + Worker  │
│   Database           │ │  Meta Ads Library    │ │  Celery Tasks    │
└──────────────────────┘ └──────────────────────┘ └──────────────────┘
```

### 2.3 Technology Stack

| Layer | Technology |
|-------|------------|
| **Web Framework** | FastAPI |
| **Database** | PostgreSQL + SQLAlchemy 2.0 async |
| **Migrations** | Alembic (async) |
| **Task Queue** | Celery + Redis |
| **HTTP Client** | aiohttp + Tenacity |
| **HTML Parsing** | BeautifulSoup4 |
| **XML/Sitemap** | lxml |
| **Configuration** | Pydantic Settings v2 |
| **Container** | Docker multi-stage |
| **CI/CD** | GitHub Actions |
| **Package Manager** | uv |

---

## 3. DECISION LOG (ADR)

### ADR-006: FastAPI Minimal Stub (Sprint 1)

| | |
|---|---|
| **Date** | Sprint 1 |
| **Status** | Accepted |
| **Context** | Docker healthcheck and uvicorn require a running app |
| **Decision** | Create minimal FastAPI app with `/health` endpoint only |
| **Consequences** | + Infra works, + No business logic leaked, - Empty app for now |

### ADR-007: Modern pyproject.toml + uv (Sprint 1)

| | |
|---|---|
| **Date** | Sprint 1 |
| **Status** | Accepted |
| **Context** | Need reliable dependency management for SaaS deployment |
| **Decision** | Use pyproject.toml with `[project.dependencies]` and `[project.optional-dependencies.dev]`, compatible with uv |
| **Consequences** | + Modern standard, + Fast installs with uv, + No requirements.txt needed |

### ADR-008: aiohttp over Playwright for Scraping (Sprint 1)

| | |
|---|---|
| **Date** | Sprint 1 |
| **Status** | Accepted |
| **Context** | Lightweight scraping needs vs Playwright complexity |
| **Decision** | Use aiohttp + BeautifulSoup for HtmlScraperClient |
| **Consequences** | + Lightweight, + Fast, + Easy to test, - No JS rendering |

### ADR-009: Flask Mock Server for Integration Tests (Sprint 1)

| | |
|---|---|
| **Date** | Sprint 1 |
| **Status** | Accepted |
| **Context** | Need to test HTTP clients without real external APIs |
| **Decision** | Create Flask mock server simulating robots.txt, sitemaps, Shopify pages |
| **Consequences** | + Deterministic tests, + Fast, + No API rate limits |

### ADR-010: Celery + Redis for TaskDispatcherPort (Sprint 2)

| | |
|---|---|
| **Date** | Sprint 2 |
| **Status** | Accepted |
| **Context** | Need async task execution for background jobs (scan, analysis, sitemap) |
| **Decision** | Implement TaskDispatcherPort using Celery with Redis as broker/backend |
| **Consequences** | + Battle-tested, + Scalable workers, + Native retries, - Redis dependency |

### ADR-011: HTTP Session in FastAPI Lifespan (Sprint 2)

| | |
|---|---|
| **Date** | Sprint 2 |
| **Status** | Accepted |
| **Context** | Need shared aiohttp session for all external API calls |
| **Decision** | Create session in lifespan handler, store in `app.state.http_session` |
| **Consequences** | + Connection pooling, + Single source of truth, + Proper cleanup |

### ADR-012: Exception → HTTP Status Mapping (Sprint 2)

| | |
|---|---|
| **Date** | Sprint 2 |
| **Status** | Accepted |
| **Context** | Domain errors need proper HTTP response codes |
| **Decision** | Create centralized exception handlers with explicit status mapping |
| **Consequences** | + Consistent API responses, + Domain errors preserved, + Clear error messages |

### ADR-013: StandardLoggingAdapter for LoggingPort (Sprint 2.1)

| | |
|---|---|
| **Date** | Sprint 2.1 |
| **Status** | Accepted |
| **Context** | Need structured logging with context across API and workers |
| **Decision** | Implement LoggingPort using standard library logging with context via `extra` |
| **Consequences** | + Consistent logging, + Standard tools work, + Structured context |

### ADR-014: Celery Tasks Connected to Use Cases (Sprint 2.1)

| | |
|---|---|
| **Date** | Sprint 2.1 |
| **Status** | Accepted |
| **Context** | Celery tasks were placeholders, not executing actual business logic |
| **Decision** | Create WorkerContainer for DI in workers, connect tasks to real use cases |
| **Consequences** | + Tasks execute actual logic, + DI mirrors API layer, + Testable |

### ADR-015: Admin API Key Authentication (Sprint 2.1)

| | |
|---|---|
| **Date** | Sprint 2.1 |
| **Status** | Accepted |
| **Context** | Admin endpoints exposed without authentication |
| **Decision** | Add `X-Admin-Api-Key` header validation via `SecuritySettings.admin_api_key` |
| **Consequences** | + Protected admin endpoints, + Dev mode when no key configured, + Simple to use |

### ADR-016: AsyncTask Event Loop Pattern (Sprint 2.1)

| | |
|---|---|
| **Date** | Sprint 2.1 |
| **Status** | Accepted |
| **Context** | Celery workers are sync, but use cases are async |
| **Decision** | Create new event loop per task for isolation and simplicity |
| **Consequences** | + Simple, + Isolated, - Overhead per task (acceptable for current scale) |

---

## 4. SPRINT HISTORY

### Sprint 0 — Foundation
- Domain layer complete (5 entities, 9 value objects, 15+ domain errors)
- Ports layer complete (4 repositories, 4 services, 1 logging)
- Use cases layer complete (5 use cases)
- Unit tests: 168 tests, 89.97% coverage

### Sprint 0.1 — Hardening
- Fix FakePageRepository blacklist naming
- Replace `except Exception` with specific exceptions
- Add structured logging for conversion errors

### Sprint 1 — Infrastructure & Adapters (COMPLETED)
- **Étape 1**: Database infrastructure (SQLAlchemy 2.0 async, ORM models)
- **Étape 2**: Domain ↔ ORM mappers (bidirectional, pure functions)
- **Étape 3**: SQLAlchemy repositories (4 repos implementing ports)
- **Étape 4**: Meta Ads client (aiohttp + Tenacity, pagination, rate limiting)
- **Étape 5**: HTTP clients (HtmlScraperClient, SitemapClient, BaseHttpClient)
- **Étape 6**: Full SaaS infrastructure
  - Docker Compose + multi-stage Dockerfile
  - Alembic async migrations
  - Pydantic v2 Settings
  - GitHub Actions CI
  - Makefile
  - Integration tests
  - Flask mock server
- **Corrections**: FastAPI stub, pyproject.toml dependencies

### Sprint 2 — Application Layer & Task System (COMPLETED)
- **Étape 1**: FastAPI Application Layer
  - Lifespan handler with shared HTTP session
  - API routes: health, keywords, pages, scans
  - Pydantic schemas for DTOs
  - Dependency injection system
  - Exception handlers (Domain → HTTP status)
  - 21 API integration tests
- **Étape 2**: TaskDispatcherPort (Celery + Redis)
  - Redis + Worker services in docker-compose
  - CelerySettings configuration
  - Celery app and task definitions
  - CeleryTaskDispatcher adapter
  - DI integration
  - 12 unit tests
- **Étape 3**: Admin Monitoring Endpoints
  - `/api/v1/admin/pages/active` with filters
  - `/api/v1/admin/keywords/recent`
  - `/api/v1/admin/scans` with filters
  - 12 admin tests
- **Testing**: 213 tests passing (excluding DB integration requiring PostgreSQL)

### Sprint 2.1 — Hardening & Cleanup (COMPLETED → v0.2.1)
- **Étape 1**: Celery Tasks Connected to Use Cases (P0)
  - `WorkerContainer` for worker DI (`infrastructure/celery/container.py`)
  - Tasks call real use cases (AnalysePageDeep, AnalyseWebsite, ExtractProductCount)
  - Value Object conversion (Country, ScanId, Url)
  - Structured error logging
- **Étape 2**: LoggingPort Adapter (P1)
  - `StandardLoggingAdapter` implementing `LoggingPort`
  - Global logging configuration (`configure_logging`)
  - Context support via `extra` parameter
  - Removed all `print()` statements
- **Étape 3**: DI Simplification (P2)
  - Use case factories use injected repo dependencies
  - Named loggers per use case
  - Removed repository re-instantiation
- **Étape 4**: AsyncTask Documentation (P2)
  - Documented event loop pattern in tasks.py
  - Trade-offs explained in docstrings
  - Future evolution noted (arq alternative)
- **Étape 5**: Admin API Security (P2/P3)
  - `SecuritySettings` with `admin_api_key`
  - `X-Admin-Api-Key` header validation
  - Dev mode when no key configured
  - All admin routes protected
- **CI Fixes**:
  - Fixed mypy errors in exception handlers (`type: ignore[arg-type]`)
  - Adjusted coverage threshold (60% baseline, 85% target)
  - Added `httpx` to dev dependencies for FastAPI TestClient
- **Testing**: 200+ tests passing, ~90% core coverage
- **Release**: Tagged as `v0.2.1`

### Sprint 3 — Scoring Engine (COMPLETED → v0.3.0-dev)

#### Sprint 3.1 — ShopScore Entity & ScoringRepository
- **ShopScore Entity** (`core/domain/entities/shop_score.py`)
  - Score value (0-100)
  - Tier property (Bronze/Silver/Gold/Platinum)
  - Components dict (ads_activity, shopify, creative_quality, catalog)
  - `create()` factory with validation
- **ScoringRepository Port** (`core/ports/repository_port.py`)
  - `save(score: ShopScore)` method
  - `get_latest_by_page_id(page_id)` method
  - `list_top(limit, offset)` method
  - `count()` method added in Sprint 3.4
- **ShopScoreModel** (`infrastructure/db/models/shop_score_model.py`)
  - UUID primary key, page_id FK, score float
  - JSONB components, created_at timestamp
  - Index on page_id for queries
- **shop_score_mapper** (`infrastructure/db/mappers/shop_score_mapper.py`)
  - Bidirectional mapping (domain ↔ ORM)
- **Alembic migration** for shop_scores table

#### Sprint 3.2 — ComputeShopScoreUseCase
- **Use Case** (`core/usecases/compute_shop_score.py`)
  - Calculates weighted global score:
    - Ads Activity (40%): ads count, country/platform diversity
    - Shopify Score (30%): store characteristics, currency
    - Creative Quality (20%): CTA presence, emojis, discount indicators
    - Catalog Score (10%): product count normalized to 200
  - Returns `ComputeShopScoreResult` with score, tier, components
  - Persists ShopScore via ScoringRepository
- **Helper functions**:
  - `_calc_ads_activity_score(ads)` — normalized to 50 ads
  - `_calc_shopify_score(page)` — boolean indicators
  - `_calc_creative_quality_score(ads)` — text analysis
  - `_calc_catalog_score(page)` — returns tuple with warning
- **31 unit tests** covering all scoring scenarios

#### Sprint 3.3 — Infrastructure & API Integration
- **PostgresScoringRepository** (`adapters/outbound/repositories/scoring_repository.py`)
  - SQLAlchemy async implementation
  - `save()`, `get_latest_by_page_id()`, `list_top()`, `count()`
- **Celery Task** (`infrastructure/celery/tasks.py`)
  - `tasks.compute_shop_score` task calling use case
  - WorkerContainer integration
- **API Endpoints** (`api/routers/pages.py`)
  - `GET /api/v1/pages/top` — leaderboard with pagination
  - `GET /api/v1/pages/{page_id}/score` — latest score
  - `POST /api/v1/pages/{page_id}/score/recompute` — trigger async
- **Pydantic Schemas** (`api/schemas/pages.py`)
  - `ShopScoreResponse`, `ShopLeaderboardResponse`
  - `RecomputeScoreResponse` with task_id

#### Sprint 3.4 — Hardening (Final)
- **Decoupling API from Postgres/Celery**:
  - Added `dispatch_compute_shop_score()` to TaskDispatcherPort
  - Implemented in CeleryTaskDispatcher
  - Changed dependencies.py type aliases to use Protocol interfaces
  - API uses TaskDispatcher instead of direct Celery import
- **Pagination Fix**:
  - Added `count()` method to ScoringRepository Protocol
  - Implemented with `SELECT COUNT(*)` in Postgres adapter
  - `GET /pages/top` uses count() instead of list_top(limit=10000)
- **Robustness for catalog_score**:
  - `_calc_catalog_score()` returns `tuple[float, str | None]`
  - Handles None/invalid product_count gracefully
  - Logs warning when catalog score cannot be calculated
- **Tests**:
  - 6 tier tests for ShopScore.tier property
  - Updated API tests to mock TaskDispatcher
  - Fixed CI: conftest.py supports both DATABASE_URL and TEST_DATABASE_URL
- **Testing**: 231+ tests passing

---

## 5. NEXT STEPS (TODO — Sprint 4 Draft)

| Priority | Task | Description |
|----------|------|-------------|
| **P0** | Admin Dashboard | Front-end minimal ou API-driven dashboard |
| **P1** | Observabilité | Prometheus metrics, tracing OpenTelemetry |
| **P1** | Scheduled Scoring | Periodic batch re-scoring of all pages |
| **P2** | E2E Tests | Full scenario tests end-to-end |
| **P2** | Score History | Historical score tracking and trends |

**Note**: Scoring engine completed in Sprint 3. Admin API security completed in Sprint 2.1.

---

## 6. UNCOMMITTED CODE

*None — All Sprint 2.1 code has been committed.*

---

## 7. IMPORTANT CONVENTIONS

### Commit Messages
```
<type>(<scope>): <description>
```
Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

### Branch Naming
- `main` — Production
- `develop` — Integration
- `feature/<name>` — Features
- `claude/<task-id>` — Claude Code branches

### Key Rules
1. **Domain-first**: Domain layer has NO external dependencies
2. **Ports = Protocol**: Use `typing.Protocol`, not ABC
3. **Async by default**: All I/O operations are async
4. **Typed exceptions**: Never `except Exception`, always specific
5. **Immutable VOs**: All value objects use `@dataclass(frozen=True)`
6. **HTTP Session**: Shared via `app.state.http_session` in lifespan
7. **Exception Mapping**: Domain errors → appropriate HTTP status codes
8. **Logging**: Use `StandardLoggingAdapter` for structured logging, never `print()`
9. **Admin Auth**: Admin endpoints protected via `X-Admin-Api-Key` header

---

> **Note**: Update this file at the end of each sprint or significant work session.
