#!/usr/bin/env python3
import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("🤖 IQ OPTION ADVANCED TRADING BOT - STATUS CHECK")
print("=" * 80)

print(f"\n📅 Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

mode = os.getenv('TRADE_MODE', 'PRACTICE')
print(f"\n⚙️ Configuration:")
print(f"   Mode: {mode}")
print(f"   Base Amount: ${os.getenv('BASE_AMOUNT', '1')}")
print(f"   Martingale Multiplier: {os.getenv('MARTINGALE_MULTIPLIER', '2.2')}x")
print(f"   Take Profit Target: ${os.getenv('TAKE_PROFIT', '50')}")
print(f"   Max Consecutive Losses: {os.getenv('MAX_LOSSES', '5')}")
print(f"   Timeframe: {os.getenv('TIMEFRAME', '1m')}")

if os.path.exists('bot_state.json'):
    with open('bot_state.json', 'r') as f:
        state = json.load(f)
    
    print(f"\n💾 Bot State (Last Update: {state.get('last_update', 'N/A')[:19]}):")
    print(f"   Current Trade Amount: ${state.get('current_amount', 0):.2f}")
    print(f"   Consecutive Losses: {state.get('consecutive_losses', 0)}")
    print(f"   Total Profit/Loss: ${state.get('total_profit', 0):.2f}")
    print(f"   Total Trades: {state.get('trade_count', 0)}")
else:
    print(f"\n💾 No saved state found (bot hasn't started trading yet)")

if os.path.exists('trades_log.csv'):
    with open('trades_log.csv', 'r') as f:
        reader = csv.DictReader(f)
        trades = list(reader)
    
    if trades:
        print(f"\n📊 Trade Statistics:")
        print(f"   Total Trades: {len(trades)}")
        
        wins = sum(1 for t in trades if t.get('result') == 'win')
        losses = sum(1 for t in trades if t.get('result') == 'loss')
        
        print(f"   Wins: {wins} ✅")
        print(f"   Losses: {losses} ❌")
        
        if wins + losses > 0:
            win_rate = (wins / (wins + losses)) * 100
            print(f"   Win Rate: {win_rate:.1f}%")
        
        if trades:
            last_trade = trades[-1]
            last_profit = float(last_trade.get('profit', 0))
            print(f"   Current P/L: ${last_profit:.2f}")
        
        print(f"\n📝 Recent Trades (Last 5):")
        for trade in trades[-5:]:
            ts = trade.get('timestamp', 'N/A')[:19] if trade.get('timestamp') else 'N/A'
            asset = trade.get('asset', 'N/A')
            direction = trade.get('direction', 'N/A')
            result = trade.get('result', 'N/A')
            amount = trade.get('amount', 'N/A')
            profit = trade.get('profit', 'N/A')
            step = trade.get('martingale_step', 'N/A')
            
            emoji = '✅' if result == 'win' else '❌' if result == 'loss' else '⚠️'
            print(f"   {emoji} {ts} | {asset:12} | {direction.upper():4} | ${amount:6} | Step {step} | P/L: ${profit}")
    else:
        print(f"\n📊 No trades executed yet")
        print(f"   The bot is scanning for high-probability setups...")
else:
    print(f"\n📊 No trade log found")
    print(f"   The bot hasn't executed any trades yet")

print("\n" + "=" * 80)
print("💡 Advanced Features Active:")
print("   ✓ Candlestick Pattern Recognition (Hammer, Shooting Star, Engulfing, Doji)")
print("   ✓ Multi-Indicator Analysis (EMA 10/20, RSI 14, MACD)")
print("   ✓ Support/Resistance Detection")
print("   ✓ Historical Pattern Matching")
print("   ✓ Martingale Recovery System")
print("   ✓ Auto Take-Profit & Max Loss Protection")
print("   ✓ State Persistence (Resume after crash)")
print("=" * 80)
