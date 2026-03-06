
import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app
from backend.app.db.database import get_db, engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import uuid

# Setup test DB
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_full_auth_flow():
    print("\n--- Starting Full Auth Flow Test ---")
    
    # Generate unique user data
    unique_id = str(uuid.uuid4())[:8]
    email = f"auth_test_{unique_id}@example.com"
    password = "TestPassword123!"
    display_name = "Auth Tester"

    # 1. Test Registration
    print(f"1. Testing Registration for {email}...")
    reg_payload = {
        "email": email,
        "password": password,
        "displayName": display_name
    }
    response = client.post("/api/auth/register", json=reg_payload)
    
    # Assertions for Registration
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == email
    assert data["data"]["displayName"] == display_name
    print("   Registration successful.")

    # 2. Test Duplicate Registration
    print("2. Testing Duplicate Registration...")
    response = client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]
    print("   Duplicate registration blocked correctly.")

    # 3. Test Login (Success)
    print("3. Testing Login (Valid Credentials)...")
    login_payload = {
        "email": email,
        "password": password
    }
    response = client.post("/api/auth/login", json=login_payload)
    
    # Assertions for Login
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == email
    user_id = data["data"]["id"]
    print("   Login successful.")

    # 4. Test Login (Invalid Password)
    print("4. Testing Login (Invalid Password)...")
    bad_login_payload = {
        "email": email,
        "password": "WrongPassword"
    }
    response = client.post("/api/auth/login", json=bad_login_payload)
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
    print("   Invalid password rejected correctly.")

    # 5. Test Login (Non-existent User)
    print("5. Testing Login (Non-existent User)...")
    fake_login_payload = {
        "email": "nonexistent@example.com",
        "password": "password"
    }
    response = client.post("/api/auth/login", json=fake_login_payload)
    assert response.status_code == 401
    print("   Non-existent user rejected correctly.")

    # 6. Verify user-id header access on protected route
    print("6. Verifying Protected Route Access...")
    headers = {"X-User-Id": user_id}
    # Using /api/user/profile as a protected route example
    response = client.get("/api/user/profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["user"]["email"] == email
    print("   Protected route access verified.")

    print("\n--- Auth Flow Test Completed Successfully ---")

if __name__ == "__main__":
    try:
        test_full_auth_flow()
    except AssertionError as e:
        print(f"\n!!! TEST FAILED !!!")
        print(e)
        exit(1)
    except Exception as e:
        print(f"\n!!! ERROR !!!")
        print(e)
        exit(1)
