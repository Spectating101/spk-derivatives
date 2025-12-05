# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0-research] - 2024-12-06

### Added

#### Core Functionality
- **Configurable volatility calculation** with three methods:
  - `log` (default): Industry-standard log returns
  - `pct_change`: Legacy percentage change method
  - `normalized`: Normalized by mean GHI
- **Optional volatility capping** instead of forced 200% cap
- **Metadata in parameter dictionary** including volatility method and cap information
- **Enhanced `load_solar_parameters()` API** with new parameters:
  - `volatility_method`: Choose calculation method
  - `volatility_cap`: Optional cap for numerical stability
  - `deseason`: Toggle deseasonalization

#### Package Infrastructure
- **setup.py**: Complete PyPI configuration
- **pyproject.toml**: Modern Python packaging with build system
- **LICENSE**: MIT License
- **MANIFEST.in**: Package data inclusion rules
- **CHANGELOG.md**: This changelog file

#### Documentation
- **VOLATILITY_ANALYSIS.md**: Comprehensive analysis of volatility calculation methods
- **READINESS_ASSESSMENT.md**: Production readiness evaluation
- **PUBLICATION_ROADMAP.md**: Phased publication strategy (research → production)
- **PRODUCTION_READINESS_REPORT.md**: Detailed technical assessment
- **FINAL_ANSWER.md**: Executive summary of production polish work
- **RESEARCH_USE_NOTICE.md**: Research software disclaimer and guidance
- **GEMINI_DISCUSSION_BRIEF.md**: Technical brief for AI/expert discussion
- **GEMINI_DISCUSSION_CHEATSHEET.md**: Quick reference guide

#### Quality Improvements
- **Comprehensive docstrings** for all volatility calculation functions
- **Type hints** for main volatility functions
- **Warning messages** when volatility is capped
- **Input validation** for method parameter

### Changed

#### Breaking Changes
- **`get_volatility_params()` signature changed**:
  - Old: `cap_volatility=2.0` (hardcoded)
  - New: `cap_volatility=None, method='log'` (configurable)
- **Default volatility method**: Changed from `pct_change` to `log` returns
- **Volatility cap**: Changed from forced to optional

#### Non-Breaking Changes
- **Taiwan volatility results** (uncapped):
  - Log returns: 740% (was: 913% with pct_change)
  - Percentage change: 913% (legacy, has artifacts)
  - Normalized: 571% (alternative)
- **Improved error messages** in data loading functions
- **Updated documentation** throughout codebase

### Fixed

- **Volatility calculation artifacts**: Log returns eliminate small-denominator issues in `pct_change()` method
- **Hardcoded cap transparency**: Users now explicitly choose whether to cap
- **Missing package structure**: Now pip-installable from Git

### Deprecated

- **`pct_change` method**: Still available but not recommended due to artifacts

### Technical Details

**Volatility Calculation Fix:**
```python
# BEFORE (v0.1.0):
df['Returns'] = df['GHI_Deseason'].pct_change()
annual_vol = daily_vol * np.sqrt(365)
if annual_vol > 2.0:  # Hardcoded cap
    annual_vol = 2.0

# AFTER (v0.2.0):
if method == 'log':  # New default
    df['Returns'] = np.log(source_data / source_data.shift(1))
elif method == 'pct_change':  # Legacy
    df['Returns'] = source_data.pct_change()
annual_vol = daily_vol * np.sqrt(365)
if cap_volatility is not None and annual_vol > cap_volatility:
    warnings.warn(f"Capping volatility at {cap_volatility:.1%}")
    annual_vol = cap_volatility
```

**Package Installation:**
```bash
# New in v0.2.0:
pip install git+https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git@v0.2.0-research

# Development installation:
pip install -e ".[viz,dev]"
```

### Migration Guide (v0.1.0 → v0.2.0)

**If you want the same behavior as v0.1.0:**
```python
# Old behavior (v0.1.0):
params = load_solar_parameters()

# Equivalent in v0.2.0:
params = load_solar_parameters(
    volatility_method='pct_change',
    volatility_cap=2.0
)
```

**Recommended for new code (v0.2.0):**
```python
# Use log returns (industry standard):
params = load_solar_parameters(
    volatility_method='log',
    volatility_cap=None  # or 2.0 for stability
)
```

### Known Issues

- Multi-location validation pending (only Taiwan tested)
- Command-line interface structure exists but not fully implemented
- Production error handling needs enhancement
- Logging uses print() instead of proper logging framework

### Validation

- ✅ All 8 unit tests passing
- ✅ Convergence validation: 1.3% difference (binomial vs Monte Carlo)
- ✅ Stable at 200% volatility
- ✅ pip installation works from Git
- ⏳ Multi-location testing pending
- ⏳ Cross-platform testing pending
- ⏳ Peer review pending

---

## [0.1.0] - 2024-11-XX

### Added

