import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.database import get_db
from app.main import app as fastapi_app
from unittest.mock import patch
from app.config import settings

# Force MOCK_SERVICES to False during pytest execution
settings.MOCK_SERVICES = False

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    
    Session = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function", autouse=True)
def ensure_local_dev_user(db_session):
    """Ensure the local dev user exists for unauthenticated test client requests."""
    from app.models import User
    user = db_session.query(User).filter(User.id == "mock_jane_doe").first()
    if not user:
        db_session.add(User(
            id="mock_jane_doe",
            email="jane.doe@example.com",
            name="Jane Doe",
        ))
        db_session.commit()
    yield "mock_jane_doe"

@pytest.fixture(scope="function", autouse=True)
def patch_db_session(db_session):
    import app.database as database_module
    original_SessionLocal = database_module.SessionLocal
    database_module.SessionLocal = lambda: db_session

    worker_module = None
    original_get_db_session = None
    try:
        import app.worker as worker_module
        original_get_db_session = worker_module.get_db_session
        worker_module.get_db_session = lambda: db_session
    except (ImportError, ModuleNotFoundError):
        pass  # celery not available in local env; skip worker patching

    yield

    database_module.SessionLocal = original_SessionLocal
    if worker_module is not None and original_get_db_session is not None:
        worker_module.get_db_session = original_get_db_session

@pytest.fixture(scope="function")
def override_get_db(db_session):
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    return _get_db

@pytest.fixture(scope="function")
def client(override_get_db, db_session):
    import app.worker as worker_module
    
    # Override worker db session to use the same transactional test db session
    original_get_db_session = worker_module.get_db_session
    worker_module.get_db_session = lambda: db_session
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    # Global SearXNG Mock
    fake_searxng_response = {
        "query": "mock",
        "results": [
            {
                "title": "Mocked Search Result",
                "url": "https://mocked-result.com",
                "content": "This is a mocked result snippet",
                "engine": "google"
            }
        ]
    }
    
    with patch("app.services.searxng_client.SearXNGClient.search", return_value=fake_searxng_response):
        with TestClient(fastapi_app) as test_client:
            yield test_client
            
    fastapi_app.dependency_overrides.clear()
    worker_module.get_db_session = original_get_db_session
