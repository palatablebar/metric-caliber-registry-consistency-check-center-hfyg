"""Celery application — backend is the producer, worker is the consumer."""
from celery import Celery

from app.config.settings import settings

celery_app = Celery(
    "metricd",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.run_consistency_check"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
    task_acks_late=False,
)

# aliases so `celery -A app.config.celery_app worker` resolves
app = celery_app
celery = celery_app
