# Algorithmic Grocery Optimization Engine

A prescriptive decision tool built to optimize low grocery costs and travel convenience using Mixed-Integer Linear Programming (MILP).

## Current Project Stage
- [x] Phase 1: Local environment & Git architecture setup
- [x] Phase 2: Core optimization proof of concept (`PuLP`)
- [ ] Phase 3: Text processing & Entity Resolution pipeline
- [ ] Phase 4: PostgreSQL inventory engine
- [ ] Phase 5: Spatial mapping dashboard

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