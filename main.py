# main.py - orchestrator: scans OTC assets and triggers sequences when a strategy signals
import os
import time
import signal
from dotenv import load_dotenv
from connector import IQConnector
from strategy import Strategies
from manager import TradeManager
import pandas as pd

load_dotenv()

EMAIL = os.getenv('IQ_EMAIL')
PASSWORD = os.getenv('IQ_PASSWORD')
MODE = os.getenv('MODE','PRACTICE')
ASSETS_ENV = os.getenv('ASSETS','')
RISK = float(os.getenv('RISK_PER_TRADE', 0.01))
TIMEFRAME = int(os.getenv('TIMEFRAME_SEC', 60))
CANDLES = int(os.getenv('CANDLES', 120))
MAX_TRADES_PER_MIN = int(os.getenv('MAX_TRADES_PER_MIN', 3))
MAX_LOSSES_IN_ROW = int(os.getenv('MAX_LOSSES_IN_ROW', 5))
COOLDOWN_AFTER_LOSS_SEC = int(os.getenv('COOLDOWN_AFTER_LOSS_SEC', 60))
MIN_STAKE = float(os.getenv('MIN_STAKE', 1.0))
RECOVERY_MULTIPLIER = float(os.getenv('RECOVERY_MULTIPLIER', 2.0))
MAX_RECOVERY_STEPS = int(os.getenv('MAX_RECOVERY_STEPS', 3))
MAX_SEQUENTIAL_TRADES = int(os.getenv('MAX_SEQUENTIAL_TRADES', 10))

running = True

def signal_handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, signal_handler)

def df_from_candles(candles):
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles)
    for col in ['ts','open','high','low','close','volume']:
        if col not in df.columns:
            df[col] = None
    return df[['ts','open','high','low','close','volume']]

def main():
    if not EMAIL or not PASSWORD:
        print('ERROR: configure IQ_EMAIL and IQ_PASSWORD as environment variables (.env)')
        return
    conn = IQConnector(EMAIL, PASSWORD, MODE)
    print('Connecting...')
    try:
        conn.connect()
    except Exception as e:
        print('Failed to connect:', e)
        return

    otc_assets = conn.get_all_assets()
    if not otc_assets:
        if ASSETS_ENV:
            otc_assets = [a.strip() for a in ASSETS_ENV.split(',') if a.strip()]
        else:
            print('No OTC assets detected and ASSETS env is empty. Exiting.')
            return

    print('OTC assets to monitor:', otc_assets)

    tm = TradeManager(conn, risk_per_trade=RISK, min_stake=MIN_STAKE, recovery_multiplier=RECOVERY_MULTIPLIER, max_recovery_steps=MAX_RECOVERY_STEPS, max_sequential_trades=MAX_SEQUENTIAL_TRADES)

    losses_in_row = 0
    last_loss_ts = None
    trades_last_min = []

    print('Starting main loop...')
    global running
    while running:
        loop_start = time.time()
        # rate limit list per minute
        trades_this_cycle = 0
        for asset in otc_assets:
            # refresh trade timestamps
            trades_last_min = [t for t in trades_last_min if t > time.time() - 60]
            if len(trades_last_min) >= MAX_TRADES_PER_MIN:
                break
            if losses_in_row >= MAX_LOSSES_IN_ROW:
                print('Max losses in a row reached. Pausing trading.')
                running = False
                break
            if last_loss_ts and (time.time() - last_loss_ts) < COOLDOWN_AFTER_LOSS_SEC:
                continue
            candles = conn.get_candles(asset, timeframe_seconds=TIMEFRAME, count=CANDLES)
            df = df_from_candles(candles)
            if df.empty or len(df) < 30:
                time.sleep(0.3)
                continue
            signal = Strategies.simple_otc_1m(df)
            if signal in ('call','put'):
                try:
                    balance = conn.Iq.get_balance()
                except Exception:
                    balance = 1000.0
                print(f"Signal {signal} on {asset} - balance approx {balance}")
                # run sequential trades for this asset/direction
                tm.run_sequential(asset, signal, balance, RISK)
                trades_last_min.append(time.time())
                trades_this_cycle += 1
                # After sequence, you could update losses_in_row by reading the last lines of logfile - omitted here
            time.sleep(0.5)
        elapsed = time.time() - loop_start
        if elapsed < 5:
            time.sleep(5 - elapsed)
    print('Bot stopped.')

if __name__ == '__main__':
    main()
