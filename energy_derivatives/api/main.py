"""
FastAPI service exposing pricing, Greeks, and stress testing endpoints.
"""

import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi import Header, HTTPException
from pydantic import BaseModel, Field
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

# Ensure local package imports work when run as module
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from spk_derivatives.data_loader import load_parameters  # type: ignore  # noqa: E402
from spk_derivatives.binomial import BinomialTree  # type: ignore  # noqa: E402
from spk_derivatives.monte_carlo import MonteCarloSimulator  # type: ignore  # noqa: E402
from spk_derivatives.sensitivities import GreeksCalculator  # type: ignore  # noqa: E402


app = FastAPI(title="Energy Derivatives API", version="1.0.0")
API_KEY = os.getenv("API_KEY")
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


class PriceRequest(BaseModel):
    S0: Optional[float] = Field(None, description="Underlying price; defaults to CEIR-derived")
    K: Optional[float] = Field(None, description="Strike; defaults to S0")
    T: float = 1.0
    r: float = 0.05
    sigma: Optional[float] = Field(None, description="Volatility; defaults to CEIR-derived")
    method: str = Field("binomial", pattern="^(binomial|monte_carlo)$")
    N: int = 100
    num_simulations: int = 10000
    payoff_type: str = Field("call", pattern="^(call|redeemable)$")
    data_dir: str = "../empirical"
    use_repo_fallback: bool = True


class GreeksRequest(BaseModel):
    S0: Optional[float] = None
    K: Optional[float] = None
    T: float = 1.0
    r: float = 0.05
    sigma: Optional[float] = None
    pricing_method: str = Field("binomial", pattern="^(binomial|monte_carlo)$")
    N: int = 100
    num_simulations: int = 5000
    payoff_type: str = Field("call", pattern="^(call|redeemable)$")
    seed: Optional[int] = None
    data_dir: str = "../empirical"
    use_repo_fallback: bool = True


class StressRequest(BaseModel):
    S0: Optional[float] = None
    K: Optional[float] = None
    T: float = 1.0
    r: float = 0.05
    sigma: Optional[float] = None
    payoff_type: str = Field("call", pattern="^(call|redeemable)$")
    num_simulations: int = 5000
    volatilities: Optional[List[float]] = None
    rates: Optional[List[float]] = None
    data_dir: str = "../empirical"
    use_repo_fallback: bool = True


def _ensure_params(S0: Optional[float], sigma: Optional[float], K: Optional[float],
                   data_dir: str, use_repo_fallback: bool):
    params = {}
    if S0 is None or sigma is None or K is None:
        derived = load_parameters(data_dir=data_dir, use_repo_fallback=use_repo_fallback)
        params.update(derived)
    if S0 is not None:
        params["S0"] = S0
    if sigma is not None:
        params["sigma"] = sigma
    if K is not None:
        params["K"] = K
    if "K" not in params:
        params["K"] = params["S0"]
    return params


def _check_api_key(x_api_key: Optional[str]):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _validate_limits(req: PriceRequest):
    if req.method == "binomial" and req.N > 2000:
        raise HTTPException(status_code=400, detail="Binomial steps too large (max 2000)")
    if req.method == "monte_carlo" and req.num_simulations > 1_000_000:
        raise HTTPException(status_code=400, detail="Too many simulations (max 1,000,000)")


@app.get("/")
def root(request: Request, x_api_key: Optional[str] = Header(default=None)):
    _check_api_key(x_api_key)
    return {"status": "ok", "message": "Energy Derivatives API"}


@app.post("/price")
@limiter.limit("30/minute")
def price(request: Request, req: PriceRequest, x_api_key: Optional[str] = Header(default=None)):
    _check_api_key(x_api_key)
    _validate_limits(req)
    params = _ensure_params(req.S0, req.sigma, req.K, req.data_dir, req.use_repo_fallback)
    params.update({"T": req.T, "r": req.r})

    if req.method == "binomial":
        tree = BinomialTree(params["S0"], params["K"], params["T"], params["r"],
                            params["sigma"], req.N, req.payoff_type)
        value = tree.price()
        return {
            "method": "binomial",
            "price": value,
            "steps": req.N,
            "inputs": params
        }
    else:
        sim = MonteCarloSimulator(params["S0"], params["K"], params["T"], params["r"],
                                  params["sigma"], req.num_simulations,
                                  payoff_type=req.payoff_type)
        price, low, high = sim.confidence_interval()
        return {
            "method": "monte_carlo",
            "price": price,
            "ci_95": [low, high],
            "num_simulations": req.num_simulations,
            "inputs": params
        }


@app.post("/greeks")
@limiter.limit("30/minute")
def greeks(request: Request, req: GreeksRequest, x_api_key: Optional[str] = Header(default=None)):
    _check_api_key(x_api_key)
    params = _ensure_params(req.S0, req.sigma, req.K, req.data_dir, req.use_repo_fallback)
    params.update({"T": req.T, "r": req.r})

    calc = GreeksCalculator(
        params["S0"], params["K"], params["T"], params["r"], params["sigma"],
        pricing_method=req.pricing_method,
        N=req.N,
        num_simulations=req.num_simulations,
        payoff_type=req.payoff_type,
        seed=req.seed
    )
    greeks = calc.compute_all_greeks()
    return {"inputs": params, "greeks": greeks}


@app.post("/stress")
@limiter.limit("10/minute")
def stress(request: Request, req: StressRequest, x_api_key: Optional[str] = Header(default=None)):
    _check_api_key(x_api_key)
    params = _ensure_params(req.S0, req.sigma, req.K, req.data_dir, req.use_repo_fallback)
    params.update({"T": req.T, "r": req.r})

    results = {}
    sim = MonteCarloSimulator(
        params["S0"], params["K"], params["T"], params["r"], params["sigma"],
        req.num_simulations, payoff_type=req.payoff_type
    )
    base_price = sim.price()
    results["base_price"] = base_price

    if req.volatilities:
        vol_results = []
        for vol in req.volatilities:
            s = MonteCarloSimulator(params["S0"], params["K"], params["T"], params["r"], vol,
                                    req.num_simulations, payoff_type=req.payoff_type)
            vol_results.append({"vol": vol, "price": s.price()})
        results["vol_stress"] = vol_results

    if req.rates:
        rate_results = []
        for rate in req.rates:
            s = MonteCarloSimulator(params["S0"], params["K"], params["T"], rate, params["sigma"],
                                    req.num_simulations, payoff_type=req.payoff_type)
            rate_results.append({"rate": rate, "price": s.price()})
        results["rate_stress"] = rate_results

    return {"inputs": params, "results": results}
