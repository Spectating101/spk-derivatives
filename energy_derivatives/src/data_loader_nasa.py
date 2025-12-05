"""
NASA POWER API Data Loader for Solar Energy Derivatives
=========================================================

Fetches real-world Global Horizontal Irradiance (GHI) data from NASA POWER API
to calibrate volatility parameters for solar energy derivatives pricing.

Location: Taoyuan, Taiwan (24.99°N, 121.30°E)
Data Source: NASA POWER (Prediction Of Worldwide Energy Resources)
Parameter: ALLSKY_SFC_SW_DWN (Solar Irradiance in kW-hr/m²/day)

Key Functions:
-----------
fetch_nasa_data(): Fetch historical GHI data from NASA API
get_volatility_params(): Calculate annualized volatility from solar data
load_solar_parameters(): Load complete parameters for solar derivative pricing
"""

import requests
import pandas as pd
import numpy as np
import warnings
from typing import Dict, Tuple, Optional
from pathlib import Path

# --- CONFIGURATION ---
# Coordinates for Taoyuan, Taiwan
LAT = 24.99
LON = 121.30
START_YEAR = 2020
END_YEAR = 2024


def fetch_nasa_data(
    lat: float = LAT,
    lon: float = LON,
    start: int = START_YEAR,
    end: int = END_YEAR,
    cache: bool = True
) -> pd.DataFrame:
    """
    Fetches Daily Global Horizontal Irradiance (GHI) from NASA POWER API.

    Parameters
    ----------
    lat : float
        Latitude (default: 24.99 for Taoyuan)
    lon : float
        Longitude (default: 121.30 for Taoyuan)
    start : int
        Start year (default: 2020)
    end : int
        End year (default: 2024)
    cache : bool
        If True, cache data locally to avoid repeated API calls

    Returns
    -------
    pd.DataFrame
        DataFrame with Date index and GHI column (kW-hr/m²/day)
    """

    # Check cache first
    cache_dir = Path(__file__).parent.parent / 'data'
    cache_file = cache_dir / f'nasa_ghi_{lat}_{lon}_{start}_{end}.csv'

    if cache and cache_file.exists():
        print(f"📁 Loading cached NASA data from {cache_file}")
        df = pd.read_csv(cache_file, parse_dates=['Date'], index_col='Date')
        print(f"✅ Loaded {len(df)} days of cached data")
        return df

    # Fetch from NASA API
    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN",  # Solar Irradiance (kW-hr/m²/day)
        "community": "RE",                   # Renewable Energy
        "longitude": lon,
        "latitude": lat,
        "start": f"{start}0101",
        "end": f"{end}1231",
        "format": "JSON"
    }

    print(f"📡 Connecting to NASA Satellite Database for Taoyuan ({lat}, {lon})...")
    print(f"   Date Range: {start}-01-01 to {end}-12-31")

    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"NASA API Failed: {e}")

    data = response.json()

    # Parse JSON into DataFrame
    try:
        solar_dict = data['properties']['parameter']['ALLSKY_SFC_SW_DWN']
        df = pd.DataFrame.from_dict(solar_dict, orient='index', columns=['GHI'])
        df.index = pd.to_datetime(df.index, format='%Y%m%d')
        df.index.name = 'Date'
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to parse NASA API response: {e}")

    # Filter missing data (NASA uses -999 for missing)
    original_len = len(df)
    df = df[df['GHI'] > -900].copy()
    removed = original_len - len(df)

    if removed > 0:
        warnings.warn(f"Removed {removed} days with missing data")

    print(f"✅ Success! Loaded {len(df)} days of historical solar data")

    # Cache for future use
    if cache:
        cache_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_file)
        print(f"💾 Cached data to {cache_file}")

    return df


