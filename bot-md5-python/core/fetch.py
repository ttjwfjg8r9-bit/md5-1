import httpx
from config import API_URL, TOKEN


async def fetch_data():
    token = (TOKEN or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    if not token:
        print("Lỗi fetch: MD5_API_TOKEN rỗng hoặc không hợp lệ. Vui lòng set biến môi trường MD5_API_TOKEN trên Railway.")
        return None

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            res = await client.get(API_URL, headers=headers)
            res.raise_for_status()
            data = res.json()
            return data if isinstance(data, list) else None
        except httpx.HTTPStatusError as e:
            print(f"Lỗi fetch HTTP: {e}")
            return None
        except httpx.InvalidHeader as e:
            print(f"Lỗi fetch header không hợp lệ: {e}")
            return None
        except Exception as e:
            print(f"Lỗi fetch: {e}")
            return None
