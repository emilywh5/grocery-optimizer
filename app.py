import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import psycopg2
import pulp
from dotenv import load_dotenv
from entity_matcher import resolve_product

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

CATALOG_ITEMS = ["milk", "eggs", "bread", "bananas", "tofu", "pasta", "cucumber", "baguette", "potatoes",
                 "parmesan", "avocado", "garlic", "yogurt", "zbars", "tomatoes", "arugula", "green onions", "onions", 
                 "chicken", "lemon"]

DEPARTMENT_MAPPING = {
    "bananas": "Produce",
    "spinach": "Produce",
    "avocado": "Produce",
    "cucumber": "Produce",
    "potatoes": "Produce",
    "garlic": "Produce",
    "tomatoes": "Produce",
    "arugula": "Produce",
    "green onions": "Produce",
    "onions": "Produce",
    "lemon": "Produce",
    "milk": "Dairy & Alternatives",
    "eggs": "Dairy & Alternatives",
    "parmesan": "Dairy & Alternatives",
    "yogurt": "Dairy & Alternatives",
    "tofu": "Proteins",
    "chicken": "Proteins",
    "bread": "Bakery & Staples",
    "pasta": "Bakery & Staples",
    "baguette": "Bakery & Staples",
    "zbars": "Bakery & Staples"
}

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
    
is_live, raw_stores_df, inventory_df = load_grocery_data()

stores_df = raw_stores_df.copy()

def run_optimization(selected_items, lambda_weight, stores, inventory):
    """
    Resolves products using fuzzy matching and solved the MILP routing problem.
    """
    store_names = stores["name"].tolist()
    store_id_to_name = stores.set_index("id")["name"].to_dict()
    travel_times = stores.set_index("name")["travel_time"].to_dict()

    prices = {}
    resolved_catalog_items = set()
    unresolved_items = set(selected_items)

    for _, row in inventory.iterrows():
        store_name = store_id_to_name.get(row["store_id"])
        raw_name = row["raw_name"]
        price = float(row["price"])

        matched_item = resolve_product(raw_name, selected_items, threshold=75.0)
        if matched_item:
            prices[(matched_item, store_name)] = price
            resolved_catalog_items.add(matched_item)
            unresolved_items.discard(matched_item)
    
    items_to_solve = sorted(list(resolved_catalog_items))

    if not items_to_solve:
        return {
            "status": "no_matches_found",
            "total_grocery_cost": 0.0,
            "total_travel_time": 0,
            "itinerary": {},
            "unresolved_items": list(unresolved_items)
        }
    
    prob = pulp.LpProblem("Grocery_Routing_Optimization", pulp.LpMinimize)

    # Decision Variables: x[i, s] is 1 if I buy item 'i' at store 's', 0 otherwise
    x = pulp.LpVariable.dicts("buy", ((i, s) for i in items_to_solve for s in store_names if (i, s) in prices), cat='Binary')

    # Activation Variables: y[s] is 1 if I visit store 's', 0 otherwise
    y = pulp.LpVariable.dicts("visit", store_names, cat='Binary')

    for i in items_to_solve:
        available_stores = [s for s in store_names if (i, s) in prices]
        if not available_stores:
            continue
        prob += pulp.lpSum(x[i, s] for s in available_stores) == 1, f"Fulfill_{i}"

    for s in store_names:
        for i in items_to_solve:
            if (i, s) in prices:
                prob += x[i, s] <= y[s], f"Activate_{i}_{s}"

    epsilon = 1e-5
    adjusted_travel_penalty = (lambda_weight + epsilon)

    prob += (
        pulp.lpSum(prices[i, s] * x[i, s] for i in items_to_solve for s in store_names if (i, s) in prices) +
        adjusted_travel_penalty * pulp.lpSum(travel_times[s] * y[s] for s in store_names)
    )

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    # Structure results
    itinerary={}
    total_grocery_cost = 0.0
    total_travel_time = 0

    for s in store_names:
        if y[s].varValue and y[s].varValue > 0.5:
            store_purchases = []
            for i in items_to_solve:
                if (i, s) in prices and x[i, s].varValue and x[i, s].varValue > 0.5:
                    item_price = prices[(i, s)]
                    store_purchases.append({"item": i, "price": item_price})
                    total_grocery_cost += item_price
            
            if store_purchases:
                itinerary[s] = {
                    "travel_time": travel_times[s],
                    "items": store_purchases
                }
                total_travel_time += travel_times[s]
    return {
        "status": "success",
        "total_grocery_cost": round(total_grocery_cost, 2),
        "total_travel_time": int(total_travel_time),
        "itinerary": itinerary,
        "unresolved_items": list(unresolved_items)
    }

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

