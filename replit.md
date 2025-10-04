# IQ Option OTC Trading Bot

## Overview
Automated trading bot for IQ Option OTC (Over-The-Counter) markets. Designed for 1-minute timeframe trading with recovery strategy logic.

**⚠️ IMPORTANT WARNINGS:**
- Currently configured to run in **PRACTICE (demo) mode** by default for safety
- Uses martingale/recovery strategy which increases risk
- This is an unofficial API for educational purposes only
- Should NOT be used on real trading accounts without extensive testing

## Project Status
- **Current State**: Bot configured and ready to run
- **Dependencies**: All Python packages installed
- **IQ API Library**: Using Lu-Yi-Hsun fork (v6.8.9.1) from GitHub for stable_api support
- **Workflow**: Trading Bot workflow configured to run `python main.py`

## Architecture

### Core Components
1. **main.py** - Main orchestrator that scans OTC assets and triggers trading sequences
2. **connector.py** - Handles IQ Option API connection and trade execution (digital/binary options)
3. **strategy.py** - Trading strategy logic (EMA crossover + RSI filter + volume spike)
4. **manager.py** - Trade management with sequential recovery logic and stake sizing

### Trading Logic
- Monitors OTC assets for trading signals
- Uses conservative strategy: EMA crossover (5/13) + RSI filter + volume spike detection
- Sequential trades: 
  - Win → next trade uses same stake
  - Loss → stake increases by RECOVERY_MULTIPLIER (default 2.0x) to attempt recovery
  - Stops after MAX_RECOVERY_STEPS (default 3) or MAX_SEQUENTIAL_TRADES (default 10)
- Logs all trades to `trades_log.csv`

### Configuration (Environment Variables)
Required:
- `IQ_EMAIL` - IQ Option account email (SECRET - not provided yet)
- `IQ_PASSWORD` - IQ Option account password (SECRET - not provided yet)

Optional (with defaults):
- `MODE=PRACTICE` - PRACTICE or REAL
- `ASSETS=` - Comma-separated OTC assets (empty = auto-detect)
- `RISK_PER_TRADE=0.01` - Risk per trade as fraction of balance
- `TIMEFRAME_SEC=60` - Candle timeframe in seconds
- `CANDLES=120` - Number of candles to analyze
- `MAX_TRADES_PER_MIN=3` - Rate limit
- `MAX_LOSSES_IN_ROW=5` - Stop after N consecutive losses
- `COOLDOWN_AFTER_LOSS_SEC=60` - Cooldown period after loss
- `MIN_STAKE=1.0` - Minimum stake amount
- `RECOVERY_MULTIPLIER=2.0` - Stake multiplier after loss
- `MAX_RECOVERY_STEPS=3` - Max recovery attempts
- `MAX_SEQUENTIAL_TRADES=10` - Max trades in one sequence

## Recent Changes
- **2025-10-04**: Initial project setup
  - Extracted bot from uploaded ZIP file
  - Installed Python dependencies
  - Fixed iqoptionapi package (switched from PyPI v0.5 to GitHub v6.8.9.1)
  - Configured Trading Bot workflow
  - Awaiting IQ_EMAIL and IQ_PASSWORD secrets from user

## Next Steps
1. User needs to provide IQ_EMAIL and IQ_PASSWORD secrets
2. Test bot in PRACTICE mode
3. Monitor trades_log.csv for results
4. Fine-tune strategy parameters if needed

## Dependencies
- Python 3.11
- iqoptionapi (6.8.9.1 from GitHub Lu-Yi-Hsun fork)
- pandas, numpy, python-dotenv, ta, pyinstaller
- websocket-client==0.56

## Additional Files
- `.env.example` - Template for environment variables
- `README.md` - Original project documentation
- `.github/workflows/build-windows.yml` - GitHub Actions workflow for building Windows .exe
