import json
import pulp
from entity_matcher import resolve_product

# setup master catalog
MASTER_PRODUCTS = ["milk", "eggs", "bread", "bananas", "tofu"]
CONFIDENCE_THRESHOLD = 75.0

# data ingestion & fuzzy resolution
with open('inventory.json', 'r') as f:
    data = json.load(f)


stores = [store['name'] for store in data['stores']]
travel_times = {store['name']: store['travel_time'] for store in data['stores']}

prices = {}
resolved_items = set()

print("Ingesting & Resolving Scraped Inventory")
print("-" * 50)

for item in data['scraped_inventory']:
    store_name = item['store']
    raw_name = item['raw_name']
    price = item['price']

    clean_product_key = resolve_product(raw_name, MASTER_PRODUCTS, CONFIDENCE_THRESHOLD)

    if clean_product_key:
        prices[(clean_product_key, store_name)] = price
        resolved_items.add(clean_product_key)
        print(f"Mapped: '{raw_name}'\n        -> [{clean_product_key.upper()}] at {store_name} for ${price}")
    else:
        print(f"Skipped (Unmapped): '{raw_name}' at {store_name}")
    print("-" * 50)

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