def get_volatility_params(df: pd.DataFrame, window: int = 365,
                         deseason: bool = True,
                         cap_volatility: float = 2.0) -> Tuple[float, pd.DataFrame]:
    """
    Calculates the Annualized Volatility (Sigma) from solar irradiance data.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with GHI column
    window : int
        Trading periods per year for annualization (default: 365)
    deseason : bool
        If True, remove seasonal component before calculating volatility
    cap_volatility : float
        Maximum volatility (default: 2.0 = 200%) to prevent numerical issues

    Returns
    -------
    Tuple[float, pd.DataFrame]
        (annualized_volatility, dataframe_with_returns)
    """

    df = df.copy()

    # If deseason=True, remove seasonal component
    if deseason:
        # Add month column
        df['Month'] = df.index.month

        # Calculate monthly average GHI
        monthly_avg = df.groupby('Month')['GHI'].transform('mean')

        # Deseasonalized GHI = actual / monthly_average
        df['GHI_Deseason'] = df['GHI'] / monthly_avg

        # Calculate returns on deseasonalized data
        df['Returns'] = df['GHI_Deseason'].pct_change()

        print(f"   ℹ️  Deseasoning applied: removes summer/winter cycles")
    else:
        # Calculate daily % change in raw solar output
        df['Returns'] = df['GHI'].pct_change()

    # Remove infinite/NaN values
    valid_returns = df['Returns'].replace([np.inf, -np.inf], np.nan).dropna()

    if len(valid_returns) < 2:
        warnings.warn("Not enough valid returns to estimate volatility; defaulting to 20%")
        return 0.20, df

    # Standard Deviation of daily returns
    daily_vol = valid_returns.std()

    # Annualize using Root-Mean-Square Rule: σ_annual = σ_daily × √periods
    annual_vol = daily_vol * np.sqrt(window)

    # Cap volatility to prevent numerical issues in Monte-Carlo
    if annual_vol > cap_volatility:
        warnings.warn(f"Volatility {annual_vol:.2%} exceeds cap {cap_volatility:.0%}, capping for numerical stability")
        annual_vol = cap_volatility

    # Sanity check
    if not np.isfinite(annual_vol) or annual_vol <= 0:
        warnings.warn(f"Invalid volatility {annual_vol}; defaulting to 20%")
        annual_vol = 0.20

    return float(annual_vol), df


def compute_solar_price(df: pd.DataFrame,
                       energy_value_per_kwh: float = 0.10,
                       panel_efficiency: float = 0.20,
                       panel_area_m2: float = 1.0) -> np.ndarray:
    """
    Compute underlying asset price from GHI data.

    Converts solar irradiance to economic value:
    Price = GHI × Panel_Efficiency × Area × Energy_Value

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with GHI column
    energy_value_per_kwh : float
        Economic value of 1 kWh of energy ($/kWh)
    panel_efficiency : float
        Solar panel conversion efficiency (0-1, default 0.20 = 20%)
    panel_area_m2 : float
        Panel area in square meters (default: 1.0)

    Returns
    -------
    np.ndarray
        Array of daily energy prices
    """

    # Energy generated (kWh) = GHI × efficiency × area
    energy_kwh = df['GHI'] * panel_efficiency * panel_area_m2

    # Economic value ($) = energy × price per kWh
    prices = energy_kwh * energy_value_per_kwh

    return prices.to_numpy()


def load_solar_parameters(
    lat: float = LAT,
    lon: float = LON,
    start: int = START_YEAR,
    end: int = END_YEAR,
    T: float = 1.0,
    r: float = 0.05,
    energy_value_per_kwh: float = 0.10,
    cache: bool = True
) -> Dict:
    """
    Load all parameters for solar derivative pricing from NASA data.

    Parameters
    ----------
    lat : float
        Latitude (default: Taoyuan, Taiwan)
    lon : float
        Longitude (default: Taoyuan, Taiwan)
    start : int
        Start year
    end : int
        End year
    T : float
        Time to maturity (years)
    r : float
        Risk-free rate
    energy_value_per_kwh : float
        Economic value per kWh
    cache : bool
        Use cached data if available

    Returns
    -------
    Dict
        Dictionary with pricing parameters:
        - S0: Initial energy price
        - sigma: Estimated volatility (from solar data)
        - T: Time to maturity
        - r: Risk-free rate
        - K: Strike price (set to current price)
        - ghi_df: Full GHI DataFrame
        - energy_prices: Array of daily energy prices
        - location: Dict with lat/lon
    """

    # Fetch NASA data
    ghi_df = fetch_nasa_data(lat, lon, start, end, cache)

    # Calculate volatility
    sigma, ghi_df = get_volatility_params(ghi_df)

    # Compute energy prices
    energy_prices = compute_solar_price(ghi_df, energy_value_per_kwh)

    # Get current price (latest)
    S0 = float(energy_prices[-1])

    # Strike price (at-the-money)
    K = S0

    params = {
        'S0': S0,
        'sigma': sigma,
        'T': T,
        'r': r,
        'K': K,
        'ghi_df': ghi_df,
        'energy_prices': energy_prices,
        'location': {
            'latitude': lat,
            'longitude': lon,
            'name': 'Taoyuan, Taiwan'
        },
        'data_source': 'NASA POWER API',
        'parameter': 'ALLSKY_SFC_SW_DWN (GHI)',
        'date_range': f"{start}-{end}"
    }

    return params


