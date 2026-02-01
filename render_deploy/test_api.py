"""
Simple API test script
Run: python test_api.py [base_url]
"""

import requests
import json
import sys

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"

def test_health():
    print("\n=== Health Check ===")
    r = requests.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    return r.status_code == 200

def test_characters():
    print("\n=== Characters ===")
    r = requests.get(f"{BASE_URL}/api/v1/characters")
    print(f"Status: {r.status_code}")
    data = r.json()
    if data.get('success'):
        for c in data.get('characters', []):
            print(f"  - {c['id']}: {c['name']} ({c.get('specialty', '')})")
    return r.status_code == 200

def test_remedies():
    print("\n=== Saturn Remedies ===")
    r = requests.get(f"{BASE_URL}/api/v1/remedies/saturn")
    print(f"Status: {r.status_code}")
    data = r.json()
    if data.get('success'):
        remedies = data.get('remedies', {})
        print(f"  Day: {remedies.get('day')}")
        print(f"  Mantra: {remedies.get('mantra', {}).get('simple')}")
        print(f"  Gemstone: {remedies.get('gemstone', {}).get('primary')}")
    return r.status_code == 200

def test_chat():
    print("\n=== Chat Test (AstroVoice Format) ===")
    payload = {
        "user_id": 1,
        "query": "meri career kaisi rahegi?",
        "session_id": "test_123",

        # Character object (REQUIRED - exact AstroVoice format)
        "character": {
            "id": "career",
            "name": "Maya Astro",
            "age": 32,
            "experience": 10,
            "specialty": "Career & Life Purpose",
            "language_style": "professional",
            "about": "A modern career-focused astrologer"
        },

        # Birth data
        "name": "Test User",
        "birth_date": "27/02/2006",
        "birth_time": "05:20",
        "birth_location": "Mysuru, India",
        "latitude": 12.305,
        "longitude": 76.655,
        "timezone": "Asia/Kolkata",
        "conversation_history": []
    }

    r = requests.post(f"{BASE_URL}/api/v1/chat", json=payload)
    print(f"Status: {r.status_code}")
    data = r.json()

    if data.get('success'):
        print(f"\nCharacter: {data.get('character', {}).get('name')}")
        print(f"Response: {data.get('response')}")
    else:
        print(f"Error: {data.get('error')}")

    return r.status_code == 200

def test_chat_followup():
    print("\n=== Chat Follow-up (Cache Test) ===")
    payload = {
        "user_id": 1,
        "query": "aur batao, kab tak success milegi?",
        "session_id": "test_123",

        # Character object (REQUIRED)
        "character": {
            "id": "career",
            "name": "Maya Astro",
            "age": 32,
            "experience": 10,
            "specialty": "Career & Life Purpose",
            "language_style": "professional",
            "about": "A modern career-focused astrologer"
        },

        "name": "Test User",
        "birth_date": "27/02/2006",
        "birth_time": "05:20",
        "birth_location": "Mysuru, India",
        "latitude": 12.305,
        "longitude": 76.655,
        "timezone": "Asia/Kolkata",
        "conversation_history": [
            {"role": "user", "content": "meri career kaisi rahegi?"},
            {"role": "assistant", "content": "Teri kundali mein 10th house Scorpio hai"}
        ]
    }

    r = requests.post(f"{BASE_URL}/api/v1/chat", json=payload)
    print(f"Status: {r.status_code}")
    data = r.json()

    if data.get('success'):
        print(f"Response: {data.get('response')}")
        print("✅ Follow-up working!")
    else:
        print(f"Error: {data.get('error')}")

    return r.status_code == 200


if __name__ == "__main__":
    print(f"Testing API at: {BASE_URL}")
    print("=" * 50)

    results = {
        "health": test_health(),
        "characters": test_characters(),
        "remedies": test_remedies(),
        "chat": test_chat(),
        "cache": test_chat_followup()
    }

    print("\n" + "=" * 50)
    print("RESULTS:")
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test}: {status}")
