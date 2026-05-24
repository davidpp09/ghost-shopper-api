import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL", "").rstrip("/")
key: str = os.environ.get("SUPABASE_KEY", "")

if not url or not key:
    raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en las variables de entorno")

supabase: Client = create_client(url, key)