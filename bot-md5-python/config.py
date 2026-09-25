import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = (os.getenv("MD5_API_TOKEN") or os.getenv("MD5_TOKEN") or "").strip()
API_URL = "https://md5.changdelamgica.xyz/api/GetListSoiCau"
PORT = int(os.getenv("PORT", 8000))
MAX_HISTORY = 2000
WARMUP_ROUNDS = 10
FETCH_INTERVAL = 1