def get_solar_summary(params: Dict) -> Dict:
    """
    Get summary statistics from solar data.

    Parameters
    ----------
    params : Dict
        Parameters dictionary from load_solar_parameters()

    Returns
    -------
    Dict
        Summary statistics
    """

    ghi_df = params['ghi_df']
    energy_prices = params['energy_prices']

    summary = {
        'location': params['location']['name'],
        'latitude': params['location']['latitude'],
        'longitude': params['location']['longitude'],
        'data_source': params['data_source'],
        'date_range': params['date_range'],
        'start_date': ghi_df.index.min(),
        'end_date': ghi_df.index.max(),
        'n_days': len(ghi_df),
        'ghi_mean': ghi_df['GHI'].mean(),
        'ghi_std': ghi_df['GHI'].std(),
        'ghi_min': ghi_df['GHI'].min(),
        'ghi_max': ghi_df['GHI'].max(),
        'price_mean': np.mean(energy_prices),
        'price_std': np.std(energy_prices),
        'price_current': params['S0'],
        'volatility': params['sigma']
    }

    return summary


if __name__ == "__main__":
    """
    Demo: Fetch NASA data and calculate volatility
    """
    print("="*80)
    print("NASA POWER API Solar Data Loader - Demo".center(80))
    print("="*80)

    # Load parameters
    params = load_solar_parameters()

    # Display summary
    summary = get_solar_summary(params)

    print(f"\n📍 LOCATION:")
    print(f"   {summary['location']}")
    print(f"   Latitude: {summary['latitude']}°N")
    print(f"   Longitude: {summary['longitude']}°E")

    print(f"\n📊 DATA SUMMARY:")
    print(f"   Source: {summary['data_source']}")
    print(f"   Date Range: {summary['date_range']}")
    print(f"   Trading Days: {summary['n_days']}")

    print(f"\n☀️ SOLAR IRRADIANCE (GHI):")
    print(f"   Mean: {summary['ghi_mean']:.2f} kW-hr/m²/day")
    print(f"   Std Dev: {summary['ghi_std']:.2f} kW-hr/m²/day")
    print(f"   Range: [{summary['ghi_min']:.2f}, {summary['ghi_max']:.2f}]")

    print(f"\n💰 ENERGY PRICES:")
    print(f"   Mean: ${summary['price_mean']:.4f}")
    print(f"   Std Dev: ${summary['price_std']:.4f}")
    print(f"   Current (S₀): ${summary['price_current']:.4f}")

    print(f"\n📈 VOLATILITY:")
    print(f"   Annualized (σ): {summary['volatility']:.2%}")

    print(f"\n💡 DERIVATIVES PARAMETERS:")
    print(f"   S₀ = ${params['S0']:.4f}")
    print(f"   K = ${params['K']:.4f} (at-the-money)")
    print(f"   σ = {params['sigma']:.2%}")
    print(f"   T = {params['T']} year")
    print(f"   r = {params['r']:.2%}")

    print("\n" + "="*80)
    print("✅ NASA data integration successful!")
    print("="*80)
