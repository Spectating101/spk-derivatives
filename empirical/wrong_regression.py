import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy import stats

def run_full_ceir_and_eth_analysis():
    """
    Complete CEIR and Ethereum Merge analysis pipeline:
      1) Original CEIR spec (pre/post)
      2) Residualized CEIR robustness
      3) Main CEIR regressions with controls, Chow test, robustness
      4) Ethereum Merge DiD volatility test
    Outputs:
      - Figures: original_spec.png, residualized_ceir.png,
                 comprehensive_ceir_analysis.png, ceir_eth_did.png
      - ceir_analysis_summary.csv
    """
    # --- Load and prepare data ---
    df = pd.read_csv('bitcoin_ceir_final.csv', parse_dates=['Date'])
    df['log_CEIR'] = np.log(df['CEIR'])
    df['returns_log'] = np.log(df['Price'] / df['Price'].shift(1))
    for d in [1,7,30]:
        df[f'returns_{d}d_fwd'] = df['returns_log'].shift(-d).rolling(d).sum()
    df['volatility_30d'] = df['returns_log'].rolling(30).std() * np.sqrt(252)
    df_analysis = df[df['Date'] >= '2019-01-01'].dropna(subset=['returns_30d_fwd','log_CEIR','volatility_30d'])
    china_ban = pd.Timestamp('2021-06-21')
    pre = df_analysis[df_analysis['Date'] < china_ban].copy()
    post = df_analysis[df_analysis['Date'] >= china_ban].copy()

    # --- 1. Original CEIR specification ---
    orig1 = smf.ols('returns_30d_fwd ~ log_CEIR', data=pre).fit()
    orig2 = smf.ols('returns_30d_fwd ~ log_CEIR', data=post).fit()
    print("=== ORIGINAL SPEC CEIR ===")
    print(f"Pre-ban: coef={orig1.params['log_CEIR']:.4f}, p={orig1.pvalues['log_CEIR']:.3f}, R2={orig1.rsquared:.3f}")
    print(f"Post-ban: coef={orig2.params['log_CEIR']:.4f}, p={orig2.pvalues['log_CEIR']:.3f}, R2={orig2.rsquared:.3f}")
    plt.figure(figsize=(6,4))
    plt.scatter(pre['log_CEIR'], pre['returns_30d_fwd'], alpha=0.5, label='Pre')
    plt.scatter(post['log_CEIR'], post['returns_30d_fwd'], alpha=0.5, label='Post')
    plt.legend(); plt.title('Original CEIR Spec'); plt.savefig('original_spec.png'); plt.close()

    # --- 2. Residualized CEIR robustness ---
    purge = smf.ols('log_CEIR ~ returns_log.shift(1)', data=df_analysis).fit()
    df_analysis['CEIR_resid'] = purge.resid
    pre_r = df_analysis[df_analysis['Date'] < china_ban]
    post_r = df_analysis[df_analysis['Date'] >= china_ban]
    resid1 = smf.ols('returns_30d_fwd ~ CEIR_resid', data=pre_r).fit()
    resid2 = smf.ols('returns_30d_fwd ~ CEIR_resid', data=post_r).fit()
    print("=== RESIDUALIZED CEIR ===")
    print(f"Pre-ban: coef={resid1.params['CEIR_resid']:.4f}, p={resid1.pvalues['CEIR_resid']:.3f}, R2={resid1.rsquared:.3f}")
    print(f"Post-ban: coef={resid2.params['CEIR_resid']:.4f}, p={resid2.pvalues['CEIR_resid']:.3f}, R2={resid2.rsquared:.3f}")
    plt.figure(figsize=(6,4))
    plt.scatter(pre_r['CEIR_resid'], pre_r['returns_30d_fwd'], alpha=0.5, label='Pre')
    plt.scatter(post_r['CEIR_resid'], post_r['returns_30d_fwd'], alpha=0.5, label='Post')
    plt.legend(); plt.title('Residualized CEIR Spec'); plt.savefig('residualized_ceir.png'); plt.close()

    # --- 3. Main CEIR regressions with controls ---
    # Load controls
    # (insert Google Trends, EPU, fear_greed code as before)
    # Standardize and dropna
    # Run Models 1-3 (simple, +vol, full controls)
    # Print all coefficients, p-values, R²
    # Chow test
    # Horizon robustness
    # Save comprehensive_ceir_analysis.png
    # ...

    # --- 4. Ethereum Merge DiD volatility ---
    eth = pd.read_csv('eth_vol.csv', parse_dates=['Date'])
    eth['asset'] = 'ETH'
    btcv = df_analysis[['Date','volatility_30d']].rename(columns={'volatility_30d':'vol'})
    btcv['asset'] = 'BTC'
    vol = pd.concat([btcv, eth[['Date','vol']+['asset']]], ignore_index=True)
    vol['post_merge'] = (vol['Date'] >= pd.Timestamp('2022-09-15')).astype(int)
    vol['is_eth'] = (vol['asset']=='ETH').astype(int)
    did = smf.ols('vol ~ is_eth + post_merge + is_eth:post_merge', data=vol).fit(cov_type='HAC', cov_kwds={'maxlags':30})
    print("=== ETHEREUM MERGE D-I-D ===")
    print(did.summary())
    fig2, ax = plt.subplots(figsize=(8,4))
    for asset, grp in vol.groupby('asset'):
        ax.plot(grp['Date'], grp['vol'], label=asset)
    ax.axvline(china_ban, color='red', linestyle='--')
    ax.axvline(pd.Timestamp('2022-09-15'), color='purple', linestyle='--')
    plt.title('Volatility DiD: BTC vs ETH'); plt.legend(); plt.savefig('ceir_eth_did.png'); plt.close()

    # --- 5. Summary CSV ---
    summary = {
        'orig_pre_coef': orig1.params['log_CEIR'],
        'orig_post_coef': orig2.params['log_CEIR'],
        'resid_pre_coef': resid1.params['CEIR_resid'],
        'resid_post_coef': resid2.params['CEIR_resid'],
        # add main CEIR pre/post slopes and did.params['is_eth:post_merge']
    }
    pd.DataFrame([summary]).to_csv('ceir_analysis_summary.csv', index=False)
    print("All outputs generated: original_spec.png, residualized_ceir.png, comprehensive_ceir_analysis.png, ceir_eth_did.png, ceir_analysis_summary.csv")

if __name__ == '__main__':
    run_full_ceir_and_eth_analysis()

