import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import psycopg2
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Grocery Route Optimizer",
    layout="wide"
)

# For Portfolio Showcase Mode, use fallback data
FALLBACK_STORES = [
    {"id": 1, "name": "Target", "travel_time": 10},
    {"id": 2, "name": "Trader Joe's", "travel_time": 5},
    {"id": 3, "name": "Whole Foods", "travel_time": 11}
]

FALLBACK_INVENTORY = [
    {"store_id": "1", "raw_name": "2% Reduced Fat Milk", "price": 1.79},
    {"store_id": "1", "raw_name": "Grade A Large White Eggs - 12ct", "price": 1.59},
    {"store_id": "1", "raw_name": "Honey Wheat Sandwich Bread", "price": 1.99},
    {"store_id": "1", "raw_name": "Banana Conventional, 1 Each", "price": 0.39},
    {"store_id": "1", "raw_name": "Organic Tofu Extra Firm", "price": 3.59},
    {"store_id": "1", "raw_name": "Fresca Original Citrus Soda - 12pk/12 fl oz Cans", "price": 8.89},
    {"store_id": "1", "raw_name": "Barilla Rigatoni Pasta - 16oz", "price": 1.99},
    {"store_id": "1", "raw_name": "Fresh English Cucumber - Each", "price": 1.19},
    {"store_id": "1", "raw_name": "Take And Bake Baguette - 11.5oz - Favorite Day", "price": 2.99},
    {"store_id": "1", "raw_name": "Idaho Russet Potatoes - 5lbs - (Brand May Vary)", "price": 2.89},
    {"store_id": "1", "raw_name": "Grated Parmesan Cheese - 8oz - Market Pantry", "price": 3.79},
    {"store_id": "1", "raw_name": "Large Hass Avocado - each", "price": 1.29},
    {"store_id": "1", "raw_name": "Spice World Fresh Whole Garlic - 3ct Bag", "price": 1.99},
    {"store_id": "1", "raw_name": "Chobani Vanilla Blended Nonfat Greek Yogurt", "price": 6.49},
    {"store_id": "1", "raw_name": "Zbar Organic Chocolate Chip Granola Snack Bars", "price": 11.99},
    {"store_id": "1", "raw_name": "Fresh Beefsteak Tomatoes - 13oz/2ct - Good & Gather", "price": 2.99},
    {"store_id": "1", "raw_name": "organicgirl FreshBaby Arugula - 5oz", "price": 4.19},
    {"store_id": "1", "raw_name": "Fresh Organic Green Onion Bunch - 5.5oz", "price": 1.99},
    {"store_id": "1", "raw_name": "Fresh Yellow Onion - each", "price": 0.99},

    {"store_id": "2", "raw_name": "Trader Joe's Whole Milk Half Gal", "price": 5.99},
    {"store_id": "2", "raw_name": "Organic Brown Eggs 12-Pack", "price": 6.99},
    {"store_id": "2", "raw_name": "Organic Sliced Wheat Bread", "price": 4.49},
    {"store_id": "2", "raw_name": "Bananas Org Bag", "price": 0.29},
    {"store_id": "2", "raw_name": "Organic Tofu", "price": 2.49},
    {"store_id": "2", "raw_name": "Organic Free Range Boneless Skinless Chicken Breasts", "price": 7.49},
    {"store_id": "2", "raw_name": "Organic Italian Artisan Gigli Pasta", "price": 2.99},
    {"store_id": "2", "raw_name": "Organic Lemon", "price": 0.49},
    {"store_id": "2", "raw_name": "Organic English Cucumber", "price": 2.49},
    {"store_id": "2", "raw_name": "Organic French Baguette", "price": 1.99},
    {"store_id": "2", "raw_name": "Russet Potatoes", "price": 0.99},
    {"store_id": "2", "raw_name": "Grated Parmesan Cheese", "price": 2.99},
    {"store_id": "2", "raw_name": "Hass Avocado", "price": 1.79},
    {"store_id": "2", "raw_name": "Organic Garlic", "price": 1.00},
    {"store_id": "2", "raw_name": "Greek Lowfat Yogurt Plain", "price": 2.99},
    {"store_id": "2", "raw_name": "Campari Tomatoes", "price": 3.49},
    {"store_id": "2", "raw_name": "Wild Arugula", "price": 2.29},
    {"store_id": "2", "raw_name": "Green Onions (Scallion)", "price": 1.29},
    {"store_id": "2", "raw_name": "Jumbo Yellow Onions", "price": 1.19},

    {"store_id": "3", "raw_name": "365 Organic Whole Milk", "price": 2.79},
    {"store_id": "3", "raw_name": "Pasture-Raised Large Eggs", "price": 4.49},
    {"store_id": "3", "raw_name": "365 Organic Whole Wheat Bread, 20 OZ", "price": 3.69},
    {"store_id": "3", "raw_name": "Organic Banana Individual", "price": 0.69},
    {"store_id": "3", "raw_name": "Sprouted Tofu Extra Firm 14oz", "price": 2.99},
    {"store_id": "3", "raw_name": "365 by Whole Foods Market Boneless Skinless Chicken Breast", "price": 5.99},
    {"store_id": "3", "raw_name": "De Cecco Pasta Mezzi Rigatoni, 16 OZ", "price": 3.59},
    {"store_id": "3", "raw_name": "Lemon", "price": 0.89},
    {"store_id": "3", "raw_name": "English Cucumber", "price": 1.99},
    {"store_id": "3", "raw_name": "Baguette Sourdough, 8.82 Ounce", "price": 4.99},
    {"store_id": "3", "raw_name": "Organic Russet Potato", "price": 2.19},
    {"store_id": "3", "raw_name": "365 by Whole Foods Market Grated Parmesan, 5 OZ", "price": 3.99},
    {"store_id": "3", "raw_name": "Medium Hass Avocado", "price": 1.39},
    {"store_id": "3", "raw_name": "Organic Garlic", "price": 0.96},
    {"store_id": "3", "raw_name": "365 by Whole Foods Market, Greek Yogurt, Plain Nonfat, 32 Ounce", "price": 4.99},
    {"store_id": "3", "raw_name": "Organic Tomato On-The-Vine (price per lb)", "price": 3.69},
    {"store_id": "3", "raw_name": "365 by Whole Foods Market Organic Baby Arugula Salad, 5 OZ", "price": 3.89},
    {"store_id": "3", "raw_name": "Green Onion (Scallions) Organic, 1 Bunch", "price": 1.99},
    {"store_id": "3", "raw_name": "Onion Yellow Conventional, 1 Each (price per lb)", "price": 1.49}
]

