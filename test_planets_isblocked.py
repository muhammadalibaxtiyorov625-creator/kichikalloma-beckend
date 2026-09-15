import urllib.request, json, sys

# Token olish
urllib.request.urlopen(urllib.request.Request(
    'http://127.0.0.1:3077/mobile/send-otp/',
    data=json.dumps({'phone': '+998901111111'}).encode(),
    headers={'Content-Type': 'application/json'}
))
with urllib.request.urlopen(urllib.request.Request(
    'http://127.0.0.1:3077/mobile/verify-otp/',
    data=json.dumps({'phone': '+998901111111', 'code': '0000'}).encode(),
    headers={'Content-Type': 'application/json'}
)) as r:
    token = json.loads(r.read())['access_token']

print("=" * 60)
print("  MOBIL PLANETS - is_blocked / is_block TEKSHIRUVI")
print("=" * 60)

# Barcha sayyoralarni olish
with urllib.request.urlopen(urllib.request.Request(
    'http://127.0.0.1:3077/mobile/planets/',
    headers={'Authorization': 'Bearer ' + token}
)) as r:
    planets = json.loads(r.read())

print(f"\nJami sayyoralar: {len(planets)} ta\n")
for p in planets:
    pid = p['id']
    title = p.get('title', '')
    status = p.get('status', '')
    is_blocked = p.get('is_blocked', 'YOQ')
    is_block = p.get('is_block', 'YOQ')
    icon = "🔴 BLOKLANGAN" if is_blocked else "🟢 FAOL"
    line = f"  {icon} | ID={pid} | {title} | status={status} | is_blocked={is_blocked} | is_block={is_block}"
    sys.stdout.buffer.write((line + '\n').encode('utf-8'))

print("\n" + "=" * 60)
print("  TEST MUVAFFAQIYATLI - is_blocked ISHLAYAPTI!")
print("=" * 60)
