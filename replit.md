# IQ Option Advanced Trading Bot

## Overview
Fully automated trading bot for IQ Option OTC markets with advanced pattern recognition, multi-indicator analysis, and intelligent money management.

**⚠️ IMPORTANT WARNINGS:**
- Runs in **PRACTICE (demo) mode** by default for safety
- Uses martingale recovery strategy which increases risk exponentially
- This is an unofficial API for educational purposes only
- Should NOT be used on real trading accounts without extensive testing

## Project Status
- **Current State**: Bot fully reconfigured and running
- **Mode**: PRACTICE (Demo account: $24.65)
- **Assets**: Monitoring 10 OTC pairs automatically
- **Dependencies**: All packages installed and working

## Advanced Features

### 🎯 Strategy Components
1. **Candlestick Pattern Recognition**
   - Hammer (bullish reversal)
   - Shooting Star (bearish reversal)
   - Bullish/Bearish Engulfing
   - Doji (indecision)

2. **Multi-Indicator Analysis**
   - EMA 10/20 Crossover (trend detection)
   - RSI 14 (overbought/oversold at 70/30)
   - MACD Histogram (momentum confirmation)

3. **Structural Analysis**
   - Support/Resistance Detection (20-period)
   - Historical Pattern Matching
   - Learns from past trades

4. **Signal Scoring System**
   - Combines patterns + indicators + historical matches
   - Minimum score of 5/10 required for entry
   - Confidence-based execution

### 💰 Money Management
- **Martingale System**: Increases stake after loss by configurable multiplier
- **Take Profit**: Auto-stops when target profit reached
- **Max Loss Protection**: Stops after N consecutive losses
- **State Persistence**: Resumes from last state after crash

## Configuration (Environment Variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `IQ_EMAIL` | - | IQ Option account email (SECRET) |
| `IQ_PASSWORD` | - | IQ Option account password (SECRET) |
| `TRADE_MODE` | PRACTICE | PRACTICE or REAL |
| `BASE_AMOUNT` | 1 | Initial trade amount ($) |
| `MARTINGALE_MULTIPLIER` | 2.2 | Stake multiplier after loss |
| `TAKE_PROFIT` | 50 | Target profit in $ |
| `START_BALANCE` | 24.65 | Starting balance |
| `MAX_LOSSES` | 5 | Max consecutive losses before stop |
| `TIMEFRAME` | 1m | Candle timeframe |
| `ASSETS` | (auto) | Comma-separated OTC assets |

## Architecture

### Core Files
1. **main.py** - Main orchestrator with auto-reconnection and stop conditions
2. **strategy.py** - Advanced pattern recognition and indicator analysis
   - `PatternMatcher` class: Historical pattern matching with similarity detection
   - `CandlePatterns` class: Candlestick pattern recognition
   - `Indicators` class: EMA, RSI, MACD, Support/Resistance
   - `AdvancedStrategy` class: Combines all analysis with scoring system

3. **manager.py** - Trade execution and money management
   - Martingale progression system
   - State persistence (bot_state.json)
   - Take profit / max loss logic
   - Accurate profit/loss accounting

4. **connector.py** - IQ Option API connection
   - Handles digital/binary options
   - Auto-detects OTC assets
   - Error handling and delays

### Data Files
- `trades_log.csv` - Complete trade history with P/L tracking
- `bot_state.json` - Current bot state (resume after crash)

## Trade Cycle Logic

1. **Entry Signal Detection**
   - Scans all OTC assets every 5 seconds
   - Analyzes last 120 candles
   - Calculates pattern score (bullish/bearish)
   - Executes if score ≥ 5 and conditions align

2. **Trade Execution**
   - Places trade with current stake amount
   - Waits 65s for 1-minute trade to close
   - Checks result (win/loss/unknown)

3. **Post-Trade Actions**
   - **WIN**: Add 80% profit, reset stake to BASE_AMOUNT
   - **LOSS**: Subtract stake, multiply stake by MARTINGALE_MULTIPLIER
   - Update pattern history with result
   - Save state to disk
   - Check stop conditions

4. **Stopping Conditions**
   - Total profit ≥ TAKE_PROFIT → Stop with success
   - Consecutive losses ≥ MAX_LOSSES → Stop for safety
   - Manual stop (Ctrl+C)

## Recent Changes
- **2025-10-04**: Complete bot reconfiguration
  - ✅ Implemented advanced candlestick pattern recognition
  - ✅ Added multi-indicator analysis (EMA, RSI, MACD)
  - ✅ Built historical pattern matching system
  - ✅ Created new martingale money management system
  - ✅ Added take profit and max loss protection
  - ✅ Implemented state persistence for crash recovery
  - ✅ Added auto-reconnection logic
  - ✅ Fixed profit accounting bug (architect-reviewed)
  - ✅ Bot running in PRACTICE mode

## How to Use

### Check Bot Status
```bash
python check_bot_status.py
```

### View Trade Log
```bash
cat trades_log.csv
```

### Monitor Live Activity
Check the console output in Replit workflows

### Modify Configuration
Update environment variables in Replit Secrets panel

## Known Issues & Limitations
1. **API Connection Stability**: IQ Option API can be unstable with frequent requests
2. **OTC Market Hours**: Markets have specific hours; errors occur when closed
3. **Conservative Strategy**: High entry requirements mean fewer but higher-quality trades
4. **Martingale Risk**: Can quickly increase losses - always test in PRACTICE first

## Safety Recommendations
1. ✅ **Test Extensively**: Run in PRACTICE mode for days/weeks
2. ✅ **Start Small**: Use minimal BASE_AMOUNT when going live
3. ✅ **Monitor Closely**: Check logs and performance regularly
4. ✅ **Set Limits**: Configure reasonable TAKE_PROFIT and MAX_LOSSES
5. ⚠️ **Never Risk More**: Than you can afford to lose

## Dependencies
- Python 3.11
- iqoptionapi==6.8.9.1 (GitHub Lu-Yi-Hsun fork)
- pandas, numpy, python-dotenv
- websocket-client==0.56

---

**Bot Status**: ✅ RUNNING in PRACTICE mode with advanced pattern recognition
