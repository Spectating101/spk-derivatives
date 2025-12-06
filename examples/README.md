# SPK Derivatives Examples

Practical examples showing how to use the solar derivatives pricing library.

## Quick Reference

| Example | What It Shows | Use When |
|---------|---------------|----------|
| `01_quick_start.py` | Simplest possible usage (5 lines) | You want to price a basic option quickly |
| `02_multi_location.py` | Compare prices across locations | You need multi-region analysis |
| `03_greeks_analysis.py` | Calculate and interpret risk metrics | You need risk management metrics |
| `04_convergence_test.py` | Validate pricing methods | You want to verify accuracy |
| `05_custom_data.py` | Use your own solar data | You have data from local sensors/API |

## Running the Examples

### Prerequisites

```bash
# Install the library
pip install git+https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git@v0.2.0-research

# Or for local development
cd solarpunk-bitcoin
pip install -e ".[viz]"
```

### Run an Example

```bash
cd examples
python 01_quick_start.py
```

## Example Descriptions

### 01_quick_start.py
**Simplest possible usage - 5 lines of code**

```python
from spk_derivatives import load_solar_parameters, BinomialTree

params = load_solar_parameters()
tree = BinomialTree(**params, N=100, payoff_type='call')
print(f"Price: ${tree.price():.6f}")
```

**Output:**
```
SOLAR CALL OPTION PRICE
Spot Price:   $0.0516/kWh
Call Price:   $0.035645
```

**Use this when:**
- You need a quick price
- You're testing the installation
- You want the default Taiwan location

---

### 02_multi_location.py
**Compare option prices across different geographic locations**

Prices solar derivatives for:
- Taiwan (monsoon climate - high volatility)
- Arizona (desert - stable sun)
- Spain (Mediterranean)
- Germany (temperate - variable)
- California (coastal)

**Output:**
```
Location          Spot ($/kWh)  Volatility  Call Price  Premium
Taiwan            $0.0516       200.00%     $0.035645   69.01%
Arizona           $0.0612       150.00%     $0.028432   46.44%
...
```

**Use this when:**
- Comparing investment locations
- Portfolio diversification analysis
- Understanding geographic risk differences

---

### 03_greeks_analysis.py
**Calculate and interpret option Greeks (Delta, Gamma, Theta, Vega, Rho)**

Shows:
- What each Greek measures
- How to interpret for risk management
- Practical hedging scenarios
- Time decay strategies

**Output:**
```
GREEKS (RISK METRICS)
Delta (Δ): 0.6341 → Hedge ratio
Gamma (Γ): 4.3574 → Delta sensitivity
Theta (Θ): -0.00013100 → Daily time decay
Vega (ν):  0.033905 → Volatility sensitivity
Rho (ρ):   0.014312 → Rate sensitivity
```

**Use this when:**
- Hedging a solar farm
- Managing options portfolio
- Understanding risk exposure
- Implementing delta-neutral strategies

---

### 04_convergence_test.py
**Validate that binomial and Monte Carlo methods converge**

Tests:
- Binomial tree with different step counts (100, 500, 1000, 2000)
- Monte Carlo with different path counts (10k, 50k, 100k, 200k)
- Compares final prices
- Shows convergence rates

**Output:**
```
CONVERGENCE ANALYSIS
Binomial (N=2000):     $0.035645
Monte Carlo (N=200k):  $0.034754
Percentage Difference: 2.50%

Status: ✅ PASS
Convergence Quality: EXCELLENT
```

**Use this when:**
- Validating implementation accuracy
- Testing extreme parameters
- Academic publication (show robustness)
- Debugging pricing issues

---

### 05_custom_data.py
**Integrate your own solar irradiance data**

Shows how to:
1. Load data from CSV/database/API
2. Calculate volatility
3. Set up pricing parameters
4. Price derivatives
5. Apply to real solar farm

**Code pattern:**
```python
# Load your data
df = pd.read_csv('my_solar_data.csv')

# Calculate volatility
returns = np.log(df['irradiance'] / df['irradiance'].shift(1))
volatility = returns.std() * np.sqrt(365)

# Set parameters
params = {
    'S0': current_irradiance * energy_price,
    'K': current_irradiance * energy_price,
    'T': 1.0,
    'r': 0.05,
    'sigma': volatility
}

# Price
tree = BinomialTree(**params, N=1000, payoff_type='call')
price = tree.price()
```

**Use this when:**
- You have your own solar sensor data
- You want to use a different API
- You need custom data processing
- You're integrating into existing system

---

## Common Patterns

### Pattern 1: Quick Price Check
```python
from spk_derivatives import load_solar_parameters, BinomialTree

params = load_solar_parameters()
price = BinomialTree(**params, N=100, payoff_type='call').price()
print(f"${price:.6f}")
```

### Pattern 2: Custom Location
```python
params = load_solar_parameters(lat=YOUR_LAT, lon=YOUR_LON)
```

### Pattern 3: Uncapped Volatility
```python
params = load_solar_parameters(volatility_cap=None)
```

### Pattern 4: Different Methodology
```python
params = load_solar_parameters(volatility_method='normalized')
```

### Pattern 5: Greeks Calculation
```python
from spk_derivatives import calculate_greeks

greeks = calculate_greeks(S0=0.05, K=0.05, T=1.0, r=0.05, sigma=2.0)
print(f"Delta: {greeks['delta']:.3f}")
```

---

## Troubleshooting

### "ImportError: No module named 'spk_derivatives'"

**Solution:**
```bash
pip install git+https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git@v0.2.0-research
```

### "NASA API rate limit exceeded"

**Solution:** Use cached data (automatic by default)
```python
params = load_solar_parameters(cache=True)  # Default
```

### "ValueError: Unknown volatility method"

**Solution:** Use valid method
```python
params = load_solar_parameters(volatility_method='log')  # 'log', 'pct_change', 'normalized'
```

### Examples run too slowly

**Solution:** Reduce step count
```python
tree = BinomialTree(**params, N=100, payoff_type='call')  # Faster
# Instead of N=1000 (slower but more accurate)
```

---

## Next Steps

1. **Read USAGE_GUIDE.md** for comprehensive API documentation
2. **Check API_REFERENCE.md** for detailed function signatures
3. **Explore notebooks/main.ipynb** for interactive exploration
4. **Build your own application** using these patterns

---

## Questions?

- **Issues:** https://github.com/YOUR_USERNAME/solarpunk-bitcoin/issues
- **Discussions:** https://github.com/YOUR_USERNAME/solarpunk-bitcoin/discussions
- **Documentation:** See `energy_derivatives/docs/`

**Version:** 0.2.0-research
**Last Updated:** December 6, 2024
