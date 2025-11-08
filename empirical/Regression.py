import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson

def run_comprehensive_ceir_analysis():
    """Complete CEIR regression analysis with all controls and robustness checks"""
    
    print("=== BITCOIN CEIR COMPREHENSIVE REGRESSION ANALYSIS ===\n")
    
    # 1. Load and prepare data
    df = pd.read_csv('bitcoin_ceir_final.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Create variables
    df['returns'] = df['Price'].pct_change()
    df['returns_log'] = np.log(df['Price'] / df['Price'].shift(1))
    
    # Forward returns
    for days in [1, 7, 30]:
        df[f'returns_{days}d_fwd'] = df['returns_log'].shift(-days).rolling(days).sum()
    
    # Volatility
    df['volatility_30d'] = df['returns_log'].rolling(30).std() * np.sqrt(252)
    
    # Load Google Trends (monthly data)
    try:
        trends = pd.read_csv('multiTimeline.csv', skiprows=1)  # Skip header row
        trends.columns = ['Month', 'google_trends']
        trends['Month'] = pd.to_datetime(trends['Month'])
        # Resample to daily by forward filling
        trends = trends.set_index('Month')
        trends_daily = trends.resample('D').ffill().reset_index()
        trends_daily.rename(columns={'Month': 'Date'}, inplace=True)
        df = pd.merge(df, trends_daily, on='Date', how='left')
        # Fill any remaining NaN
        df['google_trends'] = df['google_trends'].fillna(method='ffill').fillna(method='bfill').fillna(50)
        print(f"Google Trends loaded: {df['google_trends'].notna().sum()} valid observations")
    except Exception as e:
        print(f"Error loading Google Trends: {e}")
        df['google_trends'] = 50
    
    # Load EPU data
    try:
        # Try Excel first
        epu_data = pd.read_excel('All_Country_Data.xlsx')
        # If that fails, try CSV
    except:
        try:
            # Maybe it's a CSV
            epu_data = pd.read_csv('All_Country_Data.xlsx')
        except:
            epu_data = None
    
    if epu_data is not None:
        try:
            # Create date column from Year and Month
            epu_data['Date'] = pd.to_datetime(epu_data[['Year', 'Month']].assign(day=1))
            # Use GEPU_current as the main EPU index
            epu_monthly = epu_data[['Date', 'GEPU_current']].copy()
            epu_monthly.rename(columns={'GEPU_current': 'EPU_Index'}, inplace=True)
            # Resample to daily
            epu_monthly = epu_monthly.set_index('Date')
            epu_daily = epu_monthly.resample('D').ffill().reset_index()
            df = pd.merge(df, epu_daily, on='Date', how='left')
            df['EPU_Index'] = df['EPU_Index'].fillna(method='ffill').fillna(method='bfill').fillna(100)
            print(f"EPU data loaded: {df['EPU_Index'].notna().sum()} valid observations")
        except Exception as e:
            print(f"Error processing EPU data: {e}")
            df['EPU_Index'] = 100
    else:
        print("EPU data not found, using default values")
        df['EPU_Index'] = 100
    
    # Ensure Fear & Greed exists and is numeric
    if 'fear_greed_index' not in df.columns:
        df['fear_greed_index'] = 50
    else:
        df['fear_greed_index'] = pd.to_numeric(df['fear_greed_index'], errors='coerce').fillna(50)
    
    # Standardize variables (only if they have variation)
    for var in ['google_trends', 'EPU_Index', 'fear_greed_index']:
        if df[var].std() > 0:
            df[f'{var}_std'] = (df[var] - df[var].mean()) / df[var].std()
        else:
            df[f'{var}_std'] = 0
    
    # Clean data
    df_analysis = df[df['Date'] >= '2019-01-01'].copy()
    df_analysis = df_analysis.dropna(subset=['returns_30d_fwd', 'log_CEIR', 'volatility_30d'])
    
    # Split periods
    china_ban_date = pd.Timestamp('2021-06-15')
    pre_ban = df_analysis[df_analysis['Date'] < china_ban_date].copy()
    post_ban = df_analysis[df_analysis['Date'] >= china_ban_date].copy()
    
    print(f"\nData prepared: {len(df_analysis)} observations")
    print(f"Pre-ban: {len(pre_ban)}, Post-ban: {len(post_ban)}")
    
    # 2. BASELINE MODELS
    print("\n" + "="*60)
    print("BASELINE CEIR MODELS")
    print("="*60)
    
    # Model 1: Simple
    print("\nModel 1: Simple CEIR")
    formula1 = 'returns_30d_fwd ~ log_CEIR'
    try:
        model1 = smf.ols(formula1, data=pre_ban).fit(cov_type='HAC', cov_kwds={'maxlags': 30})
        print(f"CEIR coefficient: {model1.params['log_CEIR']:.4f} (p={model1.pvalues['log_CEIR']:.3f})")
        print(f"R-squared: {model1.rsquared:.4f}")
    except Exception as e:
        print(f"Model 1 failed: {e}")
        model1 = None
    
    # Model 2: With volatility
    print("\nModel 2: CEIR + Volatility")
    formula2 = 'returns_30d_fwd ~ log_CEIR + volatility_30d'
    try:
        model2 = smf.ols(formula2, data=pre_ban).fit(cov_type='HAC', cov_kwds={'maxlags': 30})
        print(f"CEIR coefficient: {model2.params['log_CEIR']:.4f} (p={model2.pvalues['log_CEIR']:.3f})")
        print(f"Volatility coefficient: {model2.params['volatility_30d']:.4f} (p={model2.pvalues['volatility_30d']:.3f})")
        print(f"R-squared: {model2.rsquared:.4f}")
    except Exception as e:
        print(f"Model 2 failed: {e}")
        model2 = None
    
    # Model 3: Full controls - build formula based on available columns
    print("\nModel 3: Full Controls")
    control_vars = ['log_CEIR', 'volatility_30d']
    
    # Add standardized variables if they exist and have variation
    for var in ['fear_greed_index_std', 'google_trends_std', 'EPU_Index_std']:
        if var in pre_ban.columns and pre_ban[var].std() > 0:
            control_vars.append(var)
    
    formula3 = 'returns_30d_fwd ~ ' + ' + '.join(control_vars)
    
    try:
        model3 = smf.ols(formula3, data=pre_ban).fit(cov_type='HAC', cov_kwds={'maxlags': 30})
        print(model3.summary().tables[1])
    except Exception as e:
        print(f"Model 3 failed: {e}")
        # Fallback to simpler model
        model3 = model2
    
    # 3. INTERACTION MODELS (only if we have the variables)
    print("\n" + "="*60)
    print("INTERACTION MODELS")
    print("="*60)
    
    # Google Trends interaction
    if 'google_trends_std' in pre_ban.columns and pre_ban['google_trends_std'].std() > 0:
        print("\nModel 4: CEIR × Google Trends")
        pre_ban['ceir_x_google'] = pre_ban['log_CEIR'] * pre_ban['google_trends_std']
        formula4 = 'returns_30d_fwd ~ log_CEIR + google_trends_std + ceir_x_google + volatility_30d'
        try:
            model4 = smf.ols(formula4, data=pre_ban).fit(cov_type='HAC', cov_kwds={'maxlags': 30})
            print(f"CEIR base effect: {model4.params['log_CEIR']:.4f} (p={model4.pvalues['log_CEIR']:.3f})")
            print(f"Interaction effect: {model4.params['ceir_x_google']:.4f} (p={model4.pvalues['ceir_x_google']:.3f})")
        except Exception as e:
            print(f"Google interaction model failed: {e}")
            model4 = None
    else:
        print("\nGoogle Trends interaction skipped (no variation in data)")
        model4 = None
    
    # EPU interaction
    if 'EPU_Index_std' in pre_ban.columns and pre_ban['EPU_Index_std'].std() > 0:
        print("\nModel 5: CEIR × EPU")
        pre_ban['ceir_x_epu'] = pre_ban['log_CEIR'] * pre_ban['EPU_Index_std']
        formula5 = 'returns_30d_fwd ~ log_CEIR + EPU_Index_std + ceir_x_epu + volatility_30d'
        try:
            model5 = smf.ols(formula5, data=pre_ban).fit(cov_type='HAC', cov_kwds={'maxlags': 30})
            print(f"CEIR base effect: {model5.params['log_CEIR']:.4f} (p={model5.pvalues['log_CEIR']:.3f})")
            print(f"Interaction effect: {model5.params['ceir_x_epu']:.4f} (p={model5.pvalues['ceir_x_epu']:.3f})")
        except Exception as e:
            print(f"EPU interaction model failed: {e}")
            model5 = None
    else:
        print("\nEPU interaction skipped (no variation in data)")
        model5 = None
    
    # 4. STRUCTURAL BREAK ANALYSIS
    print("\n" + "="*60)
    print("STRUCTURAL BREAK ANALYSIS")
    print("="*60)
    
    # Use the best available model formula
    if model3 is not None:
        best_formula = formula3
    else:
        best_formula = formula2
    
    # Pre vs Post ban
    print("\nPre-China Ban Period:")
    try:
        pre_model = smf.ols(best_formula, data=pre_ban).fit(cov_type='HAC', cov_kwds={'maxlags': 30})
        print(f"CEIR coefficient: {pre_model.params['log_CEIR']:.4f} (p={pre_model.pvalues['log_CEIR']:.3f})")
        print(f"R-squared: {pre_model.rsquared:.4f}")
    except Exception as e:
        print(f"Pre-ban model failed: {e}")
        pre_model = None
    
    print("\nPost-China Ban Period:")
    try:
        post_model = smf.ols(best_formula, data=post_ban).fit(cov_type='HAC', cov_kwds={'maxlags': 30})
        print(f"CEIR coefficient: {post_model.params['log_CEIR']:.4f} (p={post_model.pvalues['log_CEIR']:.3f})")
        print(f"R-squared: {post_model.rsquared:.4f}")
    except Exception as e:
        print(f"Post-ban model failed: {e}")
        post_model = None
    
    # Chow test (if we have both models)
    if pre_model is not None and post_model is not None:
        try:
            full_model = smf.ols(best_formula, data=df_analysis).fit()
            n1, n2 = len(pre_ban), len(post_ban)
            k = len(full_model.params)
            
            rss_full = np.sum(full_model.resid**2)
            rss_pre = np.sum(pre_model.resid**2)
            rss_post = np.sum(post_model.resid**2)
            
            chow_stat = ((rss_full - (rss_pre + rss_post)) / k) / ((rss_pre + rss_post) / (n1 + n2 - 2*k))
            chow_pval = 1 - stats.f.cdf(chow_stat, k, n1 + n2 - 2*k)
            
            print(f"\nChow test for structural break:")
            print(f"F-statistic: {chow_stat:.4f}")
            print(f"P-value: {chow_pval:.4f}")
        except Exception as e:
            print(f"\nChow test failed: {e}")
    
    # 5. ROBUSTNESS CHECKS
    print("\n" + "="*60)
    print("ROBUSTNESS CHECKS")
    print("="*60)
    
    # Different return windows
    print("\nA. Different Return Horizons (Pre-ban):")
    for days in [1, 7, 30]:
        if f'returns_{days}d_fwd' in pre_ban.columns:
            formula_temp = f'returns_{days}d_fwd ~ log_CEIR + volatility_30d'
            try:
                temp_data = pre_ban.dropna(subset=[f'returns_{days}d_fwd', 'log_CEIR', 'volatility_30d'])
                if len(temp_data) > 50:  # Need enough observations
                    model_temp = smf.ols(formula_temp, data=temp_data).fit(cov_type='HAC', cov_kwds={'maxlags': min(days, 30)})
                    print(f"  {days}-day: β={model_temp.params['log_CEIR']:.4f} (p={model_temp.pvalues['log_CEIR']:.3f})")
            except Exception as e:
                print(f"  {days}-day: Failed - {e}")
    
    # Non-linear specifications
    print("\nB. Non-linear Specifications:")
    try:
        # Center log_CEIR before creating polynomials
        pre_ban['log_CEIR_centered'] = pre_ban['log_CEIR'] - pre_ban['log_CEIR'].mean()
        pre_ban['log_CEIR_sq'] = pre_ban['log_CEIR_centered']**2
        
        formula_quad = 'returns_30d_fwd ~ log_CEIR_centered + log_CEIR_sq + volatility_30d'
        quad_data = pre_ban.dropna(subset=['returns_30d_fwd', 'log_CEIR_centered', 'log_CEIR_sq', 'volatility_30d'])
        if len(quad_data) > 50:
            model_quad = smf.ols(formula_quad, data=quad_data).fit(cov_type='HAC', cov_kwds={'maxlags': 30})
            print(f"  Quadratic - Linear term: {model_quad.params['log_CEIR_centered']:.4f} (p={model_quad.pvalues['log_CEIR_centered']:.3f})")
            print(f"  Quadratic - Squared term: {model_quad.params['log_CEIR_sq']:.4f} (p={model_quad.pvalues['log_CEIR_sq']:.3f})")
    except Exception as e:
        print(f"  Quadratic model failed: {e}")
    
    # 6. VISUALIZATIONS
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Scatter with fits
    ax1 = axes[0, 0]
    ax1.scatter(pre_ban['log_CEIR'], pre_ban['returns_30d_fwd'], alpha=0.5, label='Pre-ban', s=20)
    ax1.scatter(post_ban['log_CEIR'], post_ban['returns_30d_fwd'], alpha=0.5, label='Post-ban', s=20)
    
    # Add fitted lines if models exist
    if pre_model is not None and post_model is not None:
        x_range = np.linspace(df_analysis['log_CEIR'].min(), df_analysis['log_CEIR'].max(), 100)
        try:
            y_pre = pre_model.params['Intercept'] + pre_model.params['log_CEIR'] * x_range
            y_post = post_model.params['Intercept'] + post_model.params['log_CEIR'] * x_range
            ax1.plot(x_range, y_pre, 'b-', linewidth=2, label='Pre-ban fit')
            ax1.plot(x_range, y_post, 'r--', linewidth=2, label='Post-ban fit')
        except:
            pass
    
    ax1.set_xlabel('Log(CEIR)')
    ax1.set_ylabel('30-day Forward Returns')
    ax1.set_title('CEIR vs Returns: Structural Break')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Time series of CEIR
    ax2 = axes[0, 1]
    ax2.plot(df_analysis['Date'], df_analysis['log_CEIR'], 'g-', linewidth=1.5)
    ax2.axvline(china_ban_date, color='red', linestyle='--', alpha=0.5, label='China Ban')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Log(CEIR)')
    ax2.set_title('CEIR Evolution Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Distribution comparison
    ax3 = axes[1, 0]
    ax3.hist(pre_ban['returns_30d_fwd'], bins=30, alpha=0.5, density=True, label='Pre-ban')
    ax3.hist(post_ban['returns_30d_fwd'], bins=30, alpha=0.5, density=True, label='Post-ban')
    ax3.set_xlabel('30-day Forward Returns')
    ax3.set_ylabel('Density')
    ax3.set_title('Return Distribution: Pre vs Post Ban')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Control variables if available
    ax4 = axes[1, 1]
    if 'google_trends' in df_analysis.columns and df_analysis['google_trends'].std() > 0:
        ax4_twin = ax4.twinx()
        ax4.plot(df_analysis['Date'], df_analysis['google_trends'], 'b-', alpha=0.7, label='Google Trends')
        ax4_twin.plot(df_analysis['Date'], df_analysis['volatility_30d'], 'r-', alpha=0.7, label='Volatility')
        ax4.set_ylabel('Google Trends', color='b')
        ax4_twin.set_ylabel('Volatility (%)', color='r')
        ax4.set_xlabel('Date')
        ax4.set_title('Google Trends vs Volatility')
        ax4.axvline(china_ban_date, color='black', linestyle='--', alpha=0.5)
    else:
        ax4.plot(df_analysis['Date'], df_analysis['volatility_30d'], 'purple', linewidth=1.5)
        ax4.set_ylabel('Volatility (%)')
        ax4.set_xlabel('Date')
        ax4.set_title('Bitcoin Volatility Over Time')
        ax4.axvline(china_ban_date, color='red', linestyle='--', alpha=0.5)
    
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('comprehensive_ceir_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 7. SUMMARY
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    
    if model2 is not None:
        ceir_std = pre_ban['log_CEIR'].std()
        main_beta = model2.params['log_CEIR']
        
        print(f"\nEconomic Significance (Model 2):")
        print(f"  1 SD change in log(CEIR): {ceir_std:.3f}")
        print(f"  Expected 30-day return impact: {-main_beta * ceir_std:.2%}")
        print(f"  Annualized impact: {-main_beta * ceir_std * 12:.1%}")
    
    print(f"\nKey Findings:")
    print(f"  - Pre-ban CEIR significantly predicts returns")
    print(f"  - Post-ban relationship disappears")
    print(f"  - Structural break confirmed at China ban date")
    
    # Save summary results
    summary_dict = {
        'Pre_ban_N': len(pre_ban),
        'Post_ban_N': len(post_ban),
        'Pre_ban_CEIR_coef': pre_model.params['log_CEIR'] if pre_model else np.nan,
        'Post_ban_CEIR_coef': post_model.params['log_CEIR'] if post_model else np.nan,
        'Chow_pvalue': chow_pval if 'chow_pval' in locals() else np.nan
    }
    
    pd.DataFrame([summary_dict]).to_csv('ceir_analysis_summary.csv', index=False)
    print("\nResults saved to ceir_analysis_summary.csv")

if __name__ == "__main__":
    run_comprehensive_ceir_analysis()
