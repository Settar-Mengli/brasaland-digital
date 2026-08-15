"""Named-queue routing config (no Redis)."""

from celery_app import celery_app
from tasks import TASK_NAME, TASK_NAME_APPROVAL, TASK_NAME_RESPONSE


def test_default_queue_is_rfp() -> None:
    assert celery_app.conf.task_default_queue == "rfp"


def test_rfp_tasks_route_to_rfp_queue() -> None:
    routes = celery_app.conf.task_routes
    assert isinstance(routes, dict)
    for name in (TASK_NAME, TASK_NAME_RESPONSE, TASK_NAME_APPROVAL):
        assert routes[name]["queue"] == "rfp"
