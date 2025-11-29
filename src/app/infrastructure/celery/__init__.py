"""Celery infrastructure module.

Provides Celery application configuration and task definitions.
"""

from .celery_app import celery_app

__all__ = ["celery_app"]
