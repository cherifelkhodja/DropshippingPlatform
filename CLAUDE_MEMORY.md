# Claude Memory - Dropshipping Platform

## Project Overview

Dropshipping Platform suivant une architecture hexagonale stricte:
- `core/domain/` - Entités, Value Objects, Errors
- `core/ports/` - Interfaces (Protocol) pour les repositories et services
- `core/usecases/` - Logique métier
- `adapters/outbound/` - Implémentations concrètes (Postgres, Celery, HTTP clients)
- `api/` - FastAPI routers, schemas, dependencies
- `infrastructure/` - Celery, DB, Logging

---

## Sprint History

### Sprint 3.1 - Scoring Engine Foundations
**Date:** 2024-12
**Commit:** `2e48f9a`

**Objectif:** Poser les bases du Scoring Engine

**Fichiers créés:**
- `src/app/core/domain/entities/shop_score.py` - Entité ShopScore avec score clamping (0-100)
- `src/app/core/ports/repository_port.py` - Ajout ScoringRepository Protocol
- `src/app/infrastructure/db/models/shop_score_model.py` - ORM model avec JSONB components
- `src/app/infrastructure/db/mappers/shop_score_mapper.py` - Domain ↔ ORM conversion
- `src/app/adapters/outbound/repositories/scoring_repository.py` - PostgresScoringRepository
- `alembic/versions/20241201_0002_create_shop_scores_table.py` - Migration
- `tests/integration/test_scoring_repository.py` - Tests d'intégration

---

### Sprint 3.2 - ComputeShopScoreUseCase
**Date:** 2024-12
**Commit:** `7d5d62b`

**Objectif:** Implémenter le calcul de score avec pondération

**Formule de scoring:**
- Ads Activity Score (40%) - basé sur nombre d'ads, diversité pays/plateformes
- Shopify Score (30%) - basé sur is_shopify, currency, active_ads
- Creative Quality Score (20%) - basé sur analyse du contenu des ads
- Catalog Score (10%) - basé sur product_count (normalisé à 200)

**Fichiers créés:**
- `src/app/core/usecases/compute_shop_score.py` - Use case principal
- `tests/usecases/test_compute_shop_score.py` - 18 tests unitaires

**Classes principales:**
```python
class ComputeShopScoreUseCase:
    def __init__(self, page_repository, ads_repository, scoring_repository, logger)
    async def execute(self, page_id: str) -> ComputeShopScoreResult

@dataclass(frozen=True)
class ComputeShopScoreResult:
    shop_score: ShopScore
    page_id: str
    global_score: float
    components: dict[str, float]
```

---

### Sprint 3.3 - Infrastructure & API Integration
**Date:** 2024-12
**Commit:** `be4750b`

**Objectif:** Intégrer le Scoring Engine dans l'infra et l'API

**Fichiers créés/modifiés:**
- `src/app/infrastructure/celery/tasks.py` - Ajout `compute_shop_score_task`
- `src/app/infrastructure/celery/container.py` - Ajout factory `get_compute_shop_score_use_case`
- `src/app/api/schemas/scoring.py` - ShopScoreResponse, TopShopsResponse, RecomputeScoreResponse
- `src/app/api/routers/pages.py` - Endpoints scoring
- `src/app/api/dependencies.py` - ScoringRepo, ComputeShopScoreUC

**Endpoints API:**
- `GET /pages/{page_id}/score` - Récupérer le score d'une page
- `GET /pages/top` - Classement des top shops
- `POST /pages/{page_id}/score/recompute` - Dispatcher le recalcul

**Tests ajoutés:**
- 2 tests Celery task
- 7 tests API endpoints

---

### Sprint 3.4 - Hardening & Architecture
**Date:** 2024-12
**Commits:** `4585dcf`, `9467dc7`

**Objectif:** Hardening du module pour respecter l'architecture hexagonale

