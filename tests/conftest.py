"""
Test configuration and fixtures
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from app.models.user import User, Role, Department
from app.core.security import get_password_hash

# Use in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture(scope="function")
def client(db: Session):
    """Create a test client with dependency override"""
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def setup_test_db(db: Session):
    """Setup test database with roles and departments"""
    # Create roles
    roles = ["student", "support", "department", "admin"]
    for role_name in roles:
        if not db.query(Role).filter(Role.name == role_name).first():
            db.add(Role(name=role_name))
    
    # Create departments
    departments = ["Bilgi Islem", "Yapi Isleri", "Ogrenci Isleri", "Akademik Danismanlik"]
    for dept_name in departments:
        if not db.query(Department).filter(Department.name == dept_name).first():
            db.add(Department(name=dept_name))
    
    db.commit()
    return db

@pytest.fixture(scope="function")
def test_user(setup_test_db: Session):
    """Create a test user"""
    student_role = setup_test_db.query(Role).filter(Role.name == "student").first()
    
    user = User(
        email="testuser@example.com",
        password_hash=get_password_hash("test123"),
        role_id=student_role.id,
        department_id=None
    )
    setup_test_db.add(user)
    setup_test_db.commit()
    setup_test_db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_support_user(setup_test_db: Session):
    """Create a test support user"""
    support_role = setup_test_db.query(Role).filter(Role.name == "support").first()
    
    user = User(
        email="support@example.com",
        password_hash=get_password_hash("support123"),
        role_id=support_role.id,
        department_id=None
    )
    setup_test_db.add(user)
    setup_test_db.commit()
    setup_test_db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_department_user(setup_test_db: Session):
    """Create a test department manager user"""
    dept_role = setup_test_db.query(Role).filter(Role.name == "department").first()
    dept = setup_test_db.query(Department).filter(Department.name == "Bilgi Islem").first()
    
    user = User(
        email="dept@example.com",
        password_hash=get_password_hash("dept123"),
        role_id=dept_role.id,
        department_id=dept.id
    )
    setup_test_db.add(user)
    setup_test_db.commit()
    setup_test_db.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user: User):
    """Get authorization headers for test user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "test123"}
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return {}

@pytest.fixture(scope="function")
def support_auth_headers(client: TestClient, test_support_user: User):
    """Get authorization headers for support user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "support@example.com", "password": "support123"}
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return {}
