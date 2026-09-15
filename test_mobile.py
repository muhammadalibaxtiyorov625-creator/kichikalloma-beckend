import urllib.request
import urllib.error
import json
import time
import sys
import sqlite3

BASE_PORT = sys.argv[1] if len(sys.argv) > 1 else "3077"
BASE_URL = f"http://127.0.0.1:{BASE_PORT}"

def req(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as res:
            res_body = res.read().decode("utf-8")
            return res.status, json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"detail": err_body}
        return e.code, err_json

def test_full_features():
    print("="*60)
    print("  MOBIL API, CODE-ACCESS BOLA MA'LUMOTLARI & AI TESTLARI")
    print("="*60)

    test_phone = f"+99893{int(time.time()) % 10000000:07d}"

    # 1. Tillar ro'yxatini olish (uzb, rus, eng)
    status, langs = req(f"{BASE_URL}/mobile/languages/", "GET")
    print(f"\n1. GET /mobile/languages/ -> Status: {status}")
    print(f"   Mavjud tillar: {[l['code'] for l in langs]}")
    assert status == 200

    # 2. Yangi foydalanuvchi: OTP va Token olish
    status, data = req(f"{BASE_URL}/mobile/send-otp/", "POST", {"phone": test_phone})
    otp_code = data["code"]
    status, data = req(f"{BASE_URL}/mobile/verify-otp/", "POST", {"phone": test_phone, "code": otp_code})
    token = data["access_token"]
    assert data["is_new_user"] is True
    print(f"\n2. Yangi Foydalanuvchi Tokeni: {token[:25]}...")

    # 3. CODE-ACCESS: Yangi foydalanuvchi bo'lganda (is_new_user == True) -> child_id: null, child: null, children: []
    status, code_res = req(f"{BASE_URL}/mobile/code-access/", "POST", {"code": "4455"}, token=token)
    print(f"\n3. POST /mobile/code-access/ (Yangi foydalanuvchi) -> Status: {status}")
    print(f"   is_new_user: {code_res.get('is_new_user')}")
    print(f"   child_id: {code_res.get('child_id')}")
    print(f"   child: {code_res.get('child')}")
    print(f"   children: {code_res.get('children')}")
    assert status == 200
    assert code_res["is_new_user"] is True
    assert code_res["child_id"] is None
    assert code_res["child"] is None
    assert code_res["children"] == []

    # 4. Farzand qo'shish
    child_payload = {
        "name": "Samir",
        "surname": "Ibrohimov",
        "year": "14/02/2019",
        "gender": "male",
        "language": "uzb"
    }
    status, res = req(f"{BASE_URL}/mobile/add-child/", "POST", child_payload, token=token)
    print(f"\n4. POST /mobile/add-child/ -> Status: {status}")
    child = res["child"]
    child_id = child["id"]
    print(f"   Farzand qo'shildi: ID={child_id}, Ismi={child['name']}, Tili={child['language']}")
    assert status == 201

    # 5. CODE-ACCESS: Endi foydalanuvchida bola bor (is_new_user == False) -> child_id, child va children to'liq qaytadi!
    status, code_res = req(f"{BASE_URL}/mobile/code-access/", "POST", {"code": "4455"}, token=token)
    print(f"\n5. POST /mobile/code-access/ (Mavjud bola bilan) -> Status: {status}")
    print(f"   is_new_user: {code_res.get('is_new_user')}")
    print(f"   child_id: {code_res.get('child_id')}")
    print(f"   child nomi: {code_res.get('child', {}).get('name')} {code_res.get('child', {}).get('surname')}")
    print(f"   children soni: {len(code_res.get('children', []))} ta")
    assert status == 200
    assert code_res["is_new_user"] is False
    assert code_res["child_id"] == child_id
    assert code_res["child"]["name"] == "Samir"
    assert len(code_res["children"]) >= 1

    # 6. Farzand Tilini o'zgartirish (rus)
    status, lang_res = req(f"{BASE_URL}/mobile/child-profile/{child_id}/set-language/", "POST", {"language": "rus"}, token=token)
    print(f"\n6. POST /mobile/child-profile/{child_id}/set-language/ ('rus') -> Status: {status}")
    sys.stdout.buffer.write((f"   Xabar: {lang_res.get('message')}\n").encode('utf-8'))
    assert status == 200

    # 7. Mobil Sayyoralar (Token orqali)
    status, planets = req(f"{BASE_URL}/mobile/planets/", "GET", token=token)
    print(f"\n7. GET /mobile/planets/ -> Status: {status} ({len(planets)} ta sayyora)")
    assert status == 200

    print("\n" + "="*60)
    print("  CODE-ACCESS BOLA MA'LUMOTLARI VA BARCHA TESTLAR 100% ISHLAMOQDA!")
    print("="*60)

if __name__ == "__main__":
    test_full_features()
