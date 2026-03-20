from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Support Cloud SQL connection via Unix socket for Cloud Run
if settings.gcp_cloud_sql_connection_name:
    import urllib.parse
    # Create the connection URL for Cloud SQL
    # Format: postgresql+psycopg2://<user>:<password>@/<dbname>?host=/cloudsql/<connection_name>
    
    # Parse existing URL to extract credentials
    parsed_url = urllib.parse.urlparse(settings.postgres_url)
    user = parsed_url.username
    password = parsed_url.password
    dbname = parsed_url.path.lstrip('/')
    
    db_url = f"postgresql+psycopg2://{user}:{password}@/{dbname}?host=/cloudsql/{settings.gcp_cloud_sql_connection_name}"
else:
    db_url = settings.postgres_url

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Dependency for getting database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
