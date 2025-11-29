"""Ad Mapper.

Bidirectional mapping between Ad domain entity and AdModel ORM.
Pure functions, no I/O, no session dependency.
"""

from uuid import UUID

from src.app.core.domain.entities.ad import Ad, AdPlatform, AdStatus
from src.app.core.domain.value_objects import Country, Url
from src.app.infrastructure.db.models.ad_model import AdModel


def _platform_to_string(platform: AdPlatform) -> str:
    """Convert AdPlatform enum to string."""
    return platform.value


def _string_to_platform(value: str) -> AdPlatform:
    """Convert string to AdPlatform enum."""
    for platform in AdPlatform:
        if platform.value == value:
            return platform
    return AdPlatform.UNKNOWN


def _status_to_string(status: AdStatus) -> str:
    """Convert AdStatus enum to string."""
    return status.value


def _string_to_status(value: str) -> AdStatus:
    """Convert string to AdStatus enum."""
    for status in AdStatus:
        if status.value == value:
            return status
    return AdStatus.UNKNOWN


def to_domain(model: AdModel) -> Ad:
    """Convert AdModel ORM instance to Ad domain entity.

    Args:
        model: The AdModel ORM instance.

    Returns:
        The corresponding Ad domain entity.
    """
    return Ad(
        id=str(model.id),
        page_id=str(model.page_id),
        meta_page_id=model.meta_page_id,
        meta_ad_id=model.meta_ad_id,
        title=model.title,
        body=model.body,
        link_url=Url(value=model.link_url) if model.link_url else None,
        image_url=Url(value=model.image_url) if model.image_url else None,
        video_url=Url(value=model.video_url) if model.video_url else None,
        cta_type=model.cta_type,
        status=_string_to_status(model.status),
        platforms=[_string_to_platform(p) for p in model.platforms],
        countries=[Country(code=c) for c in model.countries],
        started_at=model.started_at,
        ended_at=model.ended_at,
        impressions_lower=model.impressions_lower,
        impressions_upper=model.impressions_upper,
        spend_lower=model.spend_lower,
        spend_upper=model.spend_upper,
        currency=model.currency,
        first_seen_at=model.first_seen_at,
        last_seen_at=model.last_seen_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_model(entity: Ad) -> AdModel:
    """Convert Ad domain entity to AdModel ORM instance.

    Args:
        entity: The Ad domain entity.

    Returns:
        The corresponding AdModel ORM instance.
    """
    return AdModel(
        id=UUID(entity.id),
        page_id=UUID(entity.page_id),
        meta_page_id=entity.meta_page_id,
        meta_ad_id=entity.meta_ad_id,
        title=entity.title,
        body=entity.body,
        link_url=entity.link_url.value if entity.link_url else None,
        image_url=entity.image_url.value if entity.image_url else None,
        video_url=entity.video_url.value if entity.video_url else None,
        cta_type=entity.cta_type,
        status=_status_to_string(entity.status),
        platforms=[_platform_to_string(p) for p in entity.platforms],
        countries=[c.code for c in entity.countries],
        started_at=entity.started_at,
        ended_at=entity.ended_at,
        impressions_lower=entity.impressions_lower,
        impressions_upper=entity.impressions_upper,
        spend_lower=entity.spend_lower,
        spend_upper=entity.spend_upper,
        currency=entity.currency,
        first_seen_at=entity.first_seen_at,
        last_seen_at=entity.last_seen_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
