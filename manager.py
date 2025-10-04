import csv
import time
import json
import os
from datetime import datetime

class TradeManager:
    def __init__(self, connector, base_amount=1, martingale_multiplier=2.2, 
                 take_profit=50, start_balance=24.65, max_losses=5):
        self.conn = connector
        self.base_amount = float(base_amount)
        self.martingale_multiplier = float(martingale_multiplier)
        self.take_profit = float(take_profit)
        self.start_balance = float(start_balance)
        self.max_losses = int(max_losses)
        
        self.logfile = 'trades_log.csv'
        self.statefile = 'bot_state.json'
        
        self.current_amount = self.base_amount
        self.consecutive_losses = 0
        self.total_profit = 0
        self.trade_count = 0
        
        self._init_log()
        self._load_state()
    
    def _init_log(self):
        try:
            with open(self.logfile, 'x', newline='') as f:
                w = csv.writer(f)
                w.writerow(['timestamp', 'asset', 'direction', 'amount', 'result', 
                           'balance', 'profit', 'martingale_step', 'info'])
        except FileExistsError:
            pass
    
    def _save_state(self):
        state = {
            'current_amount': self.current_amount,
            'consecutive_losses': self.consecutive_losses,
            'total_profit': self.total_profit,
            'trade_count': self.trade_count,
            'last_update': datetime.utcnow().isoformat()
        }
        with open(self.statefile, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _load_state(self):
        if os.path.exists(self.statefile):
            try:
                with open(self.statefile, 'r') as f:
                    state = json.load(f)
                self.current_amount = state.get('current_amount', self.base_amount)
                self.consecutive_losses = state.get('consecutive_losses', 0)
                self.total_profit = state.get('total_profit', 0)
                self.trade_count = state.get('trade_count', 0)
                print(f"📥 Loaded previous state: {self.consecutive_losses} losses, ${self.total_profit:.2f} profit")
            except:
                print("⚠️ Could not load previous state, starting fresh")
    
    def should_stop_trading(self):
        if self.consecutive_losses >= self.max_losses:
            return True, f"Max losses ({self.max_losses}) reached"
        
        if self.total_profit >= self.take_profit:
            return True, f"Take profit target (${self.take_profit}) reached"
        
        return False, None
    
    def execute_trade(self, asset, direction, balance=None, analysis=None):
        timestamp = datetime.utcnow().isoformat()
        
        if balance is None:
            try:
                balance = self.conn.Iq.get_balance()
            except:
                balance = self.start_balance + self.total_profit
        
        print(f"\n🎯 EXECUTING TRADE #{self.trade_count + 1}")
        print(f"   Asset: {asset}")
        print(f"   Direction: {direction.upper()}")
        print(f"   Amount: ${self.current_amount:.2f}")
        print(f"   Martingale Step: {self.consecutive_losses}")
        print(f"   Balance: ${balance:.2f}")
        
        if analysis:
            print(f"   📊 Analysis:")
            print(f"      RSI: {analysis.get('rsi', 0):.1f}")
            print(f"      EMA10: {analysis.get('ema10', 0):.4f} | EMA20: {analysis.get('ema20', 0):.4f}")
            print(f"      MACD Histogram: {analysis.get('macd_hist', 0):.4f}")
            print(f"      Confidence: {analysis.get('confidence', 0)*100:.1f}%")
        
        traded_amount = self.current_amount
        
        response = self.conn.buy_asset(asset, traded_amount, direction, expiration_minutes=1)
        
        if not response:
            print(f"   ❌ Trade execution failed")
            self._log(timestamp, asset, direction, traded_amount, 'error', 
                     balance, self.total_profit, self.consecutive_losses, 'execution_failed')
            return None
        
        print(f"   ⏳ Waiting for trade to close (65s)...")
        time.sleep(65)
        
        result_status = self.conn.check_trade_result(response)
        
        if result_status == 'win':
            payout = traded_amount * 0.80
            self.total_profit += payout
            self.consecutive_losses = 0
            self.current_amount = self.base_amount
            
            print(f"   ✅ WIN! Profit: ${payout:.2f} | Total: ${self.total_profit:.2f}")
            
            self._log(timestamp, asset, direction, traded_amount, 'win', 
                     balance, self.total_profit, 0, str(response))
        
        elif result_status == 'loss':
            self.total_profit -= traded_amount
            self.consecutive_losses += 1
            self.current_amount = round(traded_amount * self.martingale_multiplier, 2)
            
            print(f"   ❌ LOSS! -${traded_amount:.2f} | Total: ${self.total_profit:.2f}")
            print(f"   📈 Next amount: ${self.current_amount:.2f} (Step {self.consecutive_losses})")
            
            self._log(timestamp, asset, direction, traded_amount, 'loss', 
                     balance, self.total_profit, self.consecutive_losses, str(response))
        
        else:
            print(f"   ⚠️ Unknown result, treating as loss for safety")
            self.total_profit -= traded_amount
            self.consecutive_losses += 1
            self.current_amount = round(traded_amount * self.martingale_multiplier, 2)
            
            self._log(timestamp, asset, direction, traded_amount, 'unknown', 
                     balance, self.total_profit, self.consecutive_losses, str(response))
        
        self.trade_count += 1
        self._save_state()
        
        return result_status
    
    def _log(self, ts, asset, direction, amount, result, balance, profit, martingale_step, info=''):
        with open(self.logfile, 'a', newline='') as f:
            w = csv.writer(f)
            w.writerow([ts, asset, direction, amount, result, balance, profit, martingale_step, info])
    
    def get_stats(self):
        return {
            'current_amount': self.current_amount,
            'consecutive_losses': self.consecutive_losses,
            'total_profit': self.total_profit,
            'trade_count': self.trade_count,
            'profit_target': self.take_profit,
            'max_losses': self.max_losses
        }