st.sidebar.markdown("---")
st.sidebar.markdown("### Travel Times to Stores (Minutes)")
st.sidebar.caption("Adjust the driving times from your home to customize the route calculations:")

custom_travel_times = {}
for idx, row in stores_df.iterrows():
    store_name = row["name"]
    default_time = int(row["travel_time"])

    custom_travel_times[store_name] = st.sidebar.slider(
        f"{store_name}",
        min_value=1,
        max_value=60,
        value=default_time,
        step=1,
        key=f"travel_{store_name}"
    )

stores_df["travel_time"] = stores_df["name"].map(custom_travel_times)

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

    selected_shopping_list = st.multiselect(
        "Build Your Shopping List:",
        options=CATALOG_ITEMS,
        default=["milk", "eggs"] if not is_live else CATALOG_ITEMS[:3]
    )
        
    if selected_shopping_list:
        results = run_optimization(selected_shopping_list, lambda_val, stores_df, inventory_df)

        if results["status"] == "success":
            st.markdown("---")

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Optimized Cart Cost", f"${results['total_grocery_cost']:.2f}")
            metric_col2.metric("Total Travel Time", f"{results['total_travel_time']} mins")
            metric_col3.metric("Retail Visits Needed", f"{len(results['itinerary'])}")

            st.markdown("### Personalized Shopping Itinerary")
            for store_name, details in results["itinerary"].items():
                with st.expander(f"**Visit {store_name}** — Buy {len(details['items'])} items ({details['travel_time']} mins travel time)", expanded=True):
                    # Represent as a neat DataFrame table
                    store_items_df = pd.DataFrame(details["items"])
                    store_items_df.columns = ["Resolved Product", "Shelf Price"]
                    store_items_df["Shelf Price"] = store_items_df["Shelf Price"].map("${:,.2f}".format)
                    st.table(store_items_df)

            if results["unresolved_items"]:
                st.warning(f"**Could not resolve inventory for:** {', '.join(results['unresolved_items'])}")
        
        else:
            st.error("None of your shopping list items could be matched to the current database catalog.")
    else:
        st.info("Add items to your shopping list to compute your optimized route.")

# Inside Tab 2: Placeholder
with tab_frontier:
    st.subheader("Trade-off Curve Analysis: Out-of-Pocket vs Travel Friction")
    st.markdown("""
    This visualization runs **21 distinct mathematical optimizations** on your shopping list across various $\\lambda$ settings.
    It uncovers the **Pareto-Efficient Frontier**: the boundary where you cannot lower your grocery bill without increasing travel time and store visits.         
    """)

    if selected_shopping_list:
        frontier_data = []
        lambda_sweep = np.linspace(0.0, 2.0, 21)

        for l_val in lambda_sweep:
            sweep_results = run_optimization(selected_shopping_list, l_val, stores_df, inventory_df)
            if sweep_results["status"] == "success":
                frontier_data.append({
                    "Lambda (λ)": round(l_val, 2),
                    "Grocery Cost ($)": sweep_results["total_grocery_cost"],
                    "Travel Time (mins)": sweep_results["total_travel_time"],
                    "Visits": len(sweep_results["itinerary"])
                })

        frontier_df = pd.DataFrame(frontier_data).drop_duplicates(subset=["Grocery Cost ($)", "Travel Time (mins)"])

        fig_frontier = px.line(
            frontier_df,
            x="Travel Time (mins)",
            y="Grocery Cost ($)",
            text="Lambda (λ)",
            markers=True,
            title="The Pareto-Efficient Frontier Curve",
            labels={
                "Travel Time (mins)": "Total Travel Time (Convenience Penalty)",
                "Grocery Cost ($)": "Grocery Bill Cost (Out-of-Pocket)"
            },
            template="plotly_dark"
        )

        fig_frontier.update_traces(
            textposition="top right",
            marker=dict(size=10, color="#10B981", line=dict(width=2, color="white")),
            line=dict(width=3, color="#059669")
        )
        
        fig_frontier.update_layout(
            hovermode="closest",
            xaxis=dict(tickmode="linear", dtick=5),
            yaxis=dict(tickprefix="$")
        )
        
        st.plotly_chart(fig_frontier, use_container_width=True)

        st.markdown("### Available Strategic Decisions")
        display_frontier_df = frontier_df.copy()
        display_frontier_df.columns = ["Lambda Value (λ)", "Total Bill Cost", "Travel Time (Mins)", "Store Stops Needed"]
        st.dataframe(display_frontier_df.style.format({
            "Lambda Value (λ)": "{:.2f}",
            "Total Bill Cost": "${:,.2f}"
        }), use_container_width=True)
    else:
        st.info("Build a shopping list in the optimizer tab to analyze your efficient frontier")

