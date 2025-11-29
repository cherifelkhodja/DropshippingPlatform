"""Task dispatcher adapters.

Provides implementations of TaskDispatcherPort.
"""

from .celery_task_dispatcher import CeleryTaskDispatcher

__all__ = ["CeleryTaskDispatcher"]
