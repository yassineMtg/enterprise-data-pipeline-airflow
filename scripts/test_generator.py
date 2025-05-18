import psycopg2
import random
import time
import argparse
from datetime import datetime

DB_HOST = "postgres"
DB_PORT = "5432"
DB_NAME = "mydb"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

def get_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

def generate_test_data():
    currencies = ["Bitcoin", "Ethereum", "Litecoin", "Ripple", "Cardano"]
    return {
        "currency": random.choice(currencies),
        "price_usd": round(random.uniform(1, 100000), 2)
    }

def perform_insert(conn):
    data = generate_test_data()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO crypto_prices (currency, price_usd) VALUES (%s, %s);",
            (data["currency"], data["price_usd"]),
        )
    conn.commit()
    print(f"Inserted: {data}")

def perform_update(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM crypto_prices ORDER BY random() LIMIT 1;")
        record = cur.fetchone()
        if record:
            new_price = round(random.uniform(1, 100000), 2)
            cur.execute(
                "UPDATE crypto_prices SET price_usd = %s WHERE id = %s;",
                (new_price, record[0]),
            )
            conn.commit()
            print(f"Updated ID {record[0]} to price {new_price}")

def perform_delete(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM crypto_prices ORDER BY random() LIMIT 1;")
        record = cur.fetchone()
        if record:
            cur.execute("DELETE FROM crypto_prices WHERE id = %s;", (record[0],))
            conn.commit()
            print(f"Deleted ID {record[0]}")

def main(duration=None):
    conn = get_connection()
    actions = [perform_insert, perform_update, perform_delete]
    start_time = time.time()
    
    try:
        while True:
            if duration and (time.time() - start_time) > duration:
                break
            action = random.choice(actions)
            action(conn)
            time.sleep(random.uniform(0.5, 2))
    except KeyboardInterrupt:
        print("Stopping test generator")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, help="Duration to run in seconds")
    args = parser.parse_args()
    main(args.duration)