# Inside Tab 3: Placeholder
with tab_insights:
    st.subheader("Market Basket Index & Competitive Pricing Insights")
    st.markdown("""
    This tab displays descriptive pricing distributions mapped across the stores in your PostgreSQL database to benchmark retail performance.         
    """)

    store_map_dict = stores_df.set_index("id")["name"].to_dict()
    resolved_records = []
    
    for _, row in inventory_df.iterrows():
        store_id = row["store_id"]
        raw_name = row["raw_name"]
        price = float(row["price"])
        store_name = store_map_dict.get(store_id)
        
        matched_cat = resolve_product(raw_name, CATALOG_ITEMS, threshold=75.0)
        
        if matched_cat:
            macro_cat = DEPARTMENT_MAPPING.get(matched_cat, "Other Staples")

            resolved_records.append({
                "Store": store_name,
                "Product": matched_cat.capitalize(),
                "Department": macro_cat,
                "Price": price,
                "Is_Organic": "organic" in raw_name.lower() or "org " in raw_name.lower() or "org" in raw_name.lower()
            })
            
    analytics_df = pd.DataFrame(resolved_records)
    
    if not analytics_df.empty:
        col_chart_left, col_chart_right = st.columns(2)
        
        with col_chart_left:
            st.markdown("#### Total Benchmark Market Basket Cost")
            st.caption("The total cost to purchase all catalog items at a single store (lower is cheaper).")
            
            total_basket = analytics_df.groupby("Store")["Price"].sum().reset_index()
            total_basket.columns = ["Store", "Basket Total ($)"]
            
            fig_basket = px.bar(
                total_basket,
                x="Store",
                y="Basket Total ($)",
                color="Store",
                text="Basket Total ($)",
                color_discrete_map={
                    "Target": "#EF4444", 
                    "Trader Joe's": "#F59E0B", 
                    "Whole Foods": "#10B981"
                },
                color_discrete_sequence=px.colors.qualitative.Safe,
                template="plotly_dark"
            )
            fig_basket.update_traces(texttemplate='$%{y:.2f}', textposition='outside')
            fig_basket.update_layout(yaxis=dict(tickprefix="$"))
            st.plotly_chart(fig_basket, use_container_width=True)
            
        with col_chart_right:
            st.markdown("#### Department-Level Average Cost Comparison")
            st.caption("Compare the average item price within each retail department across stores.")
            
            category_comparison = analytics_df.groupby(["Store", "Department"])["Price"].mean().reset_index()
            
            fig_category = px.bar(
                category_comparison,
                x="Department",
                y="Price",
                color="Store",
                barmode="group",
                color_discrete_map={
                    "Target": "#EF4444", 
                    "Trader Joe's": "#F59E0B", 
                    "Whole Foods": "#10B981"
                },
                color_discrete_sequence=px.colors.qualitative.Safe,
                labels={"Price": "Average Item Price ($)"},
                template="plotly_dark"
            )
            fig_category.update_layout(
                yaxis=dict(tickprefix="$"),
                xaxis_title="Grocery Department"
            )
            st.plotly_chart(fig_category, use_container_width=True)
            
        st.markdown("### Active Database Catalog Records")
        display_df = analytics_df.copy()
        display_df["Is_Organic"] = display_df["Is_Organic"].map({True: "Yes", False: "No"})
        display_df.columns = ["Retail Store", "Product", "Department", "Shelf Price ($)", "Is Organic"]
        
        st.dataframe(display_df.style.format({
            "Shelf Price ($)": "${:,.2f}"
        }), use_container_width=True)
        
    else:
        st.error("No product mapping logs could be loaded. Please check your PostgreSQL database configuration.")