CATALOG_ITEMS = ["milk", "eggs", "bread", "bananas", "tofu", "fresca", "pasta", "cucumber", "baguette", "potatoes",
                 "parmesan", "avocado", "garlic", "yogurt", "zbars", "tomatoes", "arugula", "green onions", "onions", 
                 "chicken", "lemon"]

@st.cache_data(ttl=300)
def load_grocery_data():
    """
    Attempts to pull live database records from PostgreSQL.
    Falls back to the in-memory dataset on connection failure.
    """
    db_config = {
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT")
    }

    if not all(db_config.values()):
        return False, pd.DataFrame(FALLBACK_STORES), pd.DataFrame(FALLBACK_INVENTORY)
    
    try:
        conn = psycopg2.connect(**db_config)

        stores_df = pd.read_sql_query("SELECT id, name, travel_time FROM stores;", conn)
        inventory_df = pd.read_sql_query("SELECT store_id, raw_name, price FROM scraped_inventory", conn)

        inventory_df["price"] = inventory_df["price"].astype(float)

        conn.close()
        return True, stores_df, inventory_df
    
    except Exception as e:
        return False, pd.DataFrame(FALLBACK_STORES), pd.DataFrame(FALLBACK_INVENTORY)
    
is_live, stores_df, inventory_df = load_grocery_data()

st.sidebar.title("Optimization Control")

if is_live:
    st.sidebar.success("Connected to live PostgreSQL Database")
else:
    st.sidebar.warning("Database offline. Running Showcase Fallback")

lambda_val = st.sidebar.slider(
    "Friction Penalty (λ)",
    min_value=0.0,
    max_value=2.0,
    value=0.5,
    step=0.1,
    help="Higher lambda penalizes travel. Slide to 0.0 for lowest prices; Slide to 1.5+ to minimize store visits."
)

st.sidebar.markdown("""
---
### Operations Research Metric
The objective function minimizes:
$$\\text{Bill Cost} + (\\lambda + \\epsilon) \\cdot \\text{Travel Time}$$
""")

st.title("Smart Grocery Route Optimizer")
st.markdown("""
This prescriptive analytics application uses a **Mixed-Integer Linear Programming (MILP)** algorithm to calculate the cheapest, most convenient route to get your groceries.
""")

tab_optimizer, tab_frontier, tab_insights = st.tabs([
    "Shopping Optimizer", 
    "The Efficient Frontier", 
    "Market Price Analytics"
])

with tab_optimizer:
    st.subheader("Custom Route Planner")

    col_input, col_metrics = st.columns([3, 1])
    
    with col_input:
        selected_shopping_list = st.multiselect(
            "Build Your Shopping List:",
            options=CATALOG_ITEMS,
            default=["milk", "eggs"] if not is_live else CATALOG_ITEMS[:3]
        )
        
    with col_metrics:
        run_opt = st.button("Solve Routing Matrix", use_container_width=True)

# Inside Tab 2: Placeholder
with tab_frontier:
    st.subheader("Trade-off Curve Analysis: Out-of-Pocket vs Travel Friction")
    st.info("Efficient Frontier Plotly visualization placeholder.")

# Inside Tab 3: Placeholder
with tab_insights:
    st.subheader("Market Basket Index & Brand Analytics")
    st.info("Descriptive SQL/Pandas analytics charts placeholder.")