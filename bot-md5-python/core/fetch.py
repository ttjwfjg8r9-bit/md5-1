import httpx
from config import API_URL, TOKEN


async def fetch_data():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            res = await client.get(API_URL, headers=headers)
            res.raise_for_status()
            data = res.json()
            return data if isinstance(data, list) else None
        except Exception as e:
            print(f"Lỗi fetch: {e}")
            return None
