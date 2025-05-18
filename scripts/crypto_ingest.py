import psycopg2
import requests
import time
from functools import wraps

DB_HOST = "postgres"
DB_PORT = "5432"
DB_NAME = "mydb"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"

def retry_postgres(max_retries=3, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except psycopg2.OperationalError as e:
                    print(f"Connection failed: {e}. Retry {retries+1}/{max_retries}")
                    retries += 1
                    time.sleep(delay)
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator

def create_table():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crypto_prices (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                currency VARCHAR(20) NOT NULL,
                price_usd DECIMAL NOT NULL
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Table created/verified")
    except Exception as e:
        print(f"Table creation error: {e}")

@retry_postgres()
def insert_crypto_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO crypto_prices (currency, price_usd) VALUES (%s, %s);",
            ("Bitcoin", data["bitcoin"]["usd"]),
        )
        
        cur.execute(
            "INSERT INTO crypto_prices (currency, price_usd) VALUES (%s, %s);",
            ("Ethereum", data["ethereum"]["usd"]),
        )
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Inserted data at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"Insert error: {e}")
        raise

while True:
    try:
        create_table()
        insert_crypto_data()
        time.sleep(10)
    except Exception as e:
        print(f"Critical failure: {e}. Restarting in 30 seconds...")
        time.sleep(30)