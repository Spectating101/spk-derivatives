# SolarPunkCoin MVP

**Energy-backed stablecoin smart contract on Polygon (EVM).**

A working proof-of-concept for an institutional-grade cryptocurrency anchored to renewable energy surplus, implementing PI-control-based peg stabilization and oracle-gated minting.

## What's Included

```
.
├── contracts/SolarPunkCoin.sol       # Main ERC-20 stablecoin contract (400 lines)
├── test/SolarPunkCoin.test.js        # 32 unit tests (all passing)
├── scripts/
│   ├── deploy.js                     # Automated deployment to Polygon Mumbai
│   └── simulate_peg.py               # 1000-day peg stabilization simulation
├── hardhat.config.js                 # Hardhat setup (Solidity 0.8.20)
├── package.json                      # Node.js dependencies
│
├── RESEARCH/                         # Research papers (background)
│   ├── CEIR-Trifecta.md
│   ├── Final-Iteration.md
│   ├── Quasi-SD-CEIR.md
│   └── Empirical-Milestone.md
│
└── docs/                             # Essential documentation
    ├── README.md (this file)
    ├── SOLIDITY_QUICKSTART.md        # How to test/deploy
    ├── MVP_SUMMARY.md                # 1-page grant summary
    ├── POLYGON_ARCHITECTURE_EXPLAINED.md
    └── REPO_STRUCTURE.md
```

## Key Features

### ✅ Rule A: Surplus-Only Minting
- Oracle-gated: Only mint when backed by verified renewable surplus (kWh)
- Fee-based: 0.1% minting fee (seigniorage)
- Access-controlled: Only MINTER role can call

### ✅ Rule B: Intrinsic Redemption
- Holders burn SPK → receive utility credits (kWh equivalent)
- 0.2% redemption fee
- Guarantees minimum intrinsic value

### ✅ Rule D: PI Control Peg Stabilization
- **Proportional term:** Immediate response to price deviation from $1.00 peg
- **Integral term:** Corrects steady-state error over time
- **Conservative limits:** Max 1% supply adjustment per call (safety first)
- Mint/burn only when needed to push price toward target

### ✅ Rule E: Grid Stress Safeguard
- Oracle can pause minting if grid is unstable
- Emergency pause/unpause by PAUSER role
- Prevents destabilizing minting during peak demand

## Is This Real Blockchain?

**YES, 100% real Ethereum/Polygon code:**

- ✅ **Solidity 0.8.20** – Actual smart contract language (compiles to EVM bytecode)
- ✅ **OpenZeppelin** – Battle-tested libraries (ERC-20, AccessControl, Pausable)
- ✅ **ethers.js** – Real blockchain interaction library
- ✅ **Hardhat** – Industry-standard Ethereum development environment
- ✅ **32 passing unit tests** – Contract logic verified locally

**Status:**
- ✅ Compiled successfully
- ✅ All tests pass locally
- ⏳ Draft/MVP (not mainnet—testnet ready)
- ⏳ Not published (easily modifiable)
- ⏳ No real $ at stake (local testing only)

## Getting Started

### Prerequisites
```bash
node --version  # v18+
npm --version   # v9+
```

### Install & Test
```bash
# Install dependencies
npm install --legacy-peer-deps

# Compile smart contract
npx hardhat compile

# Run 32 unit tests
npx hardhat test
```

**Expected output:**
```
  32 passing (1.0s)
```

### Deploy to Polygon Mumbai Testnet

1. **Get test MATIC**
   ```bash
   # Visit: https://faucet.polygon.technology/
   # Paste your wallet address, claim free test tokens
   ```

2. **Create `.env` from template**
   ```bash
   cp .env.example .env
   # Edit .env: add your private key
   ```

3. **Deploy**
   ```bash
   npx hardhat run scripts/deploy.js --network mumbai
   ```

   Output will show your live contract address.

### Run Simulation

```bash
# Python 3.8+, with dependencies
python scripts/simulate_peg.py

# Generates:
# - spk_simulation.png (6-panel analysis chart)
# - spk_simulation_results.csv (day-by-day metrics)
```

## Architecture

### Contract Design
- **Standard:** ERC-20 + OpenZeppelin extensions
- **Roles:** MINTER (mint from surplus), ORACLE (update price), PAUSER (emergency)
- **Parameters:** Tunable peg control gains (proportional/integral)
- **Gas costs:** 45–95K per function call (reasonable for Polygon)

### Peg Control Algorithm
```
1. Oracle submits current price P
2. Calculate deviation: delta = (P - $1.00) / $1.00
3. Proportional action: proportional_adjustment = -1% × delta
4. Integral action: integral_adjustment = -0.5% × accumulated_error
5. Total adjustment: clamped to ±1% of supply per call
6. If adjustment > 0: mint new SPK (increase supply → push price down)
7. If adjustment < 0: burn SPK (decrease supply → push price up)
```

### Safety Features
- ✅ Supply cap: 1 billion SPK max
- ✅ Balance checks before burns
- ✅ Oracle staleness checks (8 hours default)
- ✅ Emergency pause mechanism
- ✅ Fee collection for governance/reserve
- ✅ Whitelist-ready for DAO upgrade

## Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Deployment | 2 | ✅ |
| Minting (Rule A) | 5 | ✅ |
| Peg Stabilization (Rule D) | 5 | ✅ |
| Redemption (Rule B) | 4 | ✅ |
| Grid Safety (Rule E) | 3 | ✅ |
| Parameters | 4 | ✅ |
| View Functions | 3 | ✅ |
| Emergency | 3 | ✅ |
| Integration | 2 | ✅ |
| **TOTAL** | **32** | **✅** |

## Next Steps

### MVP Phase (This Week)
- [ ] Deploy to Mumbai testnet
- [ ] Get contract address from PolygonScan
- [ ] Test live minting/redemption
- [ ] Apply to Gitcoin/Polygon grants

### v1.0 Phase (If Funded)
- [ ] Integrate real oracle (Chainlink)
- [ ] Connect CAISO/Taipower data
- [ ] Add USDC reserve backing
- [ ] DAO governance setup
- [ ] Security audit

### Production (Before Mainnet)
- [ ] Full security audit ($50–100K)
- [ ] Legal review
- [ ] Liquidity providers onboarding
- [ ] Insurance coverage

## Documentation

- **SOLIDITY_QUICKSTART.md** – How to test, deploy, modify contract
- **MVP_SUMMARY.md** – 1-page grant application template
- **POLYGON_ARCHITECTURE_EXPLAINED.md** – Why Polygon vs custom chain
- **REPO_STRUCTURE.md** – File organization guide

## Research Background

The SolarPunkCoin MVP is based on 18+ months of research into energy-backed cryptocurrencies:

- **CEIR-Trifecta.md** – Empirical study: Does energy cost anchor crypto value?
- **Final-Iteration.md** – Design document: 10 institutional rules (A–J)
- **Quasi-SD-CEIR.md** – Supply-demand + sentiment framework
- **Empirical-Milestone.md** – Spring 2025 research proposal

See `RESEARCH/` folder for full papers.

## License

MIT (see LICENSE file)

## Questions?

This is a **draft MVP**. All code is:
- ✅ Real blockchain code (Solidity + ethers.js)
- ✅ Tested locally (32/32 passing)
- ✅ Safe for experimentation (testnet only)
- ⏳ Ready for community feedback

Not for production use without security audit.
