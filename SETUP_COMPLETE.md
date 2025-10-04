# ✅ IQ Option OTC Trading Bot - Setup Complete!

## 🎯 Current Status
Your trading bot is **UP and RUNNING** in **PRACTICE MODE** 🟢

- **Account Balance**: $24.65 (Practice/Demo account)
- **Mode**: PRACTICE (safe for testing)
- **Assets Monitored**: 10 OTC pairs (EURUSD-OTC, GBPUSD-OTC, etc.)
- **Status**: Actively scanning market for signals

## 📋 What's Been Set Up

### ✅ Completed
1. **Dependencies Installed**: All Python packages installed
2. **API Fixed**: Upgraded to working version (GitHub v6.8.9.1)
3. **Credentials Added**: Your IQ Option login configured securely
4. **Bot Running**: Trading bot workflow is active
5. **Assets Configured**: 10 OTC markets being monitored
6. **Trade Logging**: trades_log.csv created for tracking

### 📊 Bot Features
- **Strategy**: EMA crossover (5/13) + RSI filter + volume spike detection
- **Risk Management**: 1% risk per trade by default
- **Recovery System**: Martingale strategy (2x multiplier on loss)
- **Safety Limits**: Max 3 recovery steps, max 5 losses in a row before stopping

## 🚀 How to Use

### Check Bot Status
```bash
python check_status.py
```

### View Trade History
```bash
cat trades_log.csv
```

### Monitor Live Activity
Check the console output in the Replit workspace (workflow logs)

## ⚙️ Configuration

All settings are controlled via environment variables:

| Variable | Current Value | Description |
|----------|---------------|-------------|
| MODE | PRACTICE | PRACTICE or REAL |
| RISK_PER_TRADE | 0.01 | Risk 1% of balance per trade |
| MIN_STAKE | 1.0 | Minimum $1 bet |
| RECOVERY_MULTIPLIER | 2.0 | Double stake after loss |
| MAX_RECOVERY_STEPS | 3 | Max 3 recovery attempts |
| MAX_TRADES_PER_MIN | 3 | Rate limit |
| MAX_LOSSES_IN_ROW | 5 | Stop after 5 consecutive losses |

To modify: Go to Replit Secrets panel or set environment variables

## ⚠️ Important Notes

### Known Limitations
1. **API Connection Issues**: The IQ Option API can be unstable. You'll see "error get_candles need reconnect" messages - this is normal. The bot retries automatically.

2. **OTC Market Hours**: OTC markets have specific operating hours. Connection errors may occur when markets are closed.

3. **Conservative Strategy**: The current strategy is very selective (needs EMA crossover + RSI confirmation + volume spike). This means fewer trades but potentially higher quality signals.

### Safety Warnings
- ⚠️ **Martingale Risk**: The recovery system can increase losses quickly
- ⚠️ **Test First**: Always test in PRACTICE mode extensively
- ⚠️ **Monitor Closely**: Check the bot regularly, especially with real money
- ⚠️ **Start Small**: Use small MIN_STAKE values when switching to REAL mode

## 🔧 Troubleshooting

### Bot not executing trades?
- This is normal - the strategy is conservative and waits for strong signals
- Markets may be closed or low volatility
- Check console logs for "Signal call/put on..." messages

### Too many connection errors?
- Reduce the number of assets monitored
- Set ASSETS environment variable to fewer pairs: `EURUSD-OTC,GBPUSD-OTC`

### Want to modify strategy?
- Edit `strategy.py` - the `simple_otc_1m()` function
- Current logic: EMA crossover + RSI filter + volume confirmation

## 📝 Next Steps

1. **Monitor Performance**: Let it run in PRACTICE mode and check trades_log.csv
2. **Adjust Parameters**: Fine-tune risk settings based on results
3. **Optimize Strategy**: Modify strategy.py if needed
4. **Go Live** (Optional): Only after extensive testing, set MODE=REAL

## 🛠️ Files Overview

- `main.py` - Main orchestrator
- `connector.py` - IQ Option API connection
- `strategy.py` - Trading strategy logic
- `manager.py` - Trade & risk management
- `trades_log.csv` - Trade history
- `check_status.py` - Status checker script

---

**Your bot is ready to trade!** 🤖📈

Remember: This is for educational purposes. Trade responsibly and never risk more than you can afford to lose.
