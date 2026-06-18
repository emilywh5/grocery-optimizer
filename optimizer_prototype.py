import os
import psycopg2
import pulp
from entity_matcher import resolve_product
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# setup master catalog
MASTER_PRODUCTS = ["milk", "eggs", "bread", "bananas", "tofu"]
CONFIDENCE_THRESHOLD = 75.0

stores = []
travel_times = {}
prices = {}
resolved_items = set()

conn = None
cur = None

try:
    print("Connecting to PostgreSQL database")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("Querying store profiles")
    cur.execute("SELECT name, travel_time FROM stores;")
    store_rows = cur.fetchall()
    for row in store_rows:
        store_name, travel_time = row
        stores.append(store_name)
        travel_times[store_name] = travel_time

    print("Querying scraped inventory records")
    cur.execute("""
        SELECT s.name, si.raw_name, si.price
        FROM scraped_inventory si
        JOIN stores s ON si.store_id = s.id;        
    """)
    inventory_rows = cur.fetchall()

    print("\nProcessing & Matching Ingested Data:")
    print("-" * 60)
    for row in inventory_rows:
        store_name, raw_name, price = row
        price = float(price)

        clean_product_key = resolve_product(raw_name, MASTER_PRODUCTS, CONFIDENCE_THRESHOLD)

        if clean_product_key:
            prices[(clean_product_key, store_name)] = price
            resolved_items.add(clean_product_key)
            print(f"Mapped: '{raw_name}'\n        -> [{clean_product_key.upper()}] at {store_name} for ${price}")
        else:
            print(f"Skipped (Unmapped): '{raw_name}' at {store_name}")
        print("-" * 60)
except psycopg2.DatabaseError as error:
    print(f"Database connection error: {error}")
    raise SystemExit
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
        print("Database connection closed safely")

items = sorted(list(resolved_items))

prob = pulp.LpProblem("Grocery_Optimization", pulp.LpMinimize)

# Decision Variables: x[i, s] is 1 if I buy item 'i' at store 's', 0 otherwise
x = pulp.LpVariable.dicts("buy", ((i, s) for i in items for s in stores), cat='Binary')

# Activation Variables: y[s] is 1 if I visit store 's', 0 otherwise
y = pulp.LpVariable.dicts("visit", stores, cat='Binary')

# verify for constraints 
for i in items:
    # The sum of buying item 'i' across all possible stores must equal 1
    prob += pulp.lpSum(x[i, s] for s in stores) == 1, f"Fulfill_{i}"

for s in stores:
    for i in items:
        # If x[i, s] becomes 1, then y[s] must be forced to 1 to satisfy this inequality
        prob += x[i, s] <= y[s], f"Activate_{i}_{s}"

# lambda = time vs money preference (lower lamba = money is more important)
# 0.0 < lambda_val < 5.0
lambda_val = 2.5

# add a tiny epsilon value (1e-5) to the travel time penalty
# when lambda = 0, the solver is forced to set unused store variables (y) to 0 to reduces the score
epsilon = 1e-5
adjusted_travel_penalty = (lambda_val + epsilon)

prob += (
    pulp.lpSum(prices[i, s] * x[i, s] for i in items for s in stores) + 
    adjusted_travel_penalty * pulp.lpSum(travel_times[s] * y[s] for s in stores)
)

status = prob.solve(pulp.PULP_CBC_CMD(msg=False))

print(f"Optimization Status: {pulp.LpStatus[status]}")
print(f"Chosen Strategy (Lambda = {lambda_val}):\n" + "-"*40)

for s in stores:
    if y[s].varValue == 1:
        print(f"Visit {s} (Travel Time: {travel_times[s]} mins):")
        for i in items:
            if x[i, s].varValue == 1:
                print(f"   - Buy {i} (${prices[i, s]})")

# Calculate metrics manually to see real breakdown
total_grocery_cost = sum(prices[i, s] * x[i, s].varValue for i in items for s in stores)
total_travel_time = sum(travel_times[s] * y[s].varValue for s in stores)

print("-"*40)
print(f"Total Out-of-Pocket Grocery Bill: ${total_grocery_cost:.2f}")
print(f"Total Travel Time: {total_travel_time} minutes")