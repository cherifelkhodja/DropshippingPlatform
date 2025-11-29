# PROJECT MEMORY — Dropshipping Platform

> **Purpose**: Persistent memory file for AI assistants working on this project.
> **Last Updated**: Sprint 1 (completed)
> **Maintainer**: Claude Code / Tech Lead

---

## 1. META-INFORMATION

| Key | Value |
|-----|-------|
| **Project Name** | Dropshipping Platform |
| **Current Sprint** | Sprint 1 (completed) |
| **Last Action** | Sprint 1 Infra Runtime + Corrections |
| **Architecture** | Hexagonal (Ports & Adapters) |
| **Python Version** | 3.11+ |
| **Package Manager** | uv (modern pyproject.toml) |
| **Coverage Target** | ≥ 85% |

---

## 2. ARCHITECTURE STATE

### 2.1 Current Project Structure

```
DropshippingPlatform/
├── ARCHITECTURE.md              # Architecture guidelines (v1.1.0)
├── PROJECT_MEMORY.md            # This file
├── pyproject.toml               # Dependencies (runtime + dev)
├── Makefile                     # Dev workflow commands
├── alembic.ini                  # Alembic configuration
├── docker-compose.yml           # Production compose
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
│       ├── main.py              # FastAPI app with /health
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
│       │   ├── inbound/         # (Sprint 2)
│       │   └── outbound/
│       │       ├── repositories/
│       │       │   ├── postgres_page_repository.py
│       │       │   ├── postgres_ads_repository.py
│       │       │   ├── postgres_scan_repository.py
│       │       │   └── postgres_keyword_run_repository.py
│       │       ├── meta/
│       │       │   ├── meta_ads_client.py
│       │       │   └── meta_ads_config.py
│       │       ├── scraper/
│       │       │   └── html_scraper_client.py
│       │       └── sitemap/
│       │           └── sitemap_client.py
│       │
│       └── infrastructure/
│           ├── db/
│           │   ├── database.py        # Async engine & session
│           │   ├── models/            # ORM models
│           │   └── mappers/           # Domain ↔ ORM mappers
│           ├── http/
│           │   └── base_http_client.py  # Shared HTTP with retry
│           └── settings/
│               └── runtime_settings.py  # Pydantic v2 settings
│
└── tests/
    ├── conftest.py              # Fixtures + Fakes
    ├── domain/                  # Entity & VO tests
    ├── usecases/                # Use case tests
    └── integration/             # Adapter integration tests
        ├── conftest.py
        ├── test_db_repositories.py
        ├── test_html_scraper.py
        ├── test_sitemap_client.py
        └── test_meta_ads_client.py
```

### 2.2 Technology Stack

| Layer | Technology |
|-------|------------|
| **Web Framework** | FastAPI |
| **Database** | PostgreSQL + SQLAlchemy 2.0 async |
| **Migrations** | Alembic (async) |
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

---

## 5. NEXT STEPS (TODO — Sprint 2 Draft)

| Priority | Task | Description |
|----------|------|-------------|
| **P0** | FastAPI Endpoints | Implement API routes, schemas, dependencies |
| **P0** | TaskDispatcherPort | Celery implementation for async tasks |
| **P1** | Admin Dashboard API | Listing pages, scans, statistics |
| **P1** | Structured Logging | structlog implementation |
| **P2** | E2E Tests | Full scenario tests |

---

## 6. UNCOMMITTED CODE

*None — All Sprint 1 code has been committed.*

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

---

> **Note**: Update this file at the end of each sprint or significant work session.
