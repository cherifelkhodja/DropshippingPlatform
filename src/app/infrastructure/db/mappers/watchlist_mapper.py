"""Watchlist Mapper.

Bidirectional mapping between Watchlist/WatchlistItem domain entities
and WatchlistModel/WatchlistItemModel ORMs.
Pure functions, no I/O, no session dependency.
"""

from uuid import UUID

from src.app.core.domain.entities.watchlist import Watchlist, WatchlistItem
from src.app.infrastructure.db.models.watchlist_model import (
    WatchlistModel,
    WatchlistItemModel,
)


def watchlist_to_domain(model: WatchlistModel) -> Watchlist:
    """Convert WatchlistModel ORM instance to Watchlist domain entity.

    Args:
        model: The WatchlistModel ORM instance.

    Returns:
        The corresponding Watchlist domain entity.
    """
    return Watchlist(
        id=str(model.id),
        name=model.name,
        description=model.description,
        created_at=model.created_at,
        is_active=model.is_active,
    )


def watchlist_to_model(entity: Watchlist) -> WatchlistModel:
    """Convert Watchlist domain entity to WatchlistModel ORM instance.

    Args:
        entity: The Watchlist domain entity.

    Returns:
        The corresponding WatchlistModel ORM instance.
    """
    return WatchlistModel(
        id=UUID(entity.id),
        name=entity.name,
        description=entity.description,
        created_at=entity.created_at,
        is_active=entity.is_active,
    )


def watchlist_item_to_domain(model: WatchlistItemModel) -> WatchlistItem:
    """Convert WatchlistItemModel ORM instance to WatchlistItem domain entity.

    Args:
        model: The WatchlistItemModel ORM instance.

    Returns:
        The corresponding WatchlistItem domain entity.
    """
    return WatchlistItem(
        id=str(model.id),
        watchlist_id=str(model.watchlist_id),
        page_id=str(model.page_id),
        created_at=model.created_at,
    )


def watchlist_item_to_model(entity: WatchlistItem) -> WatchlistItemModel:
    """Convert WatchlistItem domain entity to WatchlistItemModel ORM instance.

    Args:
        entity: The WatchlistItem domain entity.

    Returns:
        The corresponding WatchlistItemModel ORM instance.
    """
    return WatchlistItemModel(
        id=UUID(entity.id),
        watchlist_id=UUID(entity.watchlist_id),
        page_id=UUID(entity.page_id),
        created_at=entity.created_at,
    )
