# PROJECT MEMORY — Dropshipping Platform

> **Purpose**: Persistent memory file for AI assistants working on this project.
> **Last Updated**: v0.6.3 (Sprint 6 + Audit complete)
> **Maintainer**: Claude Code / Tech Lead

---

## 1. META-INFORMATION

| Key | Value |
|-----|-------|
| **Project Name** | Dropshipping Platform |
| **Current Version** | v0.6.3 |
| **Current Sprint** | Sprint 6.3 — Product Insights API + Audit (completed) |
| **Last Action** | Product insights API, centralized config, migration 0006 |
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
│       │   │   ├── entities/    # Page, Ad, Scan, KeywordRun, ShopifyProfile, ShopScore, RankedShop
│       │   │   ├── value_objects/  # Url, Country, Currency, RankingCriteria, etc.
│       │   │   ├── tiering.py   # Single source of truth for tier logic (Sprint 4.1)
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

### Sprint 3 — Scoring Engine (COMPLETED)
- **Domain Layer**:
  - `ShopScore` entity (score 0-100, components dict, tier property)
  - Score components: ads_activity, shopify, creative_quality, catalog
- **Ports & Adapters**:
  - `ScoringRepository` port: save, get_latest_by_page_id, list_top, count
  - `PostgresScoringRepository` implementation with SQLAlchemy
  - `ShopScoreModel` ORM model + mapper
- **Use Case**:
  - `ComputeShopScoreUseCase`: weighted scoring formula
    - 40% ads_activity (count, country/platform diversity)
    - 30% shopify (store signals, currency, ads presence)
    - 20% creative_quality (CTAs, emojis, discount indicators)
    - 10% catalog (product count normalized to 200)
- **Celery Task**: `compute_shop_score_task` via `TaskDispatcherPort`
- **API Endpoints**:
  - `GET /pages/{page_id}/score` - Get latest score
  - `GET /pages/top` - List top-scoring shops
  - `POST /pages/{page_id}/score/recompute` - Trigger recomputation
- **Testing**: Unit tests for use case, repository integration tests

### Sprint 4 — Ranking Engine (COMPLETED)
- **Domain Layer**:
  - `RankingCriteria` value object (limit, offset, tier, min_score, country)
  - `RankedShop` read-model projection (page_id, score, tier, url, country, name)
  - `RankedShopsResult` with pagination (items, total, has_more, page_count)
- **Ports & Adapters**:
  - Extended `ScoringRepository` with `list_ranked(criteria)`, `count_ranked(criteria)`
  - Implementation with PageModel join, tier-based score filtering
- **Use Case**:
  - `GetRankedShopsUseCase`: orchestrates list_ranked + count_ranked
- **API Endpoints**:
  - `GET /pages/ranked` - New ranked shops endpoint with filters
    - Query params: limit, offset, tier, min_score, country
    - Response: RankedShopsResponse (items + total + pagination)
  - Refactored `GET /pages/top` to use ranking use case internally
- **Testing**: Unit tests, API integration tests (22 new tests)

### Sprint 4.1 — Tiering & Scoring Consistency (COMPLETED)
- **Centralized Tiering Logic**:
  - New module: `core/domain/tiering.py` (single source of truth)
  - Functions: `score_to_tier(score)`, `tier_to_score_range(tier)`, `is_valid_tier(tier)`
  - Constants: `TIER_SCORE_RANGES`, `VALID_TIERS`, `TIERS_ORDERED`
  - Tier definitions:
    - XXL: 85-100, XL: 70-85, L: 55-70, M: 40-55, S: 25-40, XS: 0-25
- **Refactored Consumers**:
  - `ShopScore.tier` property: now uses `score_to_tier()` from tiering module
  - `RankingCriteria`: imports TIER_SCORE_RANGES/VALID_TIERS from tiering module
  - `PostgresScoringRepository`: uses `tier_to_score_range()` and `score_to_tier()`
  - `FakeScoringRepository` (tests): uses tiering module functions
- **Snapshot Tests** (guard-rails for scoring formula):
  - `test_snapshot_scoring_high_winner`: Premium shop → score 85-100, tier XXL
  - `test_snapshot_scoring_dead_shop`: Inactive shop → score ≤20, tier XS
- **Documentation**: Added reference to tiering module in relevant docstrings
- **Testing**: All 35 scoring/ranking tests passing

---

## Sprint 5 – Monitoring & Alerts (terminé)

- Watchlists :
  - Entités Watchlist & WatchlistItem, WatchlistRepository.
  - Use cases CRUD (create/get/list/add/remove/list_items).
  - API : /api/v1/watchlists (+ /items, /scan_now).

- Rescans :
  - RescoreWatchlistUseCase : déclenche compute_shop_score pour toutes les pages d'une watchlist.
  - Task Celery rescore_all_watchlists_task : rescan quotidien de toutes les watchlists actives (scheduled à 3h UTC).
  - Endpoint : POST /api/v1/watchlists/{id}/scan_now (202 Accepted + nombre de tasks dispatchées).

