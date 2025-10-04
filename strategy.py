# strategy.py - placeholder strategy for 1m. Replace later with desired rules.
import pandas as pd
import numpy as np

def rsi_simple(series, window=7):
    diff = series.diff()
    up = diff.clip(lower=0).rolling(window).mean()
    down = (-diff.clip(upper=0)).rolling(window).mean()
    rs = up / (down + 1e-9)
    return 100 - (100 / (1 + rs))

class Strategies:
    @staticmethod
    def simple_otc_1m(df):
        # Conservative example: EMA crossover + RSI filter + volume spike
        s = df.copy().reset_index(drop=True)
        if len(s) < 30:
            return 'hold'
        close = s['close'].astype(float)
        vol = s['volume'].astype(float).fillna(0.0)
        ema5 = close.ewm(span=5, adjust=False).mean()
        ema13 = close.ewm(span=13, adjust=False).mean()
        rsi7 = rsi_simple(close, window=7)
        vol_avg5 = vol.rolling(5).mean().bfill()
        vol_spike = vol.iloc[-1] > 1.5 * vol_avg5.iloc[-1]
        last = s.iloc[-1]
        bullish = (ema5.iloc[-1] > ema13.iloc[-1]) and (ema5.iloc[-2] <= ema13.iloc[-2])
        bearish = (ema5.iloc[-1] < ema13.iloc[-1]) and (ema5.iloc[-2] >= ema13.iloc[-2])
        if bullish and rsi7.iloc[-1] > 55 and vol_spike:
            return 'call'
        if bearish and rsi7.iloc[-1] < 45 and vol_spike:
            return 'put'
        return 'hold'
