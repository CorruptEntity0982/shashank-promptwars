from celery import Celery
from app.config import settings
from app.tasks.document_tasks import process_document as process_document_impl

celery_app = Celery(
    "openclaims_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="process_document")
def process_document(document_id: str):
    """
    Celery task wrapper for document processing
    
    Args:
        document_id: UUID of the document to process
    """
    return process_document_impl(document_id)
