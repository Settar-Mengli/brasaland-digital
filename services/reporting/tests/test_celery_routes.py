"""Named-queue routing config (no Redis)."""

from celery_app import celery_app
from tasks import TASK_NAME


def test_default_queue_is_reporting() -> None:
    assert celery_app.conf.task_default_queue == "reporting"


def test_run_pipeline_task_routes_to_reporting() -> None:
    routes = celery_app.conf.task_routes
    assert isinstance(routes, dict)
    assert routes[TASK_NAME]["queue"] == "reporting"
