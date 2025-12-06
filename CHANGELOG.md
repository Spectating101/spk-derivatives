# Changelog

All notable changes to SPK Derivatives will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-12-06

### Added
- **Professional workflow tools**:
  - `PricingResult` class for saving/loading results
  - `ResultsComparator` for multi-scenario comparison
  - `PricingValidator` for sanity checks
  - `batch_price()` function for portfolio pricing
  - `comparative_context()` for benchmark comparisons
  - `break_even_analysis()` for payoff analysis

- **Context translation layer**:
  - `SolarSystemContext` for solar panel specifications
  - `PriceTranslator` for GHI → kWh → dollar conversions
  - `VolatilityTranslator` for volatility interpretation
  - `GreeksTranslator` for risk metric context
  - `create_contextual_summary()` for complete context

- **Enhanced examples**:
  - `06_contextual_pricing.py` - Context translation demo
  - `07_professional_workflow.py` - Complete workflow demo

### Changed
- **BREAKING**: Rewrote `get_volatility_params()` in `data_loader_nasa.py`
  - Now supports 3 methods: `'log'` (default), `'pct_change'`, `'std'`
  - Volatility capping is now optional and transparent
  - Returns metadata: `volatility_method`, `volatility_raw`, `volatility_capped`
  - **Migration**: Update calls to `load_solar_parameters()` to specify `volatility_method` if needed

- **Package renamed**: `solar-quant` → `spk-derivatives`
  - Python import: `from spk_derivatives import ...`
  - PyPI package: `pip install spk-derivatives`
  - GitHub: https://github.com/Spectating101/spk-derivatives

### Fixed
- Volatility calculation artifacts from `pct_change()` with small denominators
- Hidden volatility caps now transparent and configurable
- Export functions now include all metadata

### Removed
- Bloated documentation files (coursework submissions, research notes)
- Deployment files (Docker, Makefile) - can be recreated if needed
- Unrelated empirical data directories

## [0.1.0] - 2024-11-06

### Added
- Initial release
- **Core pricing engines**:
  - Binomial Option Pricing Model (BOPM)
  - Monte Carlo simulation
  - Greeks calculation (Delta, Vega, Theta, Rho, Gamma)

- **Data sources**:
  - NASA POWER API integration for solar irradiance
  - Bitcoin CEIR data loader
  - Automatic data fetching and caching

- **Visualization**:
  - Convergence plots
  - Greeks curves
  - Monte Carlo distributions
  - Stress testing charts

- **Examples**:
  - Quick start guide
  - Multi-location comparison
  - Greeks analysis
  - Convergence testing
  - Custom data usage

- **Infrastructure**:
  - FastAPI backend
  - Streamlit dashboard
  - Comprehensive test suite

### Documentation
- Complete mathematical framework
- API reference
- Usage examples
- Installation guide

---

## Migration Guide: v0.1.0 → v0.2.0

### Import Changes
```python
# OLD (v0.1.0):
from solar_quant import load_solar_parameters, BinomialTree

# NEW (v0.2.0):
from spk_derivatives import load_solar_parameters, BinomialTree
```

### Volatility Method Changes
```python
# For same behavior as v0.1.0:
params = load_solar_parameters(
    volatility_method='pct_change',
    volatility_cap=2.0
)

# Recommended (new default):
params = load_solar_parameters(
    volatility_method='log',  # Industry standard
    volatility_cap=None       # Optional
)
```

---

## Version History

- **0.2.0** (2024-12-06): Professional workflow + context translation + package rename
- **0.1.0** (2024-11-06): Initial release with core pricing engines

[0.2.0]: https://github.com/Spectating101/spk-derivatives/releases/tag/v0.2.0
[0.1.0]: https://github.com/Spectating101/spk-derivatives/releases/tag/v0.1.0
