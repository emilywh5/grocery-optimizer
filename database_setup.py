import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def setup_and_seed_database():
    conn = None
    cur = None
    try:
        # load existing JSON data
        print("Loading data from inventory.json")
        with open("inventory.json", "r") as f:
            raw_data = json.load(f)

        print("Connecting to PostgreSQL database")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Removing any existing tables")
        cur.execute("DROP TABLE IF EXISTS scraped_inventory;")
        cur.execute("DROP TABLE IF EXISTS stores;")

        print("Designing database schema")

        cur.execute("""
            CREATE TABLE stores (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                travel_time INTEGER NOT NULL    
            );
        """)

        cur.execute("""
            CREATE TABLE scraped_inventory (
                id SERIAL PRIMARY KEY,
                store_id INTEGER REFERENCES stores(id) ON DELETE CASCADE,
                raw_name VARCHAR(255) NOT NULL,    
                price NUMERIC(5, 2) NOT NULL    
            );
        """)

        print("Schema built successfully")

        print("Seeding relational database")

        store_map = {} # store_name: store_id
        for store in raw_data["stores"]:
            name = store["name"]
            travel_time = store["travel_time"]

            cur.execute(
                "INSERT INTO stores (name, travel_time) VALUES (%s, %s) RETURNING id;",
                (name, travel_time)
            )
            store_id = cur.fetchone()[0]
            store_map[name] = store_id
            print(f"    Stored Store: '{name}' (Generated Database ID: {store_id})")

        scraped_records = []
        for item in raw_data["scraped_inventory"]:
            store_name = item["store"]
            raw_name = item["raw_name"]
            price = item["price"]

            store_id = store_map.get(store_name)
            if store_id is not None:
                scraped_records.append((store_id, raw_name, price))
            else:
                print(f"Warning: Store '{store_name}' not found for item '{raw_name}'. Skipping.")
        
        insert_query = "INSERT INTO scraped_inventory (store_id, raw_name, price) VALUES %s"
        execute_values(cur, insert_query, scraped_records)
        print(f"    Batch inserted {len(scraped_records)} raw inventory entries")

        conn.commit()
        print("Transaction committed successfully")
    except psycopg2.DatabaseError as error:
        print(f"Database Error: {error}")
        if conn:
            print(f"Rolling back active database connection")
            conn.rollback()
    except FileNotFoundError:
        print(f"Error: could not find 'inventory.json'")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("Connection closed safely")

if __name__ == "__main__":
    setup_and_seed_database()