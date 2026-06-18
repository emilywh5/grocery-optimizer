import os
from typing import List, Dict, Any
import psycopg2
import pulp
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from entity_matcher import resolve_product

load_dotenv()

app = FastAPI(
    title="Grocery Shopping Optimizer API",
    description="A high-performance REST API that resolves messy scraped grocery data and calculates the optimal grocery shopping route",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

class OptimizationRequest(BaseModel):
    shopping_list: List[str] = Field(
        ..., 
        description="A list of grocery items you want to buy (e.g., ['Milk', 'Wheat Bread', 'Eggs'])",
        example=["Milk", "Wheat Bread", "Eggs"]
    )
    lambda_val: float = Field(
        0.5, 
        ge=0.0, 
        le=5.0, 
        description="Weight factor balancing travel time vs. saving money. 0.0 prioritizing pure cost, 5.0 prioritizing minimum stores visited.",
        example=0.5
    )

class OptimizedItem(BaseModel):
    item_name: str
    price: float

class StoreVisit(BaseModel):
    store_name: str
    travel_time: int
    items_to_buy: List[OptimizedItem]

class OptimizationResponse(BaseModel):
    status: str
    lambda_val: float
    total_grocery_cost: float
    total_travel_time: int
    itinerary: List[StoreVisit]
    unresolved_items: List[str]

@app.post(
    "/optimize", 
    response_model=OptimizationResponse, 
    status_code=status.HTTP_200_OK,
    summary="Calculate optimal shopping strategy",
    description="Accepts a raw shopping list, queries PostgreSQL, resolves chaotic products, and computes the optimal routing strategy based on cost and convenience."
)
async def optimize_grocery_run(payload: OptimizationRequest):
    # Validate payload
    if not payload.shopping_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Shopping list cannot be empty."
        )

    # Database and Ingestion Variables
    stores = []
    travel_times = {}
    prices = {}
    resolved_user_items = set()
    unresolved_items = set(payload.shopping_list)
    
    conn = None
    cur = None
    # --- 1: Query database for Stores & Scraped Inventory ---
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get active stores
        cur.execute("SELECT name, travel_time FROM stores;")
        for row in cur.fetchall():
            store_name, travel_time = row
            stores.append(store_name)
            travel_times[store_name] = travel_time
            
        # Get scraped inventory linked with store name
        cur.execute("""
            SELECT s.name, si.raw_name, si.price 
            FROM scraped_inventory si
            JOIN stores s ON si.store_id = s.id;
        """)
        scraped_rows = cur.fetchall()
        
    except psycopg2.DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection or query failed: {str(e)}"
        )
    finally:
        if cur: cur.close()
        if conn: conn.close()
    
    # --- 2: Fuzzy match scraped rows against User's requested list ---
    # Threshold of 75% for substring matches
    CONFIDENCE_THRESHOLD = 75.0
    
    for row in scraped_rows:
        store_name, raw_name, price = row
        price = float(price)
        
        # Match raw scraped string to the user's requested list dynamically
        matched_user_term = resolve_product(raw_name, payload.shopping_list, CONFIDENCE_THRESHOLD)
        
        if matched_user_term:
            prices[(matched_user_term, store_name)] = price
            resolved_user_items.add(matched_user_term)
            
            # Remove from unresolved items if successfully matched
            unresolved_items.discard(matched_user_term)

    # Convert resolved items back to a sorted list for the optimization matrices
    items_to_optimize = sorted(list(resolved_user_items))
    
    # If no matches found on the user's shopping list, exit early
    if not items_to_optimize:
        return OptimizationResponse(
            status="no_matches_found",
            lambda_val=payload.lambda_val,
            total_grocery_cost=0.0,
            total_travel_time=0,
            itinerary=[],
            unresolved_items=list(unresolved_items)
        )
    # --- 3: Formulate and Solve the MILP Optimization Problem ---
    prob = pulp.LpProblem("Grocery_Optimization", pulp.LpMinimize)
    
    # x[i, s] is 1 if item 'i' is bought at store 's', 0 otherwise (only create if price exists for that pair)
    x = pulp.LpVariable.dicts("buy", ((i, s) for i in items_to_optimize for s in stores if (i, s) in prices), cat='Binary')
    # y[s] is 1 if store 's' is visited, 0 otherwise
    y = pulp.LpVariable.dicts("visit", stores, cat='Binary')
    
    # Constraint A: Every matched user item must be bought at exactly one store
    for i in items_to_optimize:
        available_stores = [s for s in stores if (i, s) in prices]
        if not available_stores:
            continue # Skip items that are matching but lack prices
        prob += pulp.lpSum(x[i, s] for s in available_stores) == 1, f"Fulfill_{i}"
        
    # Constraint B: Items can only be purchased from a visited store
    for s in stores:
        for i in items_to_optimize:
            if (i, s) in prices:
                prob += x[i, s] <= y[s], f"Activate_{i}_{s}"
                
    # Define Lambda objective metrics
    epsilon = 1e-5
    adjusted_travel_penalty = (payload.lambda_val + epsilon)
    
    # Objective function: Minimize total item costs + lambda travel time costs
    prob += (
        pulp.lpSum(prices[i, s] * x[i, s] for i in items_to_optimize for s in stores if (i, s) in prices) + 
        adjusted_travel_penalty * pulp.lpSum(travel_times[s] * y[s] for s in stores)
    )
    
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    # --- 4: Structure Response Payload ---
    itinerary_list = []
    
    for s in stores:
        # Check if store was chosen (account for solver precision with > 0.5)
        if y[s].varValue and y[s].varValue > 0.5:
            items_bought_here = []
            for i in items_to_optimize:
                if (i, s) in prices and x[i, s].varValue and x[i, s].varValue > 0.5:
                    items_bought_here.append(OptimizedItem(item_name=i, price=prices[i, s]))
            
            # Only add to itinerary if the solver actually bought items there
            if items_bought_here:
                itinerary_list.append(StoreVisit(
                    store_name=s,
                    travel_time=travel_times[s],
                    items_to_buy=items_bought_here
                ))
                
    # Calculate totals
    total_grocery_cost = sum(
        prices[i, s] * x[i, s].varValue 
        for i in items_to_optimize for s in stores 
        if (i, s) in prices and x[i, s].varValue and x[i, s].varValue > 0.5
    )
    total_travel_time = sum(
        travel_times[s] * y[s].varValue 
        for s in stores 
        if y[s].varValue and y[s].varValue > 0.5
    )
    
    return OptimizationResponse(
        status="success",
        lambda_val=payload.lambda_val,
        total_grocery_cost=round(total_grocery_cost, 2),
        total_travel_time=int(total_travel_time),
        itinerary=itinerary_list,
        unresolved_items=list(unresolved_items)
    )

# Root endpoint for structural verification
@app.get("/")
async def root():
    return {"message": "Grocery Shopping Optimizer REST API is live. Navigate to /docs for interactive Swagger UI."}