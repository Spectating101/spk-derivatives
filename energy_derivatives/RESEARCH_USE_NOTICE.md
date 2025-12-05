# ⚠️ Research Software Notice

**Version:** 0.2.0-research
**Status:** Research-Grade Software for Academic Use
**Last Updated:** December 6, 2024

---

## Purpose and Scope

This software is **research-grade** and designed for:

✅ **Validated Use Cases:**
- Academic research and publications
- Educational purposes and coursework
- Methodology validation and comparison
- Proof-of-concept demonstrations
- Technical portfolio presentations
- Open-source collaboration and review

❌ **Not Validated For:**
- Production financial systems
- Real money trading or derivatives contracts
- Commercial deployment without additional validation
- Regulatory compliance requirements
- Mission-critical applications

---

## Installation

### Research Installation (Recommended)

Install the specific research release:

```bash
pip install git+https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git@v0.2.0-research
```

### Development Installation

For local development and experimentation:

```bash
git clone https://github.com/YOUR_USERNAME/solarpunk-bitcoin.git
cd solarpunk-bitcoin
pip install -e ".[viz,dev]"
```

---

## Known Limitations

### 1. Volatility Calculation

**Current Implementation:**
- Default method: Log returns (industry standard)
- Taiwan result: 740% annualized volatility
- Optional cap: 200% for numerical stability

**Context:**
- Raw calculation is 740% using log returns for Taiwan's monsoon climate
- Real solar farm revenue volatility: 40-60% (due to contracts, storage, diversification)
- Framework validated at extreme values (200%+), suitable for realistic applications

**Methodology:**
See `VOLATILITY_ANALYSIS.md` for complete explanation of:
- Three calculation methods (log, pct_change, normalized)
- Physical vs economic volatility distinction
- Taiwan's extreme climate characteristics

### 2. Geographic Validation

**Current Status:**
- ✅ Validated: Taiwan (24.99°N, 121.30°E)
- ⏳ Pending: Multi-location validation (Arizona, Spain, Germany)
- ⏳ Pending: Cross-climate regime testing

**Recommendation:**
Users applying this to other locations should:
1. Validate results against local solar irradiance characteristics
2. Compare with regional meteorological data
3. Adjust volatility methodology if needed

### 3. Model Assumptions

**Black-Scholes Framework Assumptions:**
- Continuous trading (not realistic for physical energy)
- Constant volatility (actual solar volatility varies seasonally)
- Log-normal price distribution (physical constraint: irradiance ≥ 0)
- No transaction costs
- Risk-free rate constant

**Real-World Considerations:**
- Energy cannot be stored costlessly (storage degrades, has costs)
- Actual energy contracts have delivery constraints
- Market liquidity may be limited
- Basis risk between irradiance and revenue

### 4. Peer Review Status

**Current:**
- ⏳ Peer review pending
- ⏳ Conference submission planned
- ✅ Open source review ongoing

**Updates:**
- Check repository for peer review outcomes
- Watch for published paper citations

---

## What IS Validated

Despite being research-grade, this software demonstrates:

✅ **Methodological Rigor:**
- Industry-standard volatility calculation (log returns)
- Cox-Ross-Rubinstein binomial model implementation
- Monte Carlo simulation for validation
- Greeks calculation (delta, gamma, theta, vega, rho)

✅ **Numerical Accuracy:**
- Convergence validation: 1.3% difference (binomial vs Monte Carlo)
- Stable at extreme volatility (200%+)
- Test suite: 8/8 passing

✅ **Data Quality:**
- Real NASA POWER satellite data (ALLSKY_SFC_SW_DWN)
- 5+ years historical data (2020-2024+)
- Daily resolution, global coverage
- Proper deseasonalization methodology

✅ **Software Engineering:**
- Full package structure (setup.py, pyproject.toml)
- MIT licensed
- Comprehensive documentation
- API reference complete
- Version controlled

---

## Citation

If you use this software in academic work, please cite:

```bibtex
@software{solar_quant_2024,
  author = {Solarpunk Bitcoin Team},
  title = {Solar Quant: Quantitative Pricing Framework for Solar Energy Derivatives},
  year = {2024},
  url = {https://github.com/YOUR_USERNAME/solarpunk-bitcoin},
  version = {0.2.0-research},
  note = {Research-grade software for academic use}
}
```

**DOI:** (Pending Zenodo registration)

---

## Disclaimer

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

**Financial Disclaimer:**
This software is for research and educational purposes only. It is NOT financial advice. Do not use for actual trading or financial decisions without:
- Independent validation
- Professional financial advice
- Regulatory compliance review
- Risk management assessment

**No Investment Advice:**
Nothing in this software constitutes investment advice, financial advice, trading advice, or any other sort of advice. Users are solely responsible for their own investment decisions.

---

## Support and Contribution

**Bug Reports:**
- Report issues at: https://github.com/YOUR_USERNAME/solarpunk-bitcoin/issues
- Include: Python version, OS, minimal reproducible example

**Contributions:**
- Pull requests welcome
- See CONTRIBUTING.md (when available)
- Discuss major changes in issues first

**Questions:**
- Open GitHub Discussions for methodology questions
- Check docs/ folder for detailed explanations
- Review examples in notebooks/

---

## Roadmap to Production

This research release (v0.2.0) is on track for production release. See `PUBLICATION_ROADMAP.md` for:

**Research → Production Timeline:**
- ✅ **Phase 1** (Week 1): Research release
- ⏳ **Phase 2** (Months 2-3): Paper submission
- ⏳ **Phase 3** (Months 4-6): Community feedback
- ⏳ **Phase 4** (Months 7-9): Production hardening
- ⏳ **Phase 5** (Months 10-12): PyPI v1.0.0 release

**What Production Release Will Add:**
- Command-line interface (CLI)
- Configuration file support (YAML/TOML)
- Production error handling
- Comprehensive logging
- Multi-location validation
- Cross-platform testing (Windows, macOS, Linux)
- Python version testing (3.8-3.12)
- Peer review validation
- Support policy and SLAs

---

## Version History

**v0.2.0-research** (December 2024)
- Production-polished code quality
- Fixed volatility calculation (log returns default)
- Configurable methodology
- Full package structure
- MIT licensed
- Research-ready

**v0.1.0** (November 2024)
- Initial NASA integration
- Bitcoin CEIR data integration
- Basic derivatives pricing
- Coursework deliverables

---

## Contact

For research collaborations, methodology questions, or academic use:
- **Repository:** https://github.com/YOUR_USERNAME/solarpunk-bitcoin
- **Issues:** https://github.com/YOUR_USERNAME/solarpunk-bitcoin/issues
- **Email:** contact@solarpunk.example.com

---

**Last Updated:** December 6, 2024
**Release:** v0.2.0-research
**License:** MIT
**Status:** Research-Ready ✅
