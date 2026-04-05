
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