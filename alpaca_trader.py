"""
Alpaca Trading Integration
==========================
Handles live/paper trading via Alpaca API.
Supports: portfolio sync, rebalancing, order execution.
"""

import os
import json
import math
import datetime as dt

try:
    import requests
except ImportError:
    requests = None


class AlpacaTrader:
    """Thin wrapper around Alpaca's REST API for portfolio rebalancing."""

    def __init__(self):
        self.api_key = os.environ.get("ALPACA_API_KEY", "")
        self.secret_key = os.environ.get("ALPACA_SECRET_KEY", "")
        self.base_url = os.environ.get(
            "ALPACA_BASE_URL", "https://paper-api.alpaca.markets"
        )
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json",
        }

    @property
    def is_configured(self):
        return bool(self.api_key and self.secret_key)

    def _get(self, path):
        r = requests.get(f"{self.base_url}{path}", headers=self.headers)
        r.raise_for_status()
        return r.json()

    def _post(self, path, data):
        r = requests.post(
            f"{self.base_url}{path}", headers=self.headers, json=data
        )
        r.raise_for_status()
        return r.json()

    def _delete(self, path):
        r = requests.delete(f"{self.base_url}{path}", headers=self.headers)
        r.raise_for_status()
        return r.json() if r.text else {}

    # ── Account ──────────────────────────────────────────────

    def get_account(self):
        """Get account info including buying power and equity."""
        return self._get("/v2/account")

    def get_positions(self):
        """Get all current positions."""
        return self._get("/v2/positions")

    def get_position(self, symbol):
        """Get a specific position."""
        try:
            return self._get(f"/v2/positions/{symbol}")
        except Exception:
            return None

    # ── Orders ───────────────────────────────────────────────

    def submit_order(self, symbol, qty, side, order_type="market", tif="day"):
        """Submit a single order."""
        if qty <= 0:
            return None
        return self._post("/v2/orders", {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": order_type,
            "time_in_force": tif,
        })

    def get_orders(self, status="open"):
        """List orders by status."""
        return self._get(f"/v2/orders?status={status}")

    def cancel_all_orders(self):
        """Cancel all open orders."""
        return self._delete("/v2/orders")

    # ── Rebalancing ──────────────────────────────────────────

    def calculate_rebalance(self, target_weights, capital=None):
        """
        Calculate trades needed to rebalance to target weights.

        Args:
            target_weights: dict of {ticker: weight} where weights sum to ~1.0
            capital: override capital amount; otherwise uses account equity

        Returns:
            list of {symbol, side, qty, current_value, target_value, diff}
        """
        account = self.get_account()
        equity = float(account["equity"])
        deploy_capital = capital if capital else equity

        # Get current positions
        positions = self.get_positions()
        current = {}
        for pos in positions:
            current[pos["symbol"]] = {
                "qty": float(pos["qty"]),
                "market_value": float(pos["market_value"]),
                "current_price": float(pos["current_price"]),
            }

        trades = []
        for ticker, weight in target_weights.items():
            target_value = deploy_capital * weight
            cur = current.get(ticker, {"qty": 0, "market_value": 0, "current_price": 0})

            if cur["current_price"] == 0:
                # Need to look up price – skip for now, will use market order
                diff_value = target_value - cur["market_value"]
                shares_to_trade = 0  # Will be determined at order time
            else:
                diff_value = target_value - cur["market_value"]
                shares_to_trade = abs(math.floor(diff_value / cur["current_price"]))

            if abs(diff_value) < 10:  # Skip tiny trades
                continue

            trades.append({
                "symbol": ticker,
                "side": "buy" if diff_value > 0 else "sell",
                "qty": shares_to_trade,
                "current_value": round(cur["market_value"], 2),
                "target_value": round(target_value, 2),
                "diff": round(diff_value, 2),
            })

        return trades

    def execute_rebalance(self, target_weights, capital=None, dry_run=True):
        """
        Execute a full rebalance.

        Args:
            target_weights: dict of {ticker: weight}
            capital: capital to deploy
            dry_run: if True, only calculate, don't execute

        Returns:
            dict with trades and results
        """
        trades = self.calculate_rebalance(target_weights, capital)

        if dry_run:
            return {
                "mode": "dry_run",
                "trades": trades,
                "timestamp": dt.datetime.now().isoformat(),
            }

        # Execute sells first, then buys
        results = {"sells": [], "buys": [], "errors": []}

        sells = [t for t in trades if t["side"] == "sell"]
        buys = [t for t in trades if t["side"] == "buy"]

        for trade in sells + buys:
            try:
                if trade["qty"] > 0:
                    order = self.submit_order(
                        trade["symbol"], trade["qty"], trade["side"]
                    )
                    bucket = "sells" if trade["side"] == "sell" else "buys"
                    results[bucket].append({
                        "symbol": trade["symbol"],
                        "order_id": order.get("id"),
                        "qty": trade["qty"],
                        "side": trade["side"],
                        "status": order.get("status"),
                    })
            except Exception as e:
                results["errors"].append({
                    "symbol": trade["symbol"],
                    "error": str(e),
                })

        results["timestamp"] = dt.datetime.now().isoformat()
        results["mode"] = "live"
        return results

    # ── Liquidation ──────────────────────────────────────────

    def liquidate_all(self):
        """Liquidate all positions (use with caution)."""
        return self._delete("/v2/positions")


def get_target_weights():
    """Return the Divisadero top-15 target weights."""
    from app import TOP_15
    return {h["ticker"]: h["weight"] for h in TOP_15}


if __name__ == "__main__":
    trader = AlpacaTrader()
    if trader.is_configured:
        weights = get_target_weights()
        result = trader.execute_rebalance(weights, dry_run=True)
        print(json.dumps(result, indent=2))
    else:
        print("Alpaca not configured. Set ALPACA_API_KEY and ALPACA_SECRET_KEY.")
