# SPK Derivatives

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Quantitative pricing framework for solar energy derivatives with NASA satellite data integration.**

A professional-grade Python library for pricing renewable energy-backed financial instruments using modern derivative pricing theory. Features industry-standard volatility estimation, comprehensive Greeks calculation, and real-time NASA POWER API integration.

## Features

- **Pricing Engines**: Binomial trees and Monte Carlo simulation
- **Risk Metrics**: Complete Greeks (Delta, Vega, Theta, Rho, Gamma)
- **Real Data**: NASA POWER API for solar irradiance (Global Horizontal Irradiance)
- **Volatility Methods**: Log returns, percent change, standard deviation (configurable)
- **Professional Workflow**: Validation, comparison, batch pricing, save/load results
- **Context Translation**: GHI → kWh → dollar value conversions

## Installation

```bash
pip install spk-derivatives
```

### Development Installation

```bash
git clone https://github.com/Spectating101/spk-derivatives.git
cd spk-derivatives
pip install -e ".[dev,viz]"
```

## Quick Start

Price a solar call option in 5 lines:

```python
from spk_derivatives import load_solar_parameters, BinomialTree

# Load solar data from NASA (Taiwan by default)
params = load_solar_parameters()

# Price an at-the-money call option
tree = BinomialTree(**params, N=100, payoff_type='call')
price = tree.price()

print(f"Option price: ${price:.6f}")
```

## Core Usage

### 1. Pricing with Custom Location

```python
from spk_derivatives import load_solar_parameters, BinomialTree, calculate_greeks

# Load data for Phoenix, Arizona
params = load_solar_parameters(
    lat=33.45,
    lon=-112.07,
    volatility_method='log',  # 'log', 'pct_change', or 'std'
    volatility_cap=2.0        # Optional cap at 200%
)

# Price option
tree = BinomialTree(**params, N=500, payoff_type='call')
price = tree.price()

# Calculate Greeks
greeks = calculate_greeks(**params)
print(f"Delta: {greeks['Delta']:.4f}")
print(f"Vega: {greeks['Vega']:.4f}")
```

### 2. Professional Workflow

```python
from spk_derivatives import (
    load_solar_parameters,
    BinomialTree,
    calculate_greeks,
    PricingResult,
    PricingValidator
)

# Price
params = load_solar_parameters(lat=33.45, lon=-112.07)
price = BinomialTree(**params, N=500).price()
greeks = calculate_greeks(**params)

# Create result object
result = PricingResult(
    price=price,
    greeks=greeks,
    parameters=params,
    metadata={'location': 'Phoenix', 'system_kw': 50}
)

# Validate
validation = PricingValidator.validate(result)
print(f"Status: {validation['status']}")

# Save
result.save('phoenix_50kw.json')
result.to_csv('phoenix_50kw.csv')
```

### 3. Compare Multiple Scenarios

```python
from spk_derivatives import batch_price, ResultsComparator, BinomialTree

scenarios = [
    {'lat': 24.99, 'lon': 121.30},  # Taiwan
    {'lat': 33.45, 'lon': -112.07},  # Arizona
    {'lat': 40.42, 'lon': -3.70}     # Spain
]

labels = ['Taiwan', 'Arizona', 'Spain']

def pricing_func(params):
    return BinomialTree(**params, N=500).price()

comparator = batch_price(scenarios, pricing_func, labels)
print(comparator.comparison_table())

best_idx, best_label, best_value = comparator.best_value()
print(f"Best location: {best_label} (${best_value:.6f})")
```

## Volatility Methodology

SPK Derivatives uses industry-standard volatility estimation with full transparency:

```python
params = load_solar_parameters(
    lat=24.99,
    lon=121.30,
    volatility_method='log',     # Recommended: log returns (default)
    volatility_cap=2.0,          # Optional: cap at 200%
    start_date='2020-01-01',
    end_date='2024-12-31'
)

# Returned parameters include methodology metadata
print(params['volatility_method'])      # 'log'
print(params['volatility_raw'])         # Raw calculated value
print(params['volatility_capped'])      # Whether cap was applied
print(params['sigma'])                  # Final volatility used
```

**Methods**:
- `'log'`: Log returns (recommended, industry standard)
- `'pct_change'`: Percent change
- `'std'`: Standard deviation

## Examples

See the [`examples/`](examples/) directory for complete demonstrations:

- `01_quick_start.py` - 5-second quick start
- `02_multi_location.py` - Geographic comparison
- `03_greeks_analysis.py` - Risk metrics
- `04_convergence_test.py` - Validation
- `05_custom_data.py` - Use your own data
- `06_contextual_pricing.py` - Context translation
- `07_professional_workflow.py` - Complete workflow

## API Reference

### Data Loading

```python
load_solar_parameters(
    lat=24.99,                   # Latitude
    lon=121.30,                  # Longitude
    start_date='2020-01-01',     # Start date
    end_date='2024-12-31',       # End date
    T=1.0,                       # Time to maturity (years)
    r=0.05,                      # Risk-free rate
    volatility_method='log',     # Volatility calculation method
    volatility_cap=None          # Optional volatility cap
)
```

### Pricing

```python
BinomialTree(
    S0,              # Initial price
    K,               # Strike price
    T,               # Time to maturity
    r,               # Risk-free rate
    sigma,           # Volatility
    N=100,           # Number of steps
    payoff_type='call'  # 'call' or 'redeemable'
).price()
```

### Greeks

```python
calculate_greeks(
    S0, K, T, r, sigma,
    pricing_method='binomial',  # or 'monte_carlo'
    N=100
)
# Returns: {'Delta': ..., 'Gamma': ..., 'Vega': ..., 'Theta': ..., 'Rho': ...}
```

## Testing

```bash
pytest energy_derivatives/tests/
```

## Requirements

- Python ≥ 3.8
- numpy ≥ 1.20.0
- pandas ≥ 1.3.0
- requests ≥ 2.26.0
- scipy ≥ 1.7.0

### Optional Dependencies

```bash
pip install spk-derivatives[viz]        # Visualization
pip install spk-derivatives[dev]        # Development tools
pip install spk-derivatives[all]        # Everything
```

## Mathematical Framework

Under risk-neutral measure, solar energy prices follow Geometric Brownian Motion:

$$dS_t = r S_t dt + \sigma S_t dW_t$$

**Binomial Model**: Cox-Ross-Rubinstein with backward induction
**Monte Carlo**: Geometric Brownian Motion simulation
**Greeks**: Finite difference methods

See [`energy_derivatives/README.md`](energy_derivatives/README.md) for full mathematical details.

## License

MIT License - see [LICENSE](LICENSE) file.

## Citation

If you use SPK Derivatives in academic research:

```bibtex
@software{spk_derivatives_2024,
  author = {SPK Derivatives Team},
  title = {SPK Derivatives: Quantitative Pricing Framework for Solar Energy Derivatives},
  year = {2024},
  url = {https://github.com/Spectating101/spk-derivatives},
  version = {0.2.0}
}
```

## Contributing

Contributions welcome! Please open an issue or pull request on [GitHub](https://github.com/Spectating101/spk-derivatives).

## Support

- **Issues**: [GitHub Issues](https://github.com/Spectating101/spk-derivatives/issues)
- **Examples**: See [`examples/`](examples/) directory
- **Documentation**: Full docs in [`energy_derivatives/README.md`](energy_derivatives/README.md)

---

**Version**: 0.2.0
**Author**: SPK Derivatives Team
**Email**: s1133958@mail.yzu.edu.tw
