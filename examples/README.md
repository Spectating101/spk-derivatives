# Presentation Materials

Professional-grade demos for presenting the energy derivatives framework.

## Contents

### 1. **PRESENTATION_NARRATIVE.ipynb** ⭐ (Start here!)
A polished, narrative-driven Jupyter notebook that tells the complete story:
- Energy → pricing theory → real implementation
- Load calibrated solar data → price option (2 methods) → calculate Greeks → compare locations
- Professional output, minimal code, maximum insight
- ~15 min to run end-to-end
- Perfect for live presentation or academic discussion

**Use this for:**
- Coursework submission
- Academic presentations
- Investor pitches
- Teaching quantitative finance

### 2. **presentation_live_demo.py** 🎯 (Interactive exploration)
An interactive Python script with 4 independent exploration modes:
- **Location Sensitivity**: Compare option prices across 10+ global locations
- **Greeks Curves**: Beautiful 2×3 subplot grid showing all 5 Greeks
- **Scenario Analysis**: What-if modeling (boom, disruption, crisis)
- **Convergence Validation**: Verify both pricing methods agree

**Use this for:**
- Live Q&A sessions
- Deep dives into specific aspects
- Risk management discussions
- Exploring different geographic regions

**Run:**
```bash
python presentation_live_demo.py
```

Then select demo 1-5 from the menu.

### 3. **presentation_colab.ipynb**
Extended version with additional validation steps and parameter transparency.

---

## Quick Start

**For a presentation (pick one):**

```bash
# Option A: Live notebook demo
jupyter notebook PRESENTATION_NARRATIVE.ipynb
# Run all cells, takes ~15 minutes

# Option B: Interactive Python script
python presentation_live_demo.py
# Choose exploration mode from menu
```

---

## Key Differences

| Feature | Narrative | Live Demo |
|---------|-----------|-----------|
| **Format** | Jupyter notebook | Python CLI/script |
| **Execution** | Sequential cells | Interactive menu |
| **Focus** | Story & conclusions | Exploration & details |
| **Audience** | Academic/investors | Technical/curious |
| **Time** | 15 min | Variable (5-30 min) |
| **Output** | Analysis + plots | Plots + comparison tables |

---

## What These Demonstrate

### Core Concepts
✅ Risk-neutral valuation (GBM)  
✅ Binomial tree pricing (exact)  
✅ Monte Carlo simulation (stochastic)  
✅ Greeks calculation (risk sensitivities)  
✅ Multi-location comparison  

### Business Insights
✅ Why energy volatility matters  
✅ How location affects option costs  
✅ Why stablecoins need reserves  
✅ Connection to CEIR theory  

### Technical Depth
✅ Model convergence & validation  
✅ Confidence intervals  
✅ Scenario stress testing  
✅ Risk management framework  

---

## For Questions

Both materials include:
- Clear variable names and explanations
- Inline comments on key calculations
- Interpretation of results ("what does this mean?")
- Practical implications

Ask during the demo—the framework is designed to be explainable.
