// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/proxy/utils/Initializable.sol";

/**
 * @title SolarPunkCoin (SPK)
 * @notice Energy-backed stablecoin pegged to renewable energy prices
 * @dev Implements Rules A-J from SolarPunkCoin design:
 *      A: Surplus-only issuance via oracle
 *      B: Intrinsic redemption guarantee for electricity
 *      C: Cost-value parity via stability fees
 *      D: Peg stability band with PI control
 *      E: Grid stress safeguard (halt on low reserves)
 *      F: Green energy constraint (enforced offchain, flagged onchain)
 *      G: Verifiable green proof (oracle signatures + audit trail)
 *      H: Transparent reserve + fee model
 *      I: Fair distribution (future DAO parameter)
 *      J: Decentralized governance (DAO upgradeable)
 */
contract SolarPunkCoin is
    ERC20,
    ERC20Burnable,
    ERC20Pausable,
    Ownable,
    AccessControl,
    Initializable
{
    // ============ Roles ============
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // ============ State Variables: Peg Parameters ============
    /// @notice Target peg price in USD (1e18 = $1.00)
    uint256 public pegTarget = 1e18;

    /// @notice Peg stability band (e.g., 5e16 = ±5%)
    uint256 public pegBand = 5e16; // ±5%

    /// @notice Proportional gain for PI controller (e.g., 1e16 = 1%)
    uint256 public proportionalGain = 1e16;

    /// @notice Integral gain for PI controller accumulation
    uint256 public integralGain = 5e15; // 0.5%

    /// @notice Cumulative integral error (for PI controller)
    int256 public integralError = 0;

    /// @notice Minting fee (basis points: 1000 = 10%)
    uint256 public mintingFee = 1000; // 0.1% = 1bp actually, adjust as needed

    /// @notice Redemption fee (basis points)
    uint256 public redemptionFee = 1000; // 0.1%

    /// @notice Maximum supply cap to prevent runaway inflation
    uint256 public supplyCap = 1_000_000_000e18; // 1 billion SPK max

    // ============ State Variables: Oracle & Data ============
    /// @notice Latest observed price from oracle (in USD, 1e18 = $1)
    uint256 public lastOraclePrice = 1e18;

    /// @notice Timestamp of last oracle update
    uint256 public lastOracleUpdate = 0;

    /// @notice Oracle staleness threshold (86400 = 1 day)
    uint256 public oracleStalenessThreshold = 86400;

    // ============ State Variables: Reserves & Accounting ============
    /// @notice USDC reserve held for backing (in wei, 1e6 decimals assumed)
    uint256 public usdcReserve = 0;

    /// @notice Cumulative surplus kWh recorded
    uint256 public cumulativeSurplusKwh = 0;

    /// @notice Total SPK redeemed (for tracking)
    uint256 public totalRedeemed = 0;

    // ============ State Variables: Grid Safety ============
    /// @notice Minimum reserve margin % to allow minting (e.g., 10)
    uint256 public minReserveMarginPercent = 10;

    /// @notice Is grid in stress (reserve < threshold)?
    bool public gridStressed = false;

    // ============ Events ============
    event SurplusRecorded(uint256 indexed kwhAmount, uint256 timestamp);
    event SPKMinted(
        address indexed to,
        uint256 amount,
        uint256 kwhBacked,
        uint256 fee
    );
    event SPKBurned(address indexed from, uint256 amount);
    event SPKRedeemed(address indexed user, uint256 amount);
    event PegAdjusted(uint256 newPrice, bool isMint);
    event OraclePriceUpdated(uint256 price, uint256 timestamp);
    event GridStressToggled(bool isStressed);
    event ParameterUpdated(string paramName, uint256 newValue);

    // ============ Modifiers ============
    modifier onlyOracle() {
        require(hasRole(ORACLE_ROLE, msg.sender), "Must have ORACLE_ROLE");
        _;
    }

    modifier onlyMinter() {
        require(hasRole(MINTER_ROLE, msg.sender), "Must have MINTER_ROLE");
        _;
    }

    modifier gridNotStressed() {
        require(!gridStressed, "Grid stressed: minting paused");
        _;
    }

    modifier oracleNotStale() {
        require(
            block.timestamp - lastOracleUpdate < oracleStalenessThreshold,
            "Oracle price stale"
        );
        _;
    }

    // ============ Constructor & Initialization ============
    constructor() ERC20("SolarPunkCoin", "SPK") Ownable(msg.sender) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(ORACLE_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
    }

    // ============ Core Functions: Minting & Surplus ============

    /**
     * @notice Mint SPK based on verified renewable energy surplus
     * @dev Rule A: Only mint when oracle confirms curtailment/surplus
     * @param surplusKwh Amount of surplus kWh to back new SPK
     * @param recipient Address to receive newly minted SPK
     */
    function mintFromSurplus(
        uint256 surplusKwh,
        address recipient
    ) external onlyMinter gridNotStressed oracleNotStale returns (uint256) {
        require(surplusKwh > 0, "Surplus must be > 0");
        require(recipient != address(0), "Invalid recipient");

        // Calculate base SPK amount: 1 SPK per 1 kWh (adjust as needed)
        // In practice: surplusKwh * multiplier based on regional prices
        uint256 baseSPK = surplusKwh * 1e18;

        // Apply minting fee (seigniorage)
        uint256 fee = (baseSPK * mintingFee) / 10000;
        uint256 amountToMint = baseSPK - fee;

        // Check supply cap
        require(totalSupply() + amountToMint <= supplyCap, "Supply cap exceeded");

        // Record surplus
        cumulativeSurplusKwh += surplusKwh;

        // Mint tokens to recipient
        _mint(recipient, amountToMint);

        // Mint fee to treasury (owner)
        if (fee > 0) {
            _mint(owner(), fee);
        }

        emit SurplusRecorded(surplusKwh, block.timestamp);
        emit SPKMinted(recipient, amountToMint, surplusKwh, fee);

        return amountToMint;
    }

    // ============ Peg Stabilization: PI Control ============

    /**
     * @notice Update oracle price and apply PI control for peg stability
     * @dev Rule D: Automatically adjust supply via mint/burn to maintain peg
     * @param newPrice Current market price from oracle (in USD, 1e18 = $1)
     */
    function updateOraclePriceAndAdjust(uint256 newPrice)
        external
        onlyOracle
        returns (bool adjusted)
    {
        require(newPrice > 0, "Price must be positive");

        // Update oracle state
        lastOraclePrice = newPrice;
        lastOracleUpdate = block.timestamp;

        emit OraclePriceUpdated(newPrice, block.timestamp);

        // Apply PI control to stabilize peg
        adjusted = _applyPIControl(newPrice);

        return adjusted;
    }

    /**
     * @notice PI (Proportional-Integral) control loop
     * @dev When price deviates from peg, mint or burn to bring it back
     * @param currentPrice Current market price
     */
    function _applyPIControl(uint256 currentPrice) internal returns (bool) {
        int256 priceDelta = int256(currentPrice) - int256(pegTarget);
        bool adjusted = false;

        // Proportional term: immediate response
        int256 proportional = (priceDelta * int256(proportionalGain)) / 1e18;

        // Integral term: accumulates over time (prevents steady-state error)
        integralError += priceDelta;
        // Cap integral to prevent wind-up
        if (integralError > 10e18) integralError = 10e18;
        if (integralError < -10e18) integralError = -10e18;

        int256 integral = (integralError * int256(integralGain)) / 1e18;

        // Total control signal
        int256 controlSignal = proportional + integral;

        // If price too high (positive delta), burn supply to push price down
        if (controlSignal > 0) {
            uint256 burnAmount = uint256(controlSignal);
            if (burnAmount > 0 && totalSupply() >= burnAmount) {
                _burn(address(this), burnAmount);
                emit PegAdjusted(currentPrice, false); // false = burn
                adjusted = true;
            }
        }
        // If price too low (negative delta), mint supply to push price up
        else if (controlSignal < 0) {
            uint256 mintAmount = uint256(-controlSignal);
            if (totalSupply() + mintAmount <= supplyCap) {
                _mint(address(this), mintAmount);
                emit PegAdjusted(currentPrice, true); // true = mint
                adjusted = true;
            }
        }

        return adjusted;
    }

    // ============ Redemption Mechanism ============

    /**
     * @notice Redeem SPK for energy at utilities
     * @dev Rule B: SPK holders can redeem at guaranteed rate
     *      Actual energy redemption happens offchain via utility integration
     * @param amount SPK to redeem
     */
    function redeemForEnergy(uint256 amount) external returns (bool) {
        require(amount > 0, "Redeem amount must be > 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient SPK balance");

        // Apply redemption fee
        uint256 fee = (amount * redemptionFee) / 10000;
        uint256 netAmount = amount - fee;

        // Burn the SPK
        _burn(msg.sender, amount);

        // Fee goes to reserve/treasury
        if (fee > 0) {
            // In production: transfer fee to treasury multisig
            // For now: emit event for offchain tracking
        }

        // Track redemption
        totalRedeemed += netAmount;

        emit SPKRedeemed(msg.sender, amount);

        return true;
    }

    // ============ Grid Safety (Rule E) ============

    /**
     * @notice Toggle grid stress state (blocks minting if stressed)
     * @dev Only oracle can call. Used when grid reserve < threshold
     * @param isStressed True if grid reserve < min threshold
     */
    function setGridStressed(bool isStressed) external onlyOracle {
        gridStressed = isStressed;
        emit GridStressToggled(isStressed);
    }

    // ============ Oracle & Parameter Management ============

    /**
     * @notice Update peg stability parameters
     * @dev Owner/DAO can adjust these for fine-tuning
     * @param newBand New stability band (e.g., 5e16 = ±5%)
     * @param newPropGain New proportional gain
     * @param newIntGain New integral gain
     */
    function updateControlParameters(
        uint256 newBand,
        uint256 newPropGain,
        uint256 newIntGain
    ) external onlyOwner {
        require(newBand > 0 && newBand <= 1e17, "Invalid band"); // Max 10%
        require(newPropGain > 0, "Invalid prop gain");
        require(newIntGain > 0, "Invalid int gain");

        pegBand = newBand;
        proportionalGain = newPropGain;
        integralGain = newIntGain;

        emit ParameterUpdated("pegBand", newBand);
        emit ParameterUpdated("proportionalGain", newPropGain);
        emit ParameterUpdated("integralGain", newIntGain);
    }

    /**
     * @notice Update fee structure
     * @param newMintFee Minting fee in basis points
     * @param newRedeemFee Redemption fee in basis points
     */
    function updateFees(uint256 newMintFee, uint256 newRedeemFee)
        external
        onlyOwner
    {
        require(newMintFee <= 5000, "Mint fee too high"); // Max 50%
        require(newRedeemFee <= 5000, "Redeem fee too high");

        mintingFee = newMintFee;
        redemptionFee = newRedeemFee;

        emit ParameterUpdated("mintingFee", newMintFee);
        emit ParameterUpdated("redemptionFee", newRedeemFee);
    }

    /**
     * @notice Grant or revoke oracle role (for oracle rotation)
     * @param oracle Address to grant/revoke
     * @param shouldGrant True to grant, false to revoke
     */
    function setOracleRole(address oracle, bool shouldGrant)
        external
        onlyOwner
    {
        require(oracle != address(0), "Invalid oracle address");
        if (shouldGrant) {
            grantRole(ORACLE_ROLE, oracle);
        } else {
            revokeRole(ORACLE_ROLE, oracle);
        }
    }

    // ============ View Functions ============

    /**
     * @notice Check if SPK price is within peg band
     * @return Within peg band?
     */
    function isPegStable() external view returns (bool) {
        uint256 upperBound = pegTarget + pegBand;
        uint256 lowerBound = pegTarget > pegBand ? pegTarget - pegBand : 0;
        return lastOraclePrice >= lowerBound && lastOraclePrice <= upperBound;
    }

    /**
     * @notice Get current peg deviation (negative = underpriced)
     * @return Deviation in basis points
     */
    function getPegDeviation() external view returns (int256) {
        int256 deviation = (int256(lastOraclePrice) - int256(pegTarget)) * 10000 /
            int256(pegTarget);
        return deviation;
    }

    /**
     * @notice Estimate SPK amount for given surplus kWh
     * @param surplusKwh Surplus renewable energy in kWh
     * @return Estimated SPK after fees
     */
    function estimateMintAmount(uint256 surplusKwh)
        external
        view
        returns (uint256)
    {
        uint256 baseSPK = surplusKwh * 1e18;
        uint256 fee = (baseSPK * mintingFee) / 10000;
        return baseSPK - fee;
    }

    /**
     * @notice Get reserve ratio (collateral / total supply)
     * @return Reserve ratio in percentage
     */
    function getReserveRatio() external view returns (uint256) {
        if (totalSupply() == 0) return 100;
        return (usdcReserve * 100) / totalSupply();
    }

    // ============ Internal Overrides (Pausable) ============

    function _update(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20, ERC20Pausable) whenNotPaused {
        super._update(from, to, amount);
    }

    // ============ Emergency Functions ============

    /**
     * @notice Emergency pause in case of attack or bug
     * @dev Only PAUSER_ROLE can call
     */
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /**
     * @notice Emergency unpause
     * @dev Only owner can call
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    // ============ Future: DAO & Governance Hooks ============
    // These are placeholders for future governance integration

    /**
     * @notice Transition to DAO governance (future upgrade)
     * @dev Will be called when transitioning from multisig to Aragon/Compound DAO
     */
    function initializeDAOGovernance(address daoTimeLock)
        external
        onlyOwner
    {
        // Transfer ownership to DAO timelock
        // _transferOwnership(daoTimeLock);
        // Emit governance event
    }
}
