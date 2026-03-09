# 🍌 Banana Selling Optimizer
Have you ever wondered How supermarkets determine your spending habits? I had this thought while walking to the gym, on my way I picked up a banana from a supermarket and noticed I could have paid for them by the kilo or by a stack of 5. It made me curious about when supermarket choose the price of Bananas. So I made **GoBananas**
> An interactive dashboard to determine whether you should sell bananas **by the piece** or **by the kilo** — and *why*.

![Python](https://img.shields.io/badge/Python-3.9%2B-yellow?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red?logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-5.19%2B-blue?logo=plotly)

---

## The Problem

Selling a banana by the piece typically yields a **higher per-kg revenue** — but selling by the kilo moves **more volume** and can reduce spoilage losses. The optimal strategy depends on:

- 📍 **Location** — high foot traffic (markets, stations) favours piece sales
- 💸 **Customer price sensitivity** — budget-conscious buyers prefer kilo
- 🤢 **Spoilage risk** — faster turnover via pieces can offset the unit premium
- 🏷️ **Your pricing** — the break-even piece price is rarely where you think

This dashboard lets you tune all these variables and immediately see which strategy wins.

---

## Features

| Chart | What it shows |
|---|---|
| **Verdict card** | Instant recommendation with % advantage |
| **Foot Traffic sweep** | How profit shifts as your location gets busier |
| **Price Sensitivity sweep** | When price-conscious customers flip the calculus |
| **Strategy Heatmap** | 2D grid of every foot-traffic × sensitivity combo |
| **Break-even: Piece Price** | Minimum piece price to beat kilo selling |
| **30-day Projection** | Cumulative profit with daily demand noise |
| **Margin Breakdown** | Revenue, spoilage, cost, and net margin side-by-side |

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/your-username/banana-optimizer.git
cd banana-optimizer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run GoBananas.py
```

The dashboard opens at **http://localhost:8501**.

---

## Project Structure

```
banana-optimizer/
├── GoBananas.py            # Streamlit dashboard (UI + charts)
├── models.py         # Business logic & optimization models
├── requirements.txt
└── README.md
```

### `models.py`

All pure Python — no UI dependencies. Key functions:

```python
from models import MarketConfig, profit_analysis

config = MarketConfig(
    price_per_piece=0.30,
    price_per_kilo=1.20,
    foot_traffic_multiplier=2.5,  # busy market
    price_sensitivity=0.7,         # premium shoppers
)

result = profit_analysis(config)
print(result["optimal"])        # "Piece" or "Kilo"
print(result["daily_profit_piece"])
print(result["advantage_pct"])
```

---

## The Model

### Revenue normalisation

Everything is normalised to **€ per kg** so the two strategies are directly comparable:

```
Revenue/kg (piece) = price_per_piece × bananas_per_kilo
Revenue/kg (kilo)  = price_per_kilo
```

### Spoilage adjustment

Piece selling clears stock faster → lower effective spoilage (60% of base rate).  
Kilo selling is slower → full spoilage rate applies.

### Demand capture

Each strategy captures a different slice of your customer base:

```
piece_capture = piece_demand% + (indifferent% × 1/price_sensitivity × foot_traffic × 0.5)
kilo_capture  = kilo_demand%  + (indifferent% × price_sensitivity × 0.6)
```

### Daily profit

```
daily_profit = gross_margin_per_kg × display_capacity_kg × demand_capture
```

---

## Extending the model

Want to add your own variables? Edit `models.py`:

- Add fields to `MarketConfig`
- Update `profit_analysis()` to use them
- Add a new sweep function (e.g. `sweep_spoilage_rate`)
- Drop a new chart into `app.py`

---

## License

MIT — use it, fork it, sell bananas with it. 🍌
