"""Celery task: the worker re-parses every DSL, runs conflict detection and
persists findings. The backend route only creates the batch and dispatches."""
from app.config.celery_app import celery_app
from app.utils.logger import log_event


@celery_app.task(name="metricd.run_consistency_check", bind=True, max_retries=1)
def run_consistency_check_task(self, check_id: int):
    from app.services.check_service import execute_check

    try:
        return execute_check(check_id)
    except Exception as exc:  # execute_check records the failed state itself
        log_event("CHECK_FAILED", batch=check_id, reason=f"{type(exc).__name__}: {exc}")
        raise
