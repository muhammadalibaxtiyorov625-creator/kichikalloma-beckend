import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_coins():
    # 1. Balance
    r = client.get("/mobile/coins/balance/")
    print("1. Balance status:", r.status_code, "Body:", r.json())
    assert r.status_code == 200

    # 2. Earn
    r = client.post("/mobile/coins/earn/", json={"child_id": 1, "amount": 20, "title": "Topshiriq", "source": "test"})
    print("2. Earn status:", r.status_code, "Body:", r.json())
    assert r.status_code == 200

    # 3. History
    r = client.get("/mobile/coins/history/")
    print("3. History count:", len(r.json()))
    assert r.status_code == 200

    # 4. Missions
    r = client.get("/mobile/coins/missions/")
    print("4. Missions count:", len(r.json()))
    assert r.status_code == 200

    # 5. Shop
    r = client.get("/mobile/coins/shop/")
    print("5. Shop items:", len(r.json()))
    assert r.status_code == 200

    # 6. Leaderboard
    r = client.get("/mobile/coins/leaderboard/")
    print("6. Leaderboard items:", len(r.json()))
    assert r.status_code == 200

    print("ALL TESTS PASSED!")

if __name__ == "__main__":
    test_coins()
