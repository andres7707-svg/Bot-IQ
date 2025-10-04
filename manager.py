# manager.py - handles stake sizing and sequential recovery logic
import csv
import time
from datetime import datetime

class TradeManager:
    def __init__(self, connector, risk_per_trade=0.01, min_stake=1.0, recovery_multiplier=2.0, max_recovery_steps=3, max_sequential_trades=10):
        self.conn = connector
        self.risk = float(risk_per_trade)
        self.min_stake = float(min_stake)
        self.recovery_multiplier = float(recovery_multiplier)
        self.max_recovery_steps = int(max_recovery_steps)
        self.max_sequential_trades = int(max_sequential_trades)
        self.logfile = 'trades_log.csv'
        self._init_log()

    def _init_log(self):
        try:
            with open(self.logfile, 'x', newline='') as f:
                w = csv.writer(f)
                w.writerow(['ts','asset','dir','amount','result','info'])
        except FileExistsError:
            pass

    def calc_stake(self, balance, base_fraction):
        stake = max(self.min_stake, round(balance * base_fraction, 2))
        return stake

    def run_sequential(self, asset, direction, balance, base_fraction):
        """Runs a sequence of sequential trades: if win -> next trade same stake; if loss -> increase stake by recovery_multiplier and retry (up to max_recovery_steps).
        Returns when sequence stops (either max steps reached or optionally user stops)."""
        base_stake = self.calc_stake(balance, base_fraction)
        stake = base_stake
        step = 0
        while step < self.max_sequential_trades:
            ts = datetime.utcnow().isoformat()
            print(f"Placing trade step {step+1} on {asset} - {direction} stake={stake}")
            res = self.conn.buy_asset(asset, stake, direction, expiration_minutes=1)
            info = str(res)
            outcome = 'unknown'
            if not res:
                outcome = 'error'
                self._log(ts, asset, direction, stake, outcome, info)
                # treat as loss conservative
                outcome = 'loss'
            else:
                # wait for resolution and attempt to determine result
                time.sleep(65)  # wait 65s for 1m trade to close (buffer)
                result = self.conn.check_trade_result(res)
                if result == 'win':
                    outcome = 'win'
                elif result == 'loss':
                    outcome = 'loss'
                else:
                    outcome = 'unknown'
            self._log(ts, asset, direction, stake, outcome, info)

            if outcome == 'win':
                # after a win, next trade uses same stake per your rule
                stake = base_stake
                step += 1
                # continue to place next trade with same stake
                continue
            elif outcome == 'loss':
                # increase stake to recover previous loss + target profit
                stake = round(stake * self.recovery_multiplier, 2)
                step += 1
                # if exceeded recovery steps, stop sequence
                if step >= self.max_recovery_steps:
                    print('Max recovery steps reached, stopping sequence for asset', asset)
                    break
                continue
            else:
                # unknown outcome -> stop to avoid guessing
                print('Outcome unknown, stopping sequence for safety. Asset:', asset)
                break

    def _log(self, ts, asset, direction, amount, result, info=''):
        with open(self.logfile, 'a', newline='') as f:
            w = csv.writer(f)
            w.writerow([ts, asset, direction, amount, result, info])