- Alerts Engine v1 :
  - Entité Alert + types :
    - NEW_ADS_BOOST, SCORE_JUMP, SCORE_DROP, TIER_UP, TIER_DOWN.
  - AlertRepository (save, list_by_page, list_recent).
  - DetectAlertsForPageUseCase :
    - Compare old_score/new_score, old_tier/new_tier, old_ads_count/new_ads_count.
    - Crée des alertes avec message lisible et severity.
  - Intégration dans compute_shop_score_task.
  - API :
    - GET /api/v1/alerts/{page_id} (limit, offset)
    - GET /api/v1/alerts (recent global)


### Sprint 6 — Product Domain & Insights (COMPLETED)

#### Sprint 6.1 — Product Domain & Sync
- **Domain Layer**:
  - `Product` entity (id, page_id, handle, title, url, image_url, price, synced_at)
  - `ProductExtractorPort` protocol for fetching products from Shopify stores
- **Ports & Adapters**:
  - `ProductRepository` port: upsert_many, list_by_page, get_by_id, count_by_page
  - `PostgresProductRepository` implementation with upsert (ON CONFLICT)
  - `ProductModel` ORM model + mapper
  - `ShopifyProductExtractor` adapter (fetches from /products.json API)
- **Use Case**:
  - `SyncProductsForPageUseCase`: orchestrates product sync for Shopify stores
- **API Endpoints**:
  - `GET /pages/{page_id}/products` - List products with pagination
  - `POST /pages/{page_id}/products/sync` - Trigger product sync
- **Database**: Migration 0005 (products table with UniqueConstraint)

#### Sprint 6.2 — Product-Ads Matching & Insights Engine
- **Domain Layer**:
  - `ProductInsights` entity (product, ads_count, distinct_creatives, matches, etc.)
  - `AdMatch` value object (ad, score, strength, reasons)
  - `MatchStrength` enum (STRONG, MEDIUM, WEAK, NONE)
- **Domain Services**:
  - `product_ad_matcher.py`:
    - URL matching (strong): direct URL or handle in ad link
    - Handle matching (medium): product handle in ad text
    - Text similarity (weak): fuzzy matching via SequenceMatcher
  - `MatchConfig` dataclass for customizable weights/thresholds
- **Use Case**:
  - `BuildProductInsightsForPageUseCase`:
    - Fetches products and ads for a page
    - Runs matching heuristics
    - Computes aggregated insights (promoted count, match scores)

#### Sprint 6.3 — Product Insights API
- **API Schemas** (`products.py`):
  - `MatchStrengthEnum`, `AdMatchResponse`, `ProductInsightsData`
  - `ProductInsightsEntry`, `PageProductInsightsSummary`
  - `PageProductInsightsResponse` with pagination
  - `ProductInsightsSortBy` enum (ads_count, match_score, last_seen_at)
- **API Endpoints**:
  - `GET /pages/{page_id}/products/insights` - Full insights with sorting/pagination
  - `GET /pages/{page_id}/products/{product_id}/insights` - Single product insights
  - `GET /products/{product_id}` - Direct product access
- **DI Wiring**: `BuildProductInsightsUC` dependency injection
- **Integration Tests**: 14 tests for product insights endpoints

### v0.6.3 — Audit & Cleanup (COMPLETED)

- **Architecture Verification**:
  - Confirmed API routers depend only on ports/usecases (no adapter imports) ✓
  - Confirmed domain services only depend on domain entities ✓

- **Database Indexes**:
  - Migration 0006: Added composite indexes for query optimization
    - `ix_shop_scores_page_id_created_at_desc` (shop_scores)
    - `ix_alerts_page_id_created_at_desc` (alerts)

- **Centralized Business Configuration**:
  - New module: `core/domain/config/market_intel_config.py`
  - Alert thresholds: `SCORE_CHANGE_THRESHOLD`, `ADS_BOOST_RATIO_THRESHOLD`
  - Match thresholds: `STRONG/MEDIUM/WEAK_MATCH_THRESHOLD`, `TEXT_SIMILARITY_THRESHOLD`
  - Match weights: `DEFAULT_URL/HANDLE/TEXT_SIMILARITY_WEIGHT`
  - Config classes: `AlertThresholds`, `MatchThresholds`, `MatchWeights`
  - Updated consumers: `detect_alerts_for_page.py`, `product_ad_matcher.py`

- **Celery Task Resilience**:
  - Verified `compute_shop_score_task` has alert detection in try/except (best-effort)
  - Verified `rescore_all_watchlists_task` has per-watchlist error handling

- **Integration Tests**: 145 tests collected and verified executable


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
10. **Tiering Logic**: All tier ↔ score conversions must use `core/domain/tiering.py` (single source of truth)

---

> **Note**: Update this file at the end of each sprint or significant work session.
