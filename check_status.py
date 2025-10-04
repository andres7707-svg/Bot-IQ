#!/usr/bin/env python3
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("IQ OPTION TRADING BOT - STATUS CHECK")
print("=" * 60)

print(f"\n📅 Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

mode = os.getenv('MODE', 'PRACTICE')
print(f"\n🔧 Configuration:")
print(f"   Mode: {mode}")
print(f"   Risk per trade: {os.getenv('RISK_PER_TRADE', '0.01')}")
print(f"   Min stake: ${os.getenv('MIN_STAKE', '1.0')}")
print(f"   Recovery multiplier: {os.getenv('RECOVERY_MULTIPLIER', '2.0')}x")
print(f"   Max recovery steps: {os.getenv('MAX_RECOVERY_STEPS', '3')}")
print(f"   Max trades/min: {os.getenv('MAX_TRADES_PER_MIN', '3')}")

if os.path.exists('trades_log.csv'):
    with open('trades_log.csv', 'r') as f:
        reader = csv.DictReader(f)
        trades = list(reader)
    
    if trades:
        print(f"\n📊 Trade Statistics:")
        print(f"   Total trades: {len(trades)}")
        wins = sum(1 for t in trades if t.get('result') == 'win')
        losses = sum(1 for t in trades if t.get('result') == 'loss')
        print(f"   Wins: {wins}")
        print(f"   Losses: {losses}")
        if wins + losses > 0:
            win_rate = (wins / (wins + losses)) * 100
            print(f"   Win rate: {win_rate:.1f}%")
        
        print(f"\n📝 Recent Trades:")
        for trade in trades[-5:]:
            ts = trade.get('ts', 'N/A')[:19] if trade.get('ts') else 'N/A'
            asset = trade.get('asset', 'N/A')
            direction = trade.get('dir', 'N/A')
            result = trade.get('result', 'N/A')
            amount = trade.get('amount', 'N/A')
            print(f"   {ts} | {asset} | {direction.upper()} | ${amount} | {result.upper()}")
    else:
        print(f"\n📊 No trades executed yet")
        print(f"   The bot is scanning the market for trading signals...")
else:
    print(f"\n📊 No trade log file found")
    print(f"   The bot has not executed any trades yet")

print("\n" + "=" * 60)
print("💡 Tips:")
print("   - Bot runs in PRACTICE mode by default (safe for testing)")
print("   - Check console logs for real-time activity")
print("   - Monitor trades_log.csv for trade history")
print("   - API connection errors are normal - the bot retries automatically")
print("=" * 60)
