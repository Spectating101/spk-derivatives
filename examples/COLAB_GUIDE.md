# Running in Google Colab

If you want to run the presentation notebook in Google Colab, follow these steps:

## Quick Start

1. **Open Colab**:
   - Go to [colab.research.google.com](https://colab.research.google.com)
   - Click "Open notebook" → "GitHub"
   - Enter: `Spectating101/spk-derivatives`
   - Select `examples/PRESENTATION_NARRATIVE.ipynb`

2. **Run the notebook**:
   - Click the first code cell (Setup)
   - Press Ctrl+Enter (or click the play button)
   - Wait for installation (~30 seconds)
   - Then run the remaining cells in sequence

## What Happens

**Cell 1 (Setup)**:
- Detects that you're in Colab
- Installs `spk-derivatives` from GitHub
- Imports all required libraries
- Outputs: `✅ ENVIRONMENT READY`

**Remaining Cells**:
- Load solar data from NASA
- Price options using binomial tree and MC
- Calculate Greeks
- Compare locations
- Show convergence analysis

## Troubleshooting

### If installation hangs:
- Wait longer (first install can take 1-2 minutes)
- Check internet connection
- Try restarting the kernel (Runtime → Restart all)

### If imports fail:
- Run the setup cell again
- If still failing, clear the notebook cache:
  - Runtime → Restart all
  - Then run setup cell again

### If NASA data fails:
- The code has fallback to synthetic data
- Check your internet connection
- NASA API might be temporarily down (rare)

## Local Alternative

If you prefer running locally:

```bash
# Clone the repo
git clone https://github.com/Spectating101/spk-derivatives.git
cd spk-derivatives

# Install dependencies
pip install -r energy_derivatives/requirements.txt

# Run the notebook
jupyter notebook examples/PRESENTATION_NARRATIVE.ipynb
```

---

**Questions?** Check the notebook comments—they explain every step.
