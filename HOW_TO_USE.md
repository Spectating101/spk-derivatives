# How to Actually Use This Library

**Quick answer to: "How do we plug in the data and use it?"**

---

## The 30-Second Answer

```python
# Install
pip install git+https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git@v0.2.0-research

# Use (3 lines)
from solar_quant import load_solar_parameters, BinomialTree

params = load_solar_parameters()  # NASA data → auto-fetched → processed
price = BinomialTree(**params, N=100, payoff_type='call').price()

print(f"Solar call option: ${price:.6f}")  # Output: $0.035645
```

**That's it.** Data input is automatic via NASA API.

---

## Data Flow: Where Does Data Come From?

### The Full Pipeline

```
1. YOU CALL:
   load_solar_parameters(lat=24.99, lon=121.30)

2. LIBRARY DOES:
   ├─ Checks cache: energy_derivatives/data/nasa_cache/
   ├─ If not cached:
   │  ├─ Calls NASA POWER API
   │  ├─ Downloads: ALLSKY_SFC_SW_DWN (solar irradiance)
   │  ├─ Date range: 2020-2024
   │  └─ Saves to cache
   ├─ Loads DataFrame with daily GHI (kWh/m²/day)
   ├─ Removes seasonality (30-day rolling mean)
   ├─ Calculates log returns
   ├─ Computes volatility (annualized)
   └─ Returns: {S0, K, T, r, sigma, ...}

3. YOU GET:
   Dictionary ready for pricing
```

### No Manual Data Required

- **NASA API** = free, global, satellite-based
- **Automatic caching** = fast repeated calls
- **No API key needed** for NASA POWER

---

## Import Patterns: What You Can Import

### Option 1: Import Everything Convenience

```python
from solar_quant import (
    load_solar_parameters,   # NASA data loader
    BinomialTree,            # Pricing engine
    calculate_greeks,        # Risk metrics
    monte_carlo_option_price # MC simulation
)
```

### Option 2: Import Modules

```python
from solar_quant import data_loader_nasa, binomial

params = data_loader_nasa.load_solar_parameters()
tree = binomial.BinomialTree(**params, N=100, payoff_type='call')
```

### Option 3: Module-Level Import

```python
import solar_quant

params = solar_quant.load_solar_parameters()
tree = solar_quant.BinomialTree(**params, N=100, payoff_type='call')
```

**Recommended:** Option 1 (explicit convenience imports)

---

## Real-World Usage Scenarios

### Scenario 1: Price a Solar Farm's Production Risk

**Goal:** I own a solar farm. What's the cost to hedge revenue risk?

```python
from solar_quant import load_solar_parameters, BinomialTree, calculate_greeks

# My farm location
params = load_solar_parameters(
    lat=33.45,  # Arizona
    lon=-112.07
)

# Price 1-year revenue protection
tree = BinomialTree(**params, N=500, payoff_type='call')
hedge_cost = tree.price()

# Calculate hedge ratio
greeks = calculate_greeks(**params)

print(f"Hedge cost: ${hedge_cost:.6f} per kWh/m²/day")
print(f"Need to hedge {greeks['delta']:.1%} of production")
```

**Output:**
```
Hedge cost: $0.028432 per kWh/m²/day
Need to hedge 62.3% of production
```

---

### Scenario 2: Compare Investment Locations

**Goal:** Which location has lower option premiums (= more stable sun)?

```python
from solar_quant import load_solar_parameters, BinomialTree

locations = {
    'Arizona': (33.45, -112.07),
    'Spain': (40.42, -3.70),
    'Taiwan': (24.99, 121.30)
}

for name, (lat, lon) in locations.items():
    params = load_solar_parameters(lat=lat, lon=lon, volatility_cap=2.0)
    price = BinomialTree(**params, N=100, payoff_type='call').price()
    premium = price / params['S0']

    print(f"{name:8s} - Premium: {premium:.1%}, Vol: {params['sigma']:.0%}")
```

**Output:**
```
Arizona  - Premium: 46.4%, Vol: 150%
Spain    - Premium: 57.0%, Vol: 175%
Taiwan   - Premium: 69.0%, Vol: 200%
```

**Insight:** Arizona has most stable sun → lowest premium → best for solar farms

---

### Scenario 3: Use Your Own Data (Not NASA)

**Goal:** I have solar sensor data in a CSV file.

```python
import pandas as pd
import numpy as np
from solar_quant import BinomialTree

# Load YOUR data
df = pd.read_csv('my_solar_farm_data.csv')
# Columns: date, irradiance_kwh_m2

# Calculate volatility
returns = np.log(df['irradiance_kwh_m2'] / df['irradiance_kwh_m2'].shift(1))
volatility = returns.std() * np.sqrt(365)

# Set parameters manually
params = {
    'S0': df['irradiance_kwh_m2'].iloc[-1] * 0.10,  # Current × $/kWh
    'K': df['irradiance_kwh_m2'].iloc[-1] * 0.10,   # Strike = spot
    'T': 1.0,    # 1 year
    'r': 0.05,   # 5%
    'sigma': min(volatility, 2.0)  # Cap at 200%
}

# Price as usual
price = BinomialTree(**params, N=1000, payoff_type='call').price()
print(f"Option price with custom data: ${price:.6f}")
```

**Key Point:** You control the parameters. The library just does the math.

---

### Scenario 4: Build a REST API

**Goal:** Serve solar option prices via HTTP.

```python
from fastapi import FastAPI
from pydantic import BaseModel
from solar_quant import load_solar_parameters, BinomialTree

app = FastAPI()

class PriceRequest(BaseModel):
    lat: float
    lon: float

@app.post("/price")
def price_solar_option(req: PriceRequest):
    params = load_solar_parameters(lat=req.lat, lon=req.lon)
    tree = BinomialTree(**params, N=200, payoff_type='call')

    return {
        "call_price": tree.price(),
        "spot_price": params['S0'],
        "volatility": params['sigma']
    }

# Run: uvicorn myapi:app
# Test: curl -X POST localhost:8000/price -d '{"lat":24.99,"lon":121.30}'
```

**Response:**
```json
{
  "call_price": 0.035645,
  "spot_price": 0.0516,
  "volatility": 2.0
}
```

---

### Scenario 5: Batch Pricing for Portfolio

**Goal:** Price options for 100 different solar farms.

```python
from solar_quant import load_solar_parameters, BinomialTree
import pandas as pd

# Your portfolio
farms = pd.read_csv('solar_farm_locations.csv')
# Columns: farm_id, lat, lon, capacity_mw

results = []
for _, farm in farms.iterrows():
    params = load_solar_parameters(lat=farm['lat'], lon=farm['lon'])
    price = BinomialTree(**params, N=200, payoff_type='call').price()

    results.append({
        'farm_id': farm['farm_id'],
        'capacity_mw': farm['capacity_mw'],
        'call_price': price,
        'hedge_cost_total': price * farm['capacity_mw'] * 1000  # Scale to MW
    })

portfolio = pd.DataFrame(results)
print(f"Total hedge cost: ${portfolio['hedge_cost_total'].sum():.2f}")
```

---

## Configuration Options

### Volatility Methodology

```python
# Default: Log returns (recommended)
params = load_solar_parameters(volatility_method='log')

# Legacy: Percentage change (has artifacts)
params = load_solar_parameters(volatility_method='pct_change')

# Alternative: Normalized
params = load_solar_parameters(volatility_method='normalized')
```

### Volatility Capping

```python
# Capped at 200% (stable)
params = load_solar_parameters(volatility_cap=2.0)

# Uncapped (real volatility, may be extreme)
params = load_solar_parameters(volatility_cap=None)

# Custom cap
params = load_solar_parameters(volatility_cap=1.5)  # 150%
```

### Time Parameters

