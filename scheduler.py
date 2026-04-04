"""
Quarterly Rebalance Scheduler
==============================
Runs as a background thread or standalone cron job.
Checks if a quarterly rebalance is due and executes it.
"""

import os
import json
import datetime as dt
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


REBALANCE_MONTHS = {3, 6, 9, 12}  # End of each quarter
REBALANCE_DAY = 1                  # 1st trading day of next quarter


def is_rebalance_day(date=None):
    """Check if today is a quarterly rebalance day."""
    d = date or dt.date.today()
    return d.month in {1, 4, 7, 10} and d.day <= 5 and d.weekday() < 5


def get_last_rebalance_file():
    return os.path.join(os.path.dirname(__file__), ".last_rebalance")


def was_already_rebalanced_this_quarter():
    """Check if we already rebalanced this quarter."""
    fpath = get_last_rebalance_file()
    if not os.path.exists(fpath):
        return False
    with open(fpath) as f:
        last = f.read().strip()
    try:
        last_date = dt.date.fromisoformat(last)
        today = dt.date.today()
        return (last_date.year == today.year and
                (last_date.month - 1) // 3 == (today.month - 1) // 3)
    except ValueError:
        return False


def mark_rebalanced():
    """Record that we rebalanced today."""
    fpath = get_last_rebalance_file()
    with open(fpath, "w") as f:
        f.write(dt.date.today().isoformat())


def run_rebalance(dry_run=True):
    """Execute a rebalance if conditions are met."""
    from alpaca_trader import AlpacaTrader, get_target_weights

    if not is_rebalance_day():
        logger.info("Not a rebalance day. Skipping.")
        return None

    if was_already_rebalanced_this_quarter():
        logger.info("Already rebalanced this quarter. Skipping.")
        return None

    trader = AlpacaTrader()
    if not trader.is_configured:
        logger.warning("Alpaca not configured. Skipping rebalance.")
        return None

    weights = get_target_weights()
    capital_override = os.environ.get("DEPLOY_CAPITAL")
    capital = float(capital_override) if capital_override else None

    logger.info(f"Running {'dry-run' if dry_run else 'LIVE'} rebalance...")
    result = trader.execute_rebalance(weights, capital=capital, dry_run=dry_run)

    if not dry_run and result.get("mode") == "live":
        mark_rebalanced()

    logger.info(f"Rebalance result: {json.dumps(result, indent=2)}")
    return result


def scheduler_loop(check_interval=3600):
    """
    Long-running loop that checks for rebalance conditions.
    For production, use a proper scheduler like APScheduler or cron.
    """
    logger.info("Rebalance scheduler started.")
    while True:
        try:
            dry_run = os.environ.get("REBALANCE_LIVE", "false").lower() != "true"
            run_rebalance(dry_run=dry_run)
        except Exception as e:
            logger.error(f"Rebalance error: {e}")
        time.sleep(check_interval)


if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        dry = "--live" not in sys.argv
        result = run_rebalance(dry_run=dry)
        if result:
            print(json.dumps(result, indent=2))
    else:
        scheduler_loop()
