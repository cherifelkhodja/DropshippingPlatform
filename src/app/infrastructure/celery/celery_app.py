"""Celery Application Configuration.

Configures the Celery application for async task processing.
"""

from celery import Celery

from ..settings.runtime_settings import get_settings

settings = get_settings()

celery_app = Celery(
    "dropshipping_tasks",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=["src.app.infrastructure.celery.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer=settings.celery.task_serializer,
    result_serializer=settings.celery.result_serializer,
    accept_content=settings.celery.accept_content,
    timezone=settings.celery.timezone,
    enable_utc=True,
    task_track_started=settings.celery.task_track_started,
    task_time_limit=settings.celery.task_time_limit,
    task_soft_time_limit=settings.celery.task_soft_time_limit,
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)
