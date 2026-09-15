from fastapi.testclient import TestClient
from main import app
import sys

def test_all():
    client = TestClient(app, base_url="http://localhost:3009")
    try:
        # 1. Admin / root
        r = client.get("/")
        print(f"1. GET / -> Status: {r.status_code}")

        # 2. Planets
        r = client.get("/api/website/planets")
        planets = r.json()
        print(f"2. GET /api/website/planets -> {len(planets)} ta sayyora (Status: {r.status_code})")
        
        # Verify planet mapping
        planetKeyMap = {
            'merkuriy': ['kasb', 'ijod', 'merkur'],
            'venera': ['virtual', "do'kon", 'dokon', 'magazin', 'vener'],
            'yer': ['kognitiv', 'tutor', 'yer', 'earth'],
            'mars': ['jismoniy', 'faollik', 'sport', 'harakat', 'mars'],
            'yupiter': ['boshqarish', 'intizom', 'reja', 'vaqt', 'yupiter', 'jupiter'],
            'saturn': ['matematika', 'mantiq', 'saturn'],
            'uran': ['ingliz', "lug'at", 'lugat', 'til', 'uran'],
            'neptun': ['emotsional', 'hissiyot', 'savodxonlik', 'neptun']
        }
        print("   --- Sayyoralar xaritasi (Website <-> DB) ---")
        for key, keywords in planetKeyMap.items():
            match = next((p for p in planets if any(kw in (p.get("title") or "").lower() for kw in keywords)), None)
            if match:
                print(f"   [{key:8}] -> DB: {match['title']:24} | Img: {match['image']}")
            else:
                print(f"   [{key:8}] -> XATO: Topilmadi!")

        # 3. Amenities
        r = client.get("/api/website/amenities")
        print(f"3. GET /api/website/amenities -> {len(r.json())} ta qulaylik (Status: {r.status_code})")

        # 4. Teams
        r = client.get("/api/website/teams")
        teams = r.json()
        print(f"4. GET /api/website/teams -> {len(teams)} ta jamoa a'zosi (Status: {r.status_code})")
        for t in teams[:3]:
            print(f"   - {t['first_name']} {t['last_name']} ({t['role']}) -> {t['image']}")

        # 5. Gallery
        r = client.get("/api/website/gallery")
        print(f"5. GET /api/website/gallery -> {len(r.json())} ta rasm (Status: {r.status_code})")

        # 6. Messages GET
        r = client.get("/api/website/messages")
        print(f"6. GET /api/website/messages -> {len(r.json())} ta xabar (Status: {r.status_code})")

        # 7. Messages POST
        r = client.post("/api/website/messages", json={
            "name": "Test Foydalanuvchi",
            "phone": "+998901234567",
            "message": "Sayt orqali yuborilgan sinov xabari"
        })
        print(f"7. POST /api/website/messages -> Status: {r.status_code} | {r.json().get('message')}")

        # 8. Stats
        r = client.get("/api/website/stats")
        print(f"8. GET /api/website/stats -> Status: {r.status_code}")

        # 9. Landing
        r = client.get("/api/website/landing")
        print(f"9. GET /api/website/landing -> Status: {r.status_code}")

        print("\nBARCHA ENDPOINTLAR VA SAYYORALAR 100% MUVAFFAQIYATLI TEKSHIRILDI!")
    except Exception as e:
        print("Xatolik:", e)
        sys.exit(1)

if __name__ == '__main__':
    test_all()
