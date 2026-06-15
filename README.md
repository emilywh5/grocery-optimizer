# Algorithmic Grocery Optimization Engine

A prescriptive decision tool built to optimize low grocery costs and travel convenience using Mixed-Integer Linear Programming (MILP).

## Current Project Stage
- [x] Phase 1: Local environment & Git architecture setup
- [ ] Phase 2: Core optimization proof of concept (`PuLP`)
- [ ] Phase 3: Text processing & Entity Resolution pipeline
- [ ] Phase 4: PostgreSQL inventory engine
- [ ] Phase 5: Spatial mapping dashboard

## Proof of Concept
Given a 5 item grocery list with prices from 3 stores, when purely prioritizing cost the optimal path is:
Chosen Strategy (Lambda = 0.0):
----------------------------------------
Visit Target (Travel Time: 10 mins):
   - Buy milk ($1.79)
   - Buy eggs ($1.59)
   - Buy bread ($1.99)
Visit Trader Joe's (Travel Time: 5 mins):
   - Buy bananas ($0.29)
   - Buy tofu ($2.49)
Visit Whole Foods (Travel Time: 11 mins):
----------------------------------------
Total Out-of-Pocket Grocery Bill: $8.15
Total Travel Time: 26.0 minutes

When purely prioritizing convenience the optimal path is:
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