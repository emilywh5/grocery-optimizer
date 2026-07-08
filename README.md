# Algorithmic Grocery Optimization Engine

An end-to-end, prescriptive decisions platform that solves the multi-objective trade-off between household grocery budgets and travel times.

Live App: https://grocery-optimizer.streamlit.app/

## Project Milestones
- [x] Phase 1: Local environment & Git architecture setup
- [x] Phase 2: Core optimization proof of concept (`PuLP`)
- [x] Phase 3: Text processing & Entity Resolution pipeline (`RapidFuzz`)
- [x] Phase 4: Normalized PostgreSQL database migrations (`psycopg2`)
- [x] Phase 5: Interactive BI Dashboarding (`Streamlit` & `Plotly`)

---

## Proof of Concept & Validation

The optimization engine maps a multi-objective trade-off using a parameterized tuning variable, $\lambda$ (Lambda), which acts as the user's financial valuation of their time. 

The engine was tested using a baseline 5-item grocery list across 3 competitive local storefronts (Target, Trader Joe's, and Whole Foods) with non-uniform price indices.

### Scenario 1: Pure Cost Optimization ($\lambda = 0.0$)
*In this mode, travel time friction is completely ignored. The algorithm acts as a pure bargain-hunter, splitting the shopping list across multiple locations to minimize out-of-pocket expenses.*

```text
Chosen Strategy (Lambda = 0.0):
----------------------------------------
Visit Target (Travel Time: 10 mins):
   - Buy milk ($1.79)
   - Buy eggs ($1.59)
   - Buy bread ($1.99)
Visit Trader Joe's (Travel Time: 5 mins):
   - Buy bananas ($0.29)
   - Buy tofu ($2.49)
----------------------------------------
Total Out-of-Pocket Grocery Bill: $8.15
Total Travel Time: 15.0 minutes
```

### Scenario 2: Pure Convenience Optimization ($\lambda = 5.0$)
*In this mode, travel friction carries a heavy mathematical penalty. The algorithm willingly absorbs higher individual unit prices to minimize the overall time spent traveling, consolidating all items into the single most efficient route.*

```text
Chosen Strategy (Lambda = 5.0):
----------------------------------------
Visit Trader Joe's (Travel Time: 5 mins):
   - Buy milk ($5.99)
   - Buy eggs ($6.99)
   - Buy bread ($4.49)
   - Buy bananas ($0.29)
   - Buy tofu ($2.49)
----------------------------------------
Total Out-of-Pocket Grocery Bill: $20.25
Total Travel Time: 5.0 minutes
```

## Mathematical Optimization Model

The engine formulates the routing challenge as a **Multi‑Objective Mixed‑Integer Linear Program (MILP)**. The solver minimizes total dollar expenditure plus a weighted convenience penalty.

### 1. Sets & Indexes
- **I** — Master product categories  
- **S** — Physical retail stores  

### 2. Decision Variables
- **xᵢₛ ∈ {0,1}** — Item *i* purchased at store *s*  
- **yₛ ∈ {0,1}** — Store *s* is visited  

### 3. Parameters
- **cᵢₛ** — Price of item *i* at store *s*  
- **tₛ** — Travel time to store *s*  
- **λ** — Cost–convenience trade‑off weight  
- **ε = 10⁻⁵** — Tie‑breaking micro‑penalty  

### 4. Objective Function


<div align="left">

$$
\text{Minimize } 
\sum_{i \in I} \sum_{s \in S} c_{is} x_{is}
+ (\lambda + \epsilon)\sum_{s \in S} t_s y_s
$$

**Fulfillment Constraint**

$$
\sum_{s \in S} x_{is} = 1 \quad \forall i \in I
$$

**Store Activation Constraint**  

$$
x_{is} \le y_s 
\quad \forall i \in I,\; s \in S
$$

</div>

## Unstructured Natural Language Processing (NLP)
Product listings are dirty and unstandardized:

- Whole Foods: 365 Organic Whole Wheat Bread, 20 OZ

- Target: Market Pantry Sliced White Bread Loaf

The matching module (entity_matcher.py) executes a modular, multi-stage pipeline:

### 1. Normalizes Text
Strips special characters, forces lowercase, and resolves singular/plural mismatch anomalies (e.g., bananas $\rightarrow$ banana).

### 2. Performs Fuzzy Matching
Leverages RapidFuzz's Levenshtein distance partial-ratio scoring to compare unstandardized strings against target catalog categories.

### 3. Acceptance Thresholding
Enforces a rigid confidence threshold (minimum $75\%$) to map matches safely while routing unmapped rows (like chips or sodas) to a manual review log.

## Interactive Analytics & BI Dashboard
The final layer is an interactive Streamlit and Plotly dashboard. When deployed, it offers non-technical users real-time scenario simulation:

### 1. Reactive Solver Controls
Instantly recalculates itineraries when you adjust dynamic driving sliders or the travel friction slider ($\lambda$).

### 2. The Pareto-Efficient Frontier Curve
Runs 21 consecutive optimizations under the hood on your current list. It plots the strict mathematical trade-off curve, showing where you cannot save another dollar without taking on extra travel times.

### 3. Department-Level Cost Comparison
Aggregates individual price metrics into broader business units (i.e., Produce, Proteins, Dairy) to compare store performance visually.

## Step-by-Step Installation & Local Setup
### 1. Prerequisites & Environment

Ensure you have Python 3.11+, PostgreSQL 15+, and WSL-Ubuntu installed. Clone the repository and establish a clean virtual environment:

```text
git clone https://github.com/yourusername/grocery-optimizer.git
cd grocery-optimizer
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```text
pip install -r requirements.txt
```

### 3. Database Credentials Setup

Create a .env file in the root directory to store your PostgreSQL connection details securely:

```text
DB_NAME=grocery_db
DB_USER=grocery_admin
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Build and Seed the Relational Schema

Run the custom seeder to structure PostgreSQL, create relations, and populate the tables with 32 real-world products and prices:

```text
python generate_expanded_data.py
```

### 5. Launch the Streamlit App

Launch the interactive web server locally:

```text
streamlit run app.py
```