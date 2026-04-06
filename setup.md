
``` bash
uv sync
touch .env
cd backend
uv run init_db.py
uvicorn main:app --reload 
```

## ESSENTIAL .env VARIABLES:
SECRET_KEY = ANYTHINGYOUWANT
DB_PATH = ABSOULTE LOCATION OF YOUR DATABASE FILE
MONGO_URL = ASK IN GROUP FOR THE KEY

## Database structure
for mongodb:
    user --> images

for sqlite:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
        uid           TEXT PRIMARY KEY,
        name          TEXT,
        password_hash TEXT,
        elo_rating    INTEGER DEFAULT 1200,
        is_online     INTEGER DEFAULT 0)
""")