```python
# 1-year option (default)
params = load_solar_parameters(T=1.0)

# 6-month option
params = load_solar_parameters(T=0.5)

# 2-year option
params = load_solar_parameters(T=2.0)
```

### Risk-Free Rate

```python
# US T-Bill rate ~5% (default)
params = load_solar_parameters(r=0.05)

# European rate ~3%
params = load_solar_parameters(r=0.03)

# Custom rate
params = load_solar_parameters(r=0.04)
```

---

## What Gets Returned?

### Parameters Dictionary

```python
params = load_solar_parameters()

# Keys available:
params['S0']       # Spot price (float) - e.g., 0.0516
params['K']        # Strike price (float) - same as S0
params['T']        # Maturity (float) - e.g., 1.0
params['r']        # Risk-free rate (float) - e.g., 0.05
params['sigma']    # Volatility (float) - e.g., 2.0 (200%)

# Metadata:
params['volatility_method']     # 'log', 'pct_change', 'normalized'
params['volatility_cap']        # 2.0 or None
params['deseasonalized']        # True/False
params['data_points']           # Number of days (e.g., 1827)
```

### Greeks Dictionary

```python
greeks = calculate_greeks(**params)

# Keys:
greeks['delta']   # Hedge ratio (0-1)
greeks['gamma']   # Delta sensitivity
greeks['theta']   # Time decay (per day, negative)
greeks['vega']    # Volatility sensitivity
greeks['rho']     # Rate sensitivity
```

---

## Performance Tips

### Fast Pricing (API Response Time)

```python
# N=100 steps → ~0.01 seconds
tree = BinomialTree(**params, N=100, payoff_type='call')
```

### Accurate Pricing (Research Quality)

```python
# N=1000 steps → ~0.5 seconds
tree = BinomialTree(**params, N=1000, payoff_type='call')
```

### Maximum Accuracy

```python
# N=5000 steps → ~10 seconds
tree = BinomialTree(**params, N=5000, payoff_type='call')
```

### Use Cache

```python
# First call: Fetches NASA data (~2 seconds)
params = load_solar_parameters(lat=24.99, lon=121.30, cache=True)

# Subsequent calls: Uses cache (~0.1 seconds)
params = load_solar_parameters(lat=24.99, lon=121.30, cache=True)
```

---

## Common Errors and Fixes

### Error: "No module named 'solar_quant'"

**Fix:**
```bash
pip install git+https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git@v0.2.0-research
```

### Error: "NASA API rate limit exceeded"

**Fix:** Cache is automatic. If you still hit limits:
```python
# Don't query repeatedly - use variables
params = load_solar_parameters()  # Call once
price1 = BinomialTree(**params, N=100).price()
price2 = BinomialTree(**params, N=500).price()  # Reuse params
```

### Warning: "Volatility capped at 200%"

**This is intentional.** Options:
```python
# Accept cap (recommended)
params = load_solar_parameters(volatility_cap=2.0)

# Use uncapped (advanced)
params = load_solar_parameters(volatility_cap=None)
```

---

## Summary: The Import You Need

**For 90% of use cases:**

```python
from solar_quant import load_solar_parameters, BinomialTree

params = load_solar_parameters()  # Data input happens here
price = BinomialTree(**params, N=500, payoff_type='call').price()
```

**That's the answer to "how do we plug in the data."**

- Data comes from **NASA API** (automatic)
- Processed into **pricing parameters** (automatic)
- You just **call functions** (simple)

---

## Next Steps

1. **Try it:** Run `examples/01_quick_start.py`
2. **Read:** `USAGE_GUIDE.md` for more patterns
3. **Explore:** `examples/` directory for 5 working examples
4. **Build:** Your own application

---

**Questions?**
- GitHub Issues: https://github.com/YOUR_USERNAME/solarpunk-bitcoin/issues
- Usage Guide: `USAGE_GUIDE.md`
- API Reference: `energy_derivatives/docs/API_REFERENCE.md`

**Version:** 0.2.0-research
**Status:** Research-Ready ✅
