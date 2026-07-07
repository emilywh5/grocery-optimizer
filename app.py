import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Grocery Route Optimizer",
    layout="wide"
)

st.sidebar.title("Optimization Control")

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
        st.info("Shopping list selection will go here.")
        
    with col_metrics:
        run_opt = st.button("⚡ Solve Routing Matrix", use_container_width=True)

# Inside Tab 2: Placeholder
with tab_frontier:
    st.subheader("📈 Trade-off Curve Analysis: Out-of-Pocket vs Travel Friction")
    st.info("Efficient Frontier Plotly visualization placeholder.")

# Inside Tab 3: Placeholder
with tab_insights:
    st.subheader("📊 Market Basket Index & Brand Analytics")
    st.info("Descriptive SQL/Pandas analytics charts placeholder.")