"""Shared Celery application for the autograder backend.

Configures Redis as broker and result backend, sets task timeouts,
retry policies, and concurrency alignment with the Judge0/Kata
execution-slot cap.
"""
from celery import Celery

from app.core.settings import get_settings


def create_celery_app() -> Celery:
    """Bootstrap the Celery application with settings from the environment."""
    settings = get_settings()

    app = Celery(
        "autograder",
        broker=settings.celery_broker_url,
        backend=settings.redis_url,
    )

    app.conf.update(
        # Serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",

        # Timezone
        timezone="UTC",
        enable_utc=True,

        # Concurrency: match Judge0 execution-slot cap
        worker_concurrency=settings.judge0_max_concurrent,

        # Task defaults
        task_soft_time_limit=120,   # soft limit 2 minutes
        task_time_limit=180,        # hard kill at 3 minutes
        task_acks_late=True,        # ack after completion for reliability
        worker_prefetch_multiplier=1,  # one task at a time per worker slot

        # Result expiration: 1 hour matches session TTL
        result_expires=3600,

        # Retry policy
        task_default_retry_delay=5,
        task_max_retries=3,

        # Task routing: separate queues for official and sandbox
        task_routes={
            "app.domains.runs.tasks.grade_sandbox_run": {"queue": "sandbox"},
            "app.domains.runs.tasks.grade_official_run": {"queue": "official"},
        },

        # Default queue for unrouted tasks
        task_default_queue="default",
    )

    # Auto-discover tasks in domain modules
    app.autodiscover_tasks(["app.domains.runs"])

    return app


celery_app = create_celery_app()
