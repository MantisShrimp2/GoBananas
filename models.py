"""
Banana Selling Optimization Models
Core calculations for piece vs. kilo selling strategies.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Tuple


@dataclass
class MarketConfig:
    """Configuration for a banana selling scenario."""
    # Pricing
    price_per_piece: float = 0.30       # € per piece
    price_per_kilo: float = 1.20        # € per kilo
    bananas_per_kilo: float = 6.5       # average bananas in 1kg
    cost_per_kilo: float = 0.55         # wholesale cost per kg

    # Demand
    daily_customers: int = 200          # total potential customers per day
    piece_demand_pct: float = 0.40      # % of customers preferring pieces
    kilo_demand_pct: float = 0.35       # % of customers preferring kilos
    # remaining % are indifferent

    # Operations
    spoilage_rate: float = 0.08         # % of stock lost to spoilage
    transaction_time_piece: float = 0.5 # minutes per piece transaction
    transaction_time_kilo: float = 1.0  # minutes per kilo transaction
    display_space_kg: float = 20.0      # kg of display capacity

    # Context multipliers
    foot_traffic_multiplier: float = 1.0   # 1 = normal, >1 = high traffic
    price_sensitivity: float = 1.0         # 1 = normal, >1 = very price-sensitive


def revenue_per_kg_sold(config: MarketConfig) -> Tuple[float, float]:
    """
    Returns (revenue_per_kg_piece, revenue_per_kg_kilo) —
    normalising everything to per-kg so strategies are comparable.
    """
    rev_piece = config.price_per_piece * config.bananas_per_kilo
    rev_kilo = config.price_per_kilo
    return rev_piece, rev_kilo


def profit_analysis(config: MarketConfig) -> dict:
    """Full profit breakdown for both strategies."""
    rev_piece, rev_kilo = revenue_per_kg_sold(config)
    cost = config.cost_per_kilo

    # Effective spoilage: piece selling clears stock faster → less spoilage
    # Kilo selling moves more volume → moderate spoilage
    spoilage_piece = config.spoilage_rate * 0.6   # pieces sell quickly
    spoilage_kilo = config.spoilage_rate

    gross_margin_piece = (rev_piece * (1 - spoilage_piece)) - cost
    gross_margin_kilo = (rev_kilo * (1 - spoilage_kilo)) - cost

    # Effective demand considering customer preferences & price sensitivity
    indifferent_pct = max(0, 1 - config.piece_demand_pct - config.kilo_demand_pct)
    
    # Price-sensitive customers prefer kilo
    piece_capture = (
        config.piece_demand_pct +
        indifferent_pct * (1 / config.price_sensitivity) * config.foot_traffic_multiplier * 0.5
    )
    kilo_capture = (
        config.kilo_demand_pct +
        indifferent_pct * min(1.0, config.price_sensitivity * 0.6)
    )

    # Clip to [0,1]
    piece_capture = min(piece_capture, 1.0)
    kilo_capture = min(kilo_capture, 1.0)

    daily_stock = config.display_space_kg
    daily_profit_piece = gross_margin_piece * daily_stock * piece_capture
    daily_profit_kilo = gross_margin_kilo * daily_stock * kilo_capture

    return {
        "rev_per_kg_piece": rev_piece,
        "rev_per_kg_kilo": rev_kilo,
        "margin_piece": gross_margin_piece,
        "margin_kilo": gross_margin_kilo,
        "daily_profit_piece": daily_profit_piece,
        "daily_profit_kilo": daily_profit_kilo,
        "optimal": "Piece" if daily_profit_piece > daily_profit_kilo else "Kilo",
        "advantage_pct": abs(daily_profit_piece - daily_profit_kilo) / max(daily_profit_kilo, 0.01) * 100,
        "piece_capture": piece_capture,
        "kilo_capture": kilo_capture,
    }


def sweep_foot_traffic(config: MarketConfig, n=50) -> pd.DataFrame:
    """Sweep foot traffic multiplier from 0.2 to 3.0."""
    rows = []
    for ft in np.linspace(0.2, 3.0, n):
        cfg = MarketConfig(**{**config.__dict__, "foot_traffic_multiplier": ft})
        r = profit_analysis(cfg)
        rows.append({
            "foot_traffic": ft,
            "profit_piece": r["daily_profit_piece"],
            "profit_kilo": r["daily_profit_kilo"],
            "optimal": r["optimal"],
        })
    return pd.DataFrame(rows)


def sweep_price_sensitivity(config: MarketConfig, n=50) -> pd.DataFrame:
    """Sweep price sensitivity from 0.3 to 3.0."""
    rows = []
    for ps in np.linspace(0.3, 3.0, n):
        cfg = MarketConfig(**{**config.__dict__, "price_sensitivity": ps})
        r = profit_analysis(cfg)
        rows.append({
            "price_sensitivity": ps,
            "profit_piece": r["daily_profit_piece"],
            "profit_kilo": r["daily_profit_kilo"],
            "optimal": r["optimal"],
        })
    return pd.DataFrame(rows)


def sweep_piece_price(config: MarketConfig, n=60) -> pd.DataFrame:
    """Sweep piece price to find break-even."""
    rows = []
    for pp in np.linspace(0.10, 0.80, n):
        cfg = MarketConfig(**{**config.__dict__, "price_per_piece": pp})
        r = profit_analysis(cfg)
        rows.append({
            "price_per_piece": pp,
            "profit_piece": r["daily_profit_piece"],
            "profit_kilo": r["daily_profit_kilo"],
            "optimal": r["optimal"],
        })
    return pd.DataFrame(rows)


def heatmap_data(config: MarketConfig, n=30) -> pd.DataFrame:
    """
    2D grid: foot_traffic vs price_sensitivity → optimal strategy.
    Returns DataFrame with columns: foot_traffic, price_sensitivity, advantage
    (positive = piece better, negative = kilo better)
    """
    rows = []
    for ft in np.linspace(0.2, 3.0, n):
        for ps in np.linspace(0.3, 3.0, n):
            cfg = MarketConfig(**{**config.__dict__,
                                  "foot_traffic_multiplier": ft,
                                  "price_sensitivity": ps})
            r = profit_analysis(cfg)
            advantage = r["daily_profit_piece"] - r["daily_profit_kilo"]
            rows.append({
                "foot_traffic": round(ft, 2),
                "price_sensitivity": round(ps, 2),
                "advantage": advantage,
                "optimal": r["optimal"],
            })
    return pd.DataFrame(rows)


def monthly_projection(config: MarketConfig, days: int = 30) -> pd.DataFrame:
    """Project cumulative profit over N days with random demand variation."""
    np.random.seed(42)
    rows = []
    cum_piece, cum_kilo, cum_mixed = 0.0, 0.0, 0.0
    for day in range(1, days + 1):
        # Add daily noise to demand
        noise = np.random.normal(1.0, 0.12)
        noise = max(0.5, min(1.5, noise))
        cfg_noisy = MarketConfig(**{
            **config.__dict__,
            "foot_traffic_multiplier": config.foot_traffic_multiplier * noise,
        })
        r = profit_analysis(cfg_noisy)
        cum_piece += r["daily_profit_piece"]
        cum_kilo += r["daily_profit_kilo"]
        # Mixed: weekdays piece, weekends kilo
        if day % 7 in (0, 6):
            cum_mixed += r["daily_profit_kilo"]
        else:
            cum_mixed += r["daily_profit_piece"]
        rows.append({
            "day": day,
            "cumulative_piece": cum_piece,
            "cumulative_kilo": cum_kilo,
            "cumulative_mixed": cum_mixed,
        })
    return pd.DataFrame(rows)
