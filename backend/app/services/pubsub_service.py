"""
Pub/Sub service for event publishing and decoupled workflows.
"""
from __future__ import annotations

import logging
from typing import Tuple

from google.cloud import pubsub_v1

from app.config import settings

logger = logging.getLogger(__name__)


class PubSubService:
    """Service wrapper for Google Cloud Pub/Sub operations."""

    def __init__(self) -> None:
        self.project_id = settings.gcp_project_id
        self.topic_id = settings.gcp_pubsub_topic
        self._publisher: pubsub_v1.PublisherClient | None = None

    @property
    def publisher(self) -> pubsub_v1.PublisherClient:
        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
        return self._publisher

    def health_check(self) -> Tuple[bool, str]:
        """Validate Pub/Sub setup by resolving configured topic metadata."""
        if not self.project_id or not self.topic_id:
            return False, "missing GCP_PROJECT_ID or GCP_PUBSUB_TOPIC"

        try:
            topic_path = self.publisher.topic_path(self.project_id, self.topic_id)
            self.publisher.get_topic(request={"topic": topic_path})
            return True, "connected"
        except Exception as exc:
            logger.warning("Pub/Sub health check failed: %s", exc)
            return False, str(exc)


pubsub_service = PubSubService()
