"""
BigQuery service for analytics and structured reporting.
"""
from __future__ import annotations

import logging
from typing import Tuple

from google.cloud import bigquery

from app.config import settings

logger = logging.getLogger(__name__)


class BigQueryService:
    """Service wrapper for Google BigQuery operations."""

    def __init__(self) -> None:
        self.project_id = settings.gcp_project_id
        self.dataset = settings.gcp_bigquery_dataset
        self._client: bigquery.Client | None = None

    @property
    def client(self) -> bigquery.Client:
        if self._client is None:
            if self.project_id:
                self._client = bigquery.Client(project=self.project_id)
            else:
                self._client = bigquery.Client()
        return self._client

    def health_check(self) -> Tuple[bool, str]:
        """Run a lightweight BigQuery query to verify service connectivity."""
        try:
            query_job = self.client.query("SELECT 1 AS ok")
            _ = list(query_job.result(timeout=8))
            return True, "connected"
        except Exception as exc:
            logger.warning("BigQuery health check failed: %s", exc)
            return False, str(exc)


bigquery_service = BigQueryService()
