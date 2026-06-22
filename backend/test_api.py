from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

endpoints = [
    '/api/hitters/games',
    '/api/hitters/hits',
    '/api/hitters/hr',
    '/api/hitters/tb',
    '/api/hitters/bvp',
    '/api/hitters/last7',
    '/api/hitters/consensus',
    '/api/hitters/club/hits',
    '/api/hitters/club/tb',
    '/api/hitters/streak',
    '/api/hitters/hit-streaks',
]

for endpoint in endpoints:
    try:
        response = client.get(endpoint)
        data = response.json()
        if response.status_code == 200:
            if 'data' in data:
                print(f'✓ {endpoint}: {len(data.get("data", []))} records')
            elif 'games' in data:
                print(f'✓ {endpoint}: {len(data.get("games", []))} games')
            else:
                print(f'✓ {endpoint}: OK')
        else:
            print(f'✗ {endpoint}: {response.status_code}')
            if 'detail' in data:
                print(f'  Error: {data["detail"]}')
    except Exception as e:
        print(f'✗ {endpoint}: {type(e).__name__}: {e}')
