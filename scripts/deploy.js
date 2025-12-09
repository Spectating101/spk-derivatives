const hre = require("hardhat");

async function main() {
  console.log("🚀 Deploying SolarPunkCoin...");

  // Deploy contract
  const SolarPunkCoin = await hre.ethers.getContractFactory("SolarPunkCoin");
  const spk = await SolarPunkCoin.deploy();
  await spk.waitForDeployment();

  const contractAddress = await spk.getAddress();
  console.log("✅ SolarPunkCoin deployed to:", contractAddress);

  // Get deployer info
  const [deployer] = await hre.ethers.getSigners();
  console.log("📍 Deployed by:", deployer.address);

  // Initial configuration
  console.log("\n⚙️  Initializing contract...");

  // Log initial parameters
  const pegTarget = await spk.pegTarget();
  const pegBand = await spk.pegBand();
  const mintingFee = await spk.mintingFee();

  console.log("Initial Parameters:");
  console.log("  - Peg Target: $1.00 (1e18)");
  console.log("  - Peg Band: ±5% (5e16)");
  console.log("  - Minting Fee: 0.1% (1000 bps)");
  console.log("  - Supply Cap: 1,000,000,000 SPK");

  // Create verification info
  console.log("\n📋 Contract Information:");
  console.log("Name: SolarPunkCoin");
  console.log("Symbol: SPK");
  console.log("Decimals: 18");
  console.log("Network:", hre.network.name);

  console.log("\n✨ Deployment complete!");
  console.log(
    `Next steps: 
    1. Grant MINTER_ROLE to your minting service: 
       spk.grantRole(await spk.MINTER_ROLE(), minerAddress)
    2. Grant ORACLE_ROLE to your oracle service:
       spk.grantRole(await spk.ORACLE_ROLE(), oracleAddress)
    3. Test minting: spk.mintFromSurplus(1000, recipientAddress)
    4. Test peg control: spk.updateOraclePriceAndAdjust(price)
  `
  );

  // Return contract address for scripts
  return contractAddress;
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
