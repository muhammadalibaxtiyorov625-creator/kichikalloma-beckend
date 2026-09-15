import urllib.request
import json
import sys

# Windows konsolida UTF-8 ni to'g'ri ko'rsatish
sys.stdout.reconfigure(encoding='utf-8')

def test_ai_age(age, question):
    payload = {
        'message': question,
        'child_name': 'Akmal',
        'child_age': age,
        'planet_id': 42,
        'language': 'uzb'
    }
    req = urllib.request.Request(
        'http://127.0.0.1:3009/api/website/ai/chat',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(f"\n================ YOSH: {age} YOSH | SAVOL: \"{question}\" ================")
        print("AI Javobi:\n" + res.get('response', ''))
        print("\nAudio URL: " + str(res.get('audio_url', '')))

if __name__ == '__main__':
    test_ai_age(5, "5 ga 5 ni qo'shsak nechta bo'ladi?")
    test_ai_age(12, "5 ga 5 ni qo'shsak nechta bo'ladi?")