#### Core Features
- **NASA POWER API integration** (`data_loader_nasa.py`)
  - Fetch solar irradiance data for any location
  - Automatic deseasonalization
  - Volatility calculation
  - 30-day rolling mean for trend removal
- **Solar convergence demo** (`solar_convergence_demo.py`)
  - Binomial vs Monte-Carlo comparison
  - Convergence plot generation
  - Publication-quality visualizations
- **Bitcoin CEIR data integration** (`data_loader.py`)
  - Historical price and energy consumption
  - CEIR calculation
  - Volatility estimation

#### Pricing Models
- **Binomial tree pricing** (`binomial.py`)
  - Cox-Ross-Rubinstein model
  - European call and redeemable options
  - Configurable steps (N)
- **Monte Carlo simulation** (`monte_carlo.py`)
  - Geometric Brownian Motion
  - Configurable paths and seeds
  - Confidence interval estimation
- **Greeks calculation** (`sensitivities.py`)
  - Delta, Gamma, Theta, Vega, Rho
  - Numerical differentiation
  - Risk management metrics

#### Documentation
- **README.md**: Comprehensive project documentation
- **API_REFERENCE.md**: Complete API documentation
- **COURSEWORK_GUIDE.md**: Assignment deliverables guide
- **NASA_INTEGRATION_COMPLETE.md**: Integration summary
- **PRESENTATION_GUIDE_TUESDAY.md**: Presentation guide

#### Testing
- **8 unit tests** covering core functionality
- **Integration test** (solar convergence demo)
- **Test data** fixtures

#### Infrastructure
- **requirements.txt**: Python dependencies
- **Jupyter notebook**: Interactive demonstrations
- **Data caching**: NASA API response caching

### Technical Details

**Data Sources:**
- NASA POWER API: ALLSKY_SFC_SW_DWN (Global Horizontal Irradiance)
- Location: Taoyuan, Taiwan (24.99°N, 121.30°E)
- Time period: 2020-01-01 to 2024+
- Resolution: Daily

**Pricing Results (Taiwan):**
- Spot price: $0.0516/kWh
- Volatility: 200% (capped, deseasoned)
- Risk-free rate: 5%
- Maturity: 1 year
- Call option price (binomial): $0.035645
- Call option price (Monte Carlo): $0.034754
- Convergence error: 2.5%

**Greeks (example):**
- Delta: 0.634 (63.4% hedge ratio)
- Gamma: 4.357 (exposure to price changes)
- Theta: -0.000131 (time decay per day)
- Vega: 0.0339 (volatility sensitivity)
- Rho: 0.0143 (rate sensitivity)

### Known Limitations

- Volatility calculation uses `pct_change()` (can create artifacts)
- Volatility hardcoded at 200% cap
- Single location validation (Taiwan)
- No package structure (manual installation)
- No license file
- Print-based logging

---

## [Unreleased]

### Planned for v1.0.0 (Production Release)

- Command-line interface (CLI)
- Configuration file support (YAML/TOML)
- Production error handling with custom exceptions
- Comprehensive logging framework
- Multi-location validation
- Cross-platform testing (Windows, macOS, Linux)
- Python version testing (3.8-3.12)
- Performance optimizations
- API rate limiting for NASA requests
- Caching improvements
- CONTRIBUTING.md
- Code of Conduct
- Security policy
- Peer review validation

### Future Enhancements (v2.0.0+)

- American options pricing
- Exotic derivatives (Asian, Barrier, etc.)
- Stochastic volatility models (Heston)
- Jump-diffusion models (Merton)
- Real options analysis
- Portfolio optimization
- Risk analytics dashboard
- Database integration
- REST API for pricing services
- WebSocket for live updates
- Multi-asset correlation
- Seasonal volatility modeling

---

## Release Notes

### v0.2.0-research

**Status:** Research-Ready ✅
**Target Audience:** Academic researchers, students, quantitative analysts
**Installation:** `pip install git+https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git@v0.2.0-research`

**Key Improvements:**
1. **Fixed volatility calculation** - Industry-standard log returns
2. **Made methodology configurable** - Users choose method and cap
3. **Added package structure** - Proper pip installation
4. **Comprehensive documentation** - Ready for research publication

**Not Suitable For:**
- Production financial systems
- Real money trading
- Commercial deployment without validation

**Next Steps:**
- Paper submission
- Zenodo DOI
- Peer review
- Multi-location validation

### v0.1.0

**Status:** Proof-of-Concept ✅
**Target Audience:** Coursework, initial demonstration
**Key Achievement:** Demonstrated NASA data integration and convergence validation

---

## Links

- **Repository:** https://github.com/YOUR_USERNAME/solarpunk-bitcoin
- **Issues:** https://github.com/YOUR_USERNAME/solarpunk-bitcoin/issues
- **Documentation:** See `energy_derivatives/docs/`
- **License:** MIT (see LICENSE file)

---

**Maintained by:** Solarpunk Bitcoin Team
**Last Updated:** December 6, 2024
