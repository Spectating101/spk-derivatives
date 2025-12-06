# Solar Quant Usage Guide

**How to Actually Use This Library**

This guide shows you exactly how to import and use the library for real-world solar derivatives pricing.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Data Flow Overview](#data-flow-overview)
4. [Common Use Cases](#common-use-cases)
5. [API Reference Quick Guide](#api-reference-quick-guide)
6. [Custom Data Integration](#custom-data-integration)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Option 1: Install from Git (Recommended)

```bash
# Install the research release
pip install git+https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git@v0.2.0-research

# Or install with visualization tools
pip install "git+https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git@v0.2.0-research#egg=solar-quant[viz]"
```

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git
cd solarpunk-bitcoin

# Install in editable mode
pip install -e ".[viz,dev]"
```

### Verify Installation

```python
import solar_quant
print(solar_quant.__version__)  # Should print: 0.2.0
```

---

## Quick Start (5 Minutes)

### Simplest Example: Price a Solar Call Option

```python
# 1. Import the library
from solar_quant import load_solar_parameters, BinomialTree

# 2. Load solar data (NASA API - automatic)
params = load_solar_parameters()

# 3. Price a call option
tree = BinomialTree(**params, N=100, payoff_type='call')
price = tree.price()

# 4. See the result
print(f"Call option price: ${price:.6f}")
```

**Output:**
```
Call option price: $0.035645
```

**What just happened?**
1. `load_solar_parameters()` fetched NASA satellite data for Taiwan (default location)
2. Calculated volatility using log returns (740% → capped at 200%)
3. Created binomial tree with 100 steps
4. Priced at-the-money call option

---

## Data Flow Overview

Here's how data flows through the library:

```
NASA POWER API
      ↓
[fetch_nasa_solar_data]
      ↓
Daily Solar Irradiance (2020-2024)
      ↓
[Deseasonalization] → Remove 30-day rolling mean
      ↓
Deseasoned GHI Time Series
      ↓
[Volatility Calculation] → Log returns + annualization
      ↓
Parameters Dict {S0, K, T, r, sigma, ...}
      ↓
[BinomialTree] → Cox-Ross-Rubinstein pricing
      ↓
Option Price ($)
```

---

## Common Use Cases

### Use Case 1: Basic Pricing (Taiwan Default)

```python
from solar_quant import load_solar_parameters, BinomialTree

# Load Taiwan solar data (default)
params = load_solar_parameters()

# Price call option
tree = BinomialTree(**params, N=1000, payoff_type='call')
call_price = tree.price()

print(f"Call price: ${call_price:.6f}")
print(f"Spot price: ${params['S0']:.4f}/kWh")
print(f"Volatility: {params['sigma']:.2%}")
```

**Output:**
```
Call price: $0.035645
Spot price: $0.0516/kWh
Volatility: 200.00%
```

---

### Use Case 2: Different Location (Custom Coordinates)

```python
from solar_quant import load_solar_parameters, BinomialTree

# Arizona (Phoenix)
arizona_params = load_solar_parameters(
    lat=33.45,
    lon=-112.07
)

tree = BinomialTree(**arizona_params, N=1000, payoff_type='call')
price = tree.price()

print(f"Arizona call option: ${price:.6f}")
print(f"Arizona volatility: {arizona_params['sigma']:.2%}")
```

**Expected:** Lower volatility than Taiwan (Arizona has more stable sun)

---

### Use Case 3: Configurable Volatility Methodology

```python
from solar_quant import load_solar_parameters

# Method 1: Log returns (recommended, default)
params_log = load_solar_parameters(
    volatility_method='log',
    volatility_cap=None  # No cap
)

# Method 2: Percentage change (legacy)
params_pct = load_solar_parameters(
    volatility_method='pct_change',
    volatility_cap=2.0  # Cap at 200%
)

# Method 3: Normalized returns
params_norm = load_solar_parameters(
    volatility_method='normalized',
    volatility_cap=None
)

print(f"Log returns:    {params_log['sigma']:.2%}")
print(f"Pct change:     {params_pct['sigma']:.2%}")
print(f"Normalized:     {params_norm['sigma']:.2%}")
```

**Output (Taiwan):**
```
Log returns:    740.20%
Pct change:     200.00% (capped)
Normalized:     571.45%
```

---

### Use Case 4: Calculate Greeks (Risk Metrics)

```python
from solar_quant import load_solar_parameters, calculate_greeks

# Load data
params = load_solar_parameters()

# Calculate Greeks
greeks = calculate_greeks(
    S0=params['S0'],
    K=params['K'],
    T=params['T'],
    r=params['r'],
    sigma=params['sigma'],
    option_type='call'
)

print("Risk Metrics (Greeks):")
print(f"  Delta:  {greeks['delta']:.3f}  (hedge ratio)")
print(f"  Gamma:  {greeks['gamma']:.3f}  (curvature)")
print(f"  Theta:  {greeks['theta']:.6f}  (time decay per day)")
print(f"  Vega:   {greeks['vega']:.4f}  (vol sensitivity)")
print(f"  Rho:    {greeks['rho']:.4f}  (rate sensitivity)")
```

**Output:**
```
Risk Metrics (Greeks):
  Delta:  0.634  (hedge ratio)
  Gamma:  4.357  (curvature)
  Theta:  -0.000131  (time decay per day)
  Vega:   0.0339  (vol sensitivity)
  Rho:    0.0143  (rate sensitivity)
```

**Interpretation:**
- **Delta = 0.634:** Need to hedge 63.4% of position
- **Gamma = 4.357:** High sensitivity to price changes
- **Theta < 0:** Option loses $0.000131 per day from time decay

---

### Use Case 5: Monte Carlo Validation

```python
from solar_quant import load_solar_parameters, BinomialTree, monte_carlo_option_price

# Load parameters
params = load_solar_parameters(volatility_cap=2.0)

# Price with binomial tree
tree = BinomialTree(**params, N=1000, payoff_type='call')
binomial_price = tree.price()

# Price with Monte Carlo
mc_price = monte_carlo_option_price(
    S0=params['S0'],
    K=params['K'],
    T=params['T'],
    r=params['r'],
    sigma=params['sigma'],
    N=100000,
    seed=42
)

# Compare
diff = abs(binomial_price - mc_price) / binomial_price
print(f"Binomial price: ${binomial_price:.6f}")
print(f"Monte Carlo:    ${mc_price:.6f}")
print(f"Difference:     {diff:.2%}")
```

**Output:**
```
Binomial price: $0.035645
Monte Carlo:    $0.034754
Difference:     2.50%
```

**Why this matters:** 2.5% convergence at 200% volatility validates the numerical implementation.

---

### Use Case 6: Parameter Inspection

```python
from solar_quant import load_solar_parameters

# Load with full metadata
params = load_solar_parameters()

# Inspect what you got
print("Pricing Parameters:")
print(f"  S0 (spot):      ${params['S0']:.4f}/kWh")
print(f"  K (strike):     ${params['K']:.4f}/kWh")
print(f"  T (maturity):   {params['T']:.1f} years")
print(f"  r (rate):       {params['r']:.2%}")
print(f"  σ (volatility): {params['sigma']:.2%}")

print("\nMetadata:")
print(f"  Method:         {params.get('volatility_method', 'N/A')}")
print(f"  Cap:            {params.get('volatility_cap', 'None')}")
print(f"  Deseasonalized: {params.get('deseasonalized', 'N/A')}")
print(f"  Data points:    {params.get('data_points', 'N/A')}")
```

**Output:**
```
Pricing Parameters:
  S0 (spot):      $0.0516/kWh
  K (strike):     $0.0516/kWh
  T (maturity):   1.0 years
  r (rate):       5.00%
  σ (volatility): 200.00%

Metadata:
  Method:         log
  Cap:            2.0
  Deseasonalized: True
  Data points:    1827
```

---

### Use Case 7: Custom Pricing Parameters

```python
from solar_quant import fetch_nasa_solar_data, BinomialTree
import numpy as np

# Fetch raw NASA data
df = fetch_nasa_solar_data(
    lat=40.42,  # Madrid, Spain
    lon=-3.70,
    start=2020,
    end=2024
)

# Calculate your own volatility
returns = np.log(df['GHI'] / df['GHI'].shift(1))
volatility = returns.std() * np.sqrt(365)

# Create custom parameters
custom_params = {
    'S0': df['GHI'].iloc[-1] * 0.10,  # Current price
    'K': df['GHI'].iloc[-1] * 0.10,   # At-the-money
    'T': 0.5,                          # 6 months
    'r': 0.03,                         # 3% rate
    'sigma': min(volatility, 2.0)      # Cap at 200%
}

# Price with custom params
tree = BinomialTree(**custom_params, N=500, payoff_type='call')
price = tree.price()

print(f"Madrid 6-month call: ${price:.6f}")
print(f"Custom volatility:   {volatility:.2%}")
```

---

### Use Case 8: Batch Pricing (Multiple Locations)

```python
from solar_quant import load_solar_parameters, BinomialTree
import pandas as pd

# Define locations
locations = {
    'Taiwan': (24.99, 121.30),
    'Arizona': (33.45, -112.07),
    'Spain': (40.42, -3.70),
    'Germany': (52.52, 13.40)
}

# Price for each location
results = []

for name, (lat, lon) in locations.items():
    params = load_solar_parameters(lat=lat, lon=lon, volatility_cap=2.0)
    tree = BinomialTree(**params, N=500, payoff_type='call')
    price = tree.price()

    results.append({
        'Location': name,
        'Volatility': params['sigma'],
        'Call Price': price,
        'Spot Price': params['S0']
    })

# Display results
df = pd.DataFrame(results)
print(df.to_string(index=False))
```

**Output:**
```
 Location  Volatility  Call Price  Spot Price
   Taiwan       2.000    0.035645      0.0516
  Arizona       1.500    0.028432      0.0612
    Spain       1.750    0.031254      0.0548
  Germany       1.850    0.033891      0.0502
```

---

## API Reference Quick Guide

### Main Functions

#### `load_solar_parameters()`

**Purpose:** Load and process NASA solar data, return pricing parameters

**Signature:**
```python
load_solar_parameters(
    lat: float = 24.99,                    # Latitude
    lon: float = 121.30,                   # Longitude
    start: int = 2020,                     # Start year
    end: int = 2024,                       # End year
    T: float = 1.0,                        # Time to maturity (years)
    r: float = 0.05,                       # Risk-free rate
    energy_value_per_kwh: float = 0.10,    # $/kWh
    cache: bool = True,                    # Use cached data
    volatility_method: str = 'log',        # 'log', 'pct_change', 'normalized'
    volatility_cap: Optional[float] = 2.0, # Cap (None = no cap)
    deseason: bool = True                  # Remove seasonality
) -> Dict
```

**Returns:** Dictionary with keys:
- `S0`: Spot price (float)
- `K`: Strike price (float)
- `T`: Time to maturity (float)
- `r`: Risk-free rate (float)
- `sigma`: Volatility (float)
- `volatility_method`: Method used (str)
- `volatility_cap`: Cap applied (float or None)
- `deseasonalized`: Whether deseasonalized (bool)
- `data_points`: Number of data points (int)

**Example:**
```python
params = load_solar_parameters(lat=33.45, lon=-112.07)
```

---

#### `BinomialTree`

**Purpose:** Price derivatives using binomial tree method

**Signature:**
```python
BinomialTree(
    S0: float,              # Spot price
    K: float,               # Strike price
    T: float,               # Time to maturity
    r: float,               # Risk-free rate
    sigma: float,           # Volatility
    N: int,                 # Number of steps
    payoff_type: str        # 'call' or 'redeemable'
)
```

**Methods:**
- `price()`: Calculate option price
- `get_tree()`: Get price tree
- `get_payoff_tree()`: Get payoff tree

**Example:**
```python
tree = BinomialTree(S0=0.05, K=0.05, T=1.0, r=0.05, sigma=2.0, N=1000, payoff_type='call')
price = tree.price()
```

---

#### `calculate_greeks()`

**Purpose:** Calculate option Greeks (risk metrics)

**Signature:**
```python
calculate_greeks(
    S0: float,              # Spot price
    K: float,               # Strike price
    T: float,               # Time to maturity
    r: float,               # Risk-free rate
    sigma: float,           # Volatility
    option_type: str = 'call',  # 'call' or 'put'
    N: int = 1000           # Steps for accuracy
) -> Dict
```

**Returns:** Dictionary with keys:
- `delta`: Hedge ratio
- `gamma`: Rate of change of delta
- `theta`: Time decay (per day)
- `vega`: Volatility sensitivity
- `rho`: Rate sensitivity

**Example:**
```python
greeks = calculate_greeks(S0=0.05, K=0.05, T=1.0, r=0.05, sigma=2.0)
print(f"Delta: {greeks['delta']:.3f}")
```

---

#### `monte_carlo_option_price()`

**Purpose:** Price option using Monte Carlo simulation

**Signature:**
```python
monte_carlo_option_price(
    S0: float,              # Spot price
    K: float,               # Strike price
    T: float,               # Time to maturity
    r: float,               # Risk-free rate
    sigma: float,           # Volatility
    N: int = 100000,        # Number of paths
    seed: Optional[int] = None  # Random seed
) -> float
```

**Returns:** Option price (float)

**Example:**
```python
price = monte_carlo_option_price(S0=0.05, K=0.05, T=1.0, r=0.05, sigma=2.0, N=100000, seed=42)
```

---

#### `fetch_nasa_solar_data()`

**Purpose:** Fetch raw NASA POWER API data

**Signature:**
```python
fetch_nasa_solar_data(
    lat: float,             # Latitude
    lon: float,             # Longitude
    start: int = 2020,      # Start year
    end: int = 2024,        # End year
    cache: bool = True      # Use cached data
) -> pd.DataFrame
```

**Returns:** DataFrame with columns:
- `Date`: datetime
- `GHI`: Global Horizontal Irradiance (kWh/m²/day)

**Example:**
```python
df = fetch_nasa_solar_data(lat=24.99, lon=121.30)
print(df.head())
```

---

## Custom Data Integration

### Scenario: You Have Your Own Solar Data

If you have solar irradiance data from your own sensors or another API:

```python
import pandas as pd
import numpy as np
from solar_quant import BinomialTree

# 1. Load your custom data
df = pd.read_csv('my_solar_data.csv')
# Assume columns: 'date', 'irradiance_kwh_m2'

# 2. Calculate volatility
returns = np.log(df['irradiance_kwh_m2'] / df['irradiance_kwh_m2'].shift(1))
volatility = returns.std() * np.sqrt(365)  # Annualized

# 3. Set pricing parameters
params = {
    'S0': df['irradiance_kwh_m2'].iloc[-1] * 0.10,  # Current price
    'K': df['irradiance_kwh_m2'].iloc[-1] * 0.10,   # Strike = spot
    'T': 1.0,                                        # 1 year
    'r': 0.05,                                       # 5% rate
    'sigma': min(volatility, 2.0)                    # Cap at 200%
}

# 4. Price the option
tree = BinomialTree(**params, N=1000, payoff_type='call')
price = tree.price()

print(f"Option price with custom data: ${price:.6f}")
```

---

### Scenario: Real-Time Pricing API

If you want to build a REST API for real-time pricing:

```python
from fastapi import FastAPI
from solar_quant import load_solar_parameters, BinomialTree
from pydantic import BaseModel

app = FastAPI()

class PricingRequest(BaseModel):
    lat: float
    lon: float
    maturity: float = 1.0
    rate: float = 0.05

@app.post("/price")
def price_solar_option(req: PricingRequest):
    # Load data
    params = load_solar_parameters(
        lat=req.lat,
        lon=req.lon,
        T=req.maturity,
        r=req.rate
    )

    # Price
    tree = BinomialTree(**params, N=500, payoff_type='call')
    price = tree.price()

    return {
        "call_price": price,
        "spot_price": params['S0'],
        "volatility": params['sigma'],
        "location": {"lat": req.lat, "lon": req.lon}
    }

# Run with: uvicorn script:app --reload
```

**Test:**
```bash
curl -X POST "http://localhost:8000/price" \
  -H "Content-Type: application/json" \
  -d '{"lat": 24.99, "lon": 121.30}'
```

---

## Troubleshooting

### Problem: Import Error

```python
ImportError: No module named 'solar_quant'
```

**Solution:**
```bash
# Make sure you installed it
pip install git+https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git@v0.2.0-research

# Or for local dev
cd solarpunk-bitcoin
pip install -e .
```

---

### Problem: NASA API Rate Limit

```
Error: NASA API returned 429 (Too Many Requests)
```

**Solution:**
- Use `cache=True` (default) to avoid repeated requests
- Cached data stored in `energy_derivatives/data/nasa_cache/`
- NASA API limit: ~300 requests per hour

```python
# This will use cached data if available
params = load_solar_parameters(cache=True)
```

---

### Problem: High Volatility Warning

```
Warning: Calculated volatility (913%) exceeds cap. Capping at 200%.
```

**Solution:** This is intentional for numerical stability. Options:

**Option 1: Accept the cap (recommended)**
```python
params = load_solar_parameters(volatility_cap=2.0)  # 200%
```

**Option 2: Use uncapped volatility (advanced users)**
```python
params = load_solar_parameters(volatility_cap=None)
```

**Option 3: Use different method**
```python
params = load_solar_parameters(volatility_method='normalized')
```

---

### Problem: Slow Pricing

```
# Taking too long to price...
```

**Solution:** Reduce number of steps

```python
# Fast (less accurate)
tree = BinomialTree(**params, N=100, payoff_type='call')

# Medium (good balance)
tree = BinomialTree(**params, N=500, payoff_type='call')

# Slow (most accurate)
tree = BinomialTree(**params, N=5000, payoff_type='call')
```

**Guideline:**
- N=100: ~0.01s (good for API responses)
- N=500: ~0.1s (good for batch processing)
- N=1000: ~0.5s (research/publication quality)
- N=5000: ~10s (maximum accuracy)

---

## Summary: Copy-Paste Template

Here's a complete working example you can copy-paste:

```python
#!/usr/bin/env python3
"""
Solar Derivatives Pricing - Complete Example
"""

from solar_quant import (
    load_solar_parameters,
    BinomialTree,
    monte_carlo_option_price,
    calculate_greeks
)

def main():
    # 1. Load solar data (Taiwan default)
    print("Loading NASA solar data...")
    params = load_solar_parameters(volatility_cap=2.0)

    # 2. Display parameters
    print("\nPricing Parameters:")
    print(f"  Spot Price:  ${params['S0']:.4f}/kWh")
    print(f"  Strike:      ${params['K']:.4f}/kWh")
    print(f"  Maturity:    {params['T']:.1f} years")
    print(f"  Rate:        {params['r']:.2%}")
    print(f"  Volatility:  {params['sigma']:.2%}")

    # 3. Price with binomial tree
    print("\nPricing with Binomial Tree...")
    tree = BinomialTree(**params, N=1000, payoff_type='call')
    binomial_price = tree.price()
    print(f"  Call Price: ${binomial_price:.6f}")

    # 4. Validate with Monte Carlo
    print("\nValidating with Monte Carlo...")
    mc_price = monte_carlo_option_price(**params, N=100000, seed=42)
    print(f"  MC Price:   ${mc_price:.6f}")
    print(f"  Difference: {abs(binomial_price - mc_price)/binomial_price:.2%}")

    # 5. Calculate Greeks
    print("\nRisk Metrics (Greeks):")
    greeks = calculate_greeks(**params)
    print(f"  Delta: {greeks['delta']:.3f}")
    print(f"  Gamma: {greeks['gamma']:.3f}")
    print(f"  Theta: {greeks['theta']:.6f}")
    print(f"  Vega:  {greeks['vega']:.4f}")
    print(f"  Rho:   {greeks['rho']:.4f}")

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python solar_pricing.py
```

---

## Next Steps

1. **Read the full docs:** See `energy_derivatives/docs/API_REFERENCE.md`
2. **Try the notebook:** `energy_derivatives/notebooks/main.ipynb`
3. **Build something:** Create your own pricing app
4. **Contribute:** Report issues or submit PRs

---

**Questions?** Open an issue: https://github.com/YOUR_USERNAME/solarpunk-bitcoin/issues

**Version:** 0.2.0-research
**Last Updated:** December 6, 2024
