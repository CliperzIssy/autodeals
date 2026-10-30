"""Celery application configuration for AutoDeals background tasks."""

import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("autodeals")

celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    imports=[
        "app.tasks.scrape_task",
        "app.tasks.ai_process_task",
        "app.tasks.scheduler",
    ],
    beat_schedule={
        "check-due-searches-every-5-min": {
            "task": "app.tasks.scheduler.check_due_searches",
            "schedule": 300.0,  # every 5 minutes
        },
    },
)
