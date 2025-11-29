# PROJECT MEMORY — Dropshipping Platform

> **Purpose**: Persistent memory file for AI assistants working on this project.
> **Last Updated**: Sprint 2 (completed)
> **Maintainer**: Claude Code / Tech Lead

---

## 1. META-INFORMATION

| Key | Value |
|-----|-------|
| **Project Name** | Dropshipping Platform |
| **Current Sprint** | Sprint 2 (completed) |
| **Last Action** | Add Application Layer + Celery Task System + Admin Endpoints |
| **Architecture** | Hexagonal (Ports & Adapters) |
| **Python Version** | 3.11+ |
| **Package Manager** | uv (modern pyproject.toml) |
| **Coverage Target** | ≥ 85% |

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
│           ├── celery/                # Sprint 2
│           │   ├── celery_app.py      # Celery configuration
│           │   └── tasks.py           # Task definitions
│           └── settings/
│               └── runtime_settings.py  # Pydantic v2 settings + CelerySettings
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

---

## 5. NEXT STEPS (TODO — Sprint 3 Draft)

| Priority | Task | Description |
|----------|------|-------------|
| **P0** | Admin Dashboard | Front-end minimal ou API-driven dashboard |
| **P1** | Filtres avancés | Scoring des shops, filtres multicritères |
| **P1** | Observabilité | Prometheus metrics, logs structurés, tracing |
| **P2** | Sécurité & Auth | API keys / JWT authentication |
| **P2** | E2E Tests | Full scenario tests end-to-end |

---

## 6. UNCOMMITTED CODE

*None — All Sprint 2 code has been committed.*

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

---

> **Note**: Update this file at the end of each sprint or significant work session.
