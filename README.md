# Divisadero Street Capital · Lookalike Portfolio

A portfolio mirroring tool that replicates the **top 15 equity holdings** from Divisadero Street Capital Management's most recent 13F filing, weighted proportionally and rebalanced quarterly.

## Data Source

**SEC EDGAR 13F-HR Filing**
- **Fund:** Divisadero Street Capital Management, LP
- **CIK:** 0001901865
- **Period:** Q4 2025 (December 31, 2025)
- **Filed:** February 17, 2026
- **Manager:** Brian Goldenberg, Miami, FL

## Top 15 Holdings (by combined value)

| # | Ticker | Company | Weight |
|---|--------|---------|--------|
| 1 | SGHC | Super Group (SGHC) Limited | 19.56% |
| 2 | DAVE | Dave Inc | 14.82% |
| 3 | CELH | Celsius Holdings Inc | 7.85% |
| 4 | INDV | Indivior PLC | 6.78% |
| 5 | AS | Amer Sports Inc | 6.31% |
| 6 | CVNA | Carvana Co | 6.25% |
| 7 | SN | SharkNinja Inc | 5.84% |
| 8 | RSI | Rush Street Interactive Inc | 5.81% |
| 9 | FLYW | Flywire Corporation | 5.56% |
| 10 | BBW | Build-A-Bear Workshop Inc | 5.20% |
| 11 | SEZL | Sezzle Inc | 4.84% |
| 12 | APEI | American Public Education Inc | 4.29% |
| 13 | TPB | Turning Point Brands Inc | 3.91% |
| 14 | CLS | Celestica Inc | 3.51% |
| 15 | FIGS | FIGS Inc | 3.40% |

These 15 positions represent ~69% of the fund's total $2.14B 13F portfolio.

## Features

- **Weighted allocation** matching 13F filing proportions
- **Configurable capital** — enter any amount to see exact dollar allocations
- **5-year backtest** with performance metrics (CAGR, Sharpe, max drawdown)
- **Quarterly rebalancing** with simulated trade preview
- **Alpaca integration** for paper and live trading
- **Interactive dashboard** with charts, heatmaps, and tables

## Architecture

```
├── app.py                 # Flask API + backtest engine
├── alpaca_trader.py       # Alpaca trading integration
├── scheduler.py           # Quarterly rebalance scheduler
├── static/
│   └── index.html         # Full dashboard (Chart.js)
├── requirements.txt
├── Procfile               # Railway/Heroku
├── Dockerfile
├── railway.toml
└── README.md
```

## Quick Start

### Local Development

```bash
pip install -r requirements.txt
python app.py
# Open http://localhost:8080
```

### Deploy to Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select this repository
4. Add environment variables (optional for Alpaca):
   ```
   ALPACA_API_KEY=your_key
   ALPACA_SECRET_KEY=your_secret
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   DEPLOY_CAPITAL=100000
   ```
5. Railway auto-deploys on push

### Alpaca Paper Trading

1. Create a free account at [alpaca.markets](https://alpaca.markets)
2. Generate paper trading API keys
3. Set environment variables
4. The scheduler runs rebalances quarterly, or trigger manually:
   ```bash
   python scheduler.py --once
   ```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/holdings` | Top-15 holdings with weights |
| `GET /api/allocate?capital=N` | Dollar allocations for given capital |
| `GET /api/backtest?capital=N&years=5` | Historical backtest results |
| `GET /api/rebalance-preview?capital=N` | Simulated rebalance trades |
| `GET /api/alpaca-config` | Alpaca integration details |

## Disclaimer

This tool is for **educational and research purposes only**. It is not financial advice. Past performance does not guarantee future results. The backtest uses simulated price data. Always consult a qualified financial advisor before making investment decisions. 13F filings reflect positions at quarter-end and may not represent current holdings.