**1. Découplage API des implémentations concrètes:**
- Type aliases utilisent maintenant les Protocol interfaces (PageRepository, ScoringRepository, TaskDispatcherPort)
- Suppression import direct de `compute_shop_score_task` dans router
- Utilisation de `TaskDispatcher.dispatch_compute_shop_score()` au lieu de `.delay()`

**2. Pagination améliorée `/pages/top`:**
- Ajout méthode `count()` au ScoringRepository port
- Implémentation `count()` dans PostgresScoringRepository avec SQL COUNT
- Remplacement du hack `list_top(limit=10000)` par `count()`

**3. Robustesse catalog_score:**
- `_calc_catalog_score()` retourne maintenant `tuple[float, str | None]`
- Gestion gracieuse de product_count None ou <= 0
- Logging des warnings via LoggingPort

**4. Nouveaux tests:**
- 6 tests pour la propriété `tier` de ShopScore (XS/S/M/L/XL/XXL)
- MAJ tests catalog_score pour le nouveau type de retour
- MAJ tests API pour mocker TaskDispatcher

**5. Fix CI:**
- `tests/integration/conftest.py` - Support de DATABASE_URL en plus de TEST_DATABASE_URL

**Fichiers modifiés:**
| Fichier | Changements |
|---------|-------------|
| `core/ports/task_dispatcher_port.py` | +`dispatch_compute_shop_score()` |
| `core/ports/repository_port.py` | +`count()` à ScoringRepository |
| `adapters/outbound/tasks/celery_task_dispatcher.py` | +impl `dispatch_compute_shop_score()` |
| `adapters/outbound/repositories/scoring_repository.py` | +impl `count()` |
| `api/dependencies.py` | Type aliases → Protocol interfaces |
| `api/routers/pages.py` | TaskDispatcher + count() |
| `core/usecases/compute_shop_score.py` | `_calc_catalog_score` tuple + logging |

---

## Architecture Patterns

### Repository Pattern
```python
# Port (interface)
class ScoringRepository(Protocol):
    async def save(self, score: ShopScore) -> None: ...
    async def get_latest_by_page_id(self, page_id: str) -> ShopScore | None: ...
    async def list_top(self, limit: int, offset: int) -> list[ShopScore]: ...
    async def count(self) -> int: ...

# Adapter (implementation)
class PostgresScoringRepository:
    def __init__(self, session: AsyncSession): ...
```

### TaskDispatcher Pattern
```python
# Port
class TaskDispatcherPort(Protocol):
    async def dispatch_compute_shop_score(self, page_id: str) -> str: ...

# Adapter
class CeleryTaskDispatcher(TaskDispatcherPort):
    def __init__(self, celery_app: Celery, logger: Logger): ...
```

### FastAPI Dependency Injection
```python
# Type aliases using Protocol interfaces
PageRepo = Annotated[PageRepository, Depends(get_page_repository)]
ScoringRepo = Annotated[ScoringRepository, Depends(get_scoring_repository)]
TaskDispatcher = Annotated[TaskDispatcherPort, Depends(get_task_dispatcher)]
```

---

## Tier Classification

Le tier est calculé depuis le score via la propriété `ShopScore.tier`:

| Tier | Score Range |
|------|-------------|
| XXL  | >= 85       |
| XL   | >= 70       |
| L    | >= 55       |
| M    | >= 40       |
| S    | >= 25       |
| XS   | < 25        |

---

## Tests Coverage

**Total tests scoring:** 31+
- `tests/usecases/test_compute_shop_score.py` - 24 tests (use case + helpers + tiers)
- `tests/integration/test_api_endpoints.py::TestScoringEndpoints` - 7 tests
- `tests/unit/infrastructure/celery/test_tasks.py::TestComputeShopScoreTask` - 2 tests
- `tests/integration/test_scoring_repository.py` - Tests repo intégration

---

## Next Steps (Potential)

- [ ] Scheduler pour recalcul périodique des scores
- [ ] Webhooks pour notification de changement de tier
- [ ] Dashboard analytics pour visualisation des scores
- [ ] Export CSV/Excel des top shops
- [ ] Filtres avancés sur `/pages/top` (par tier, date, etc.)
