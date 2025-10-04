import pandas as pd
import numpy as np
from collections import deque
import hashlib

class PatternMatcher:
    def __init__(self, max_history=500):
        self.history = {}
        self.max_history = max_history
    
    def normalize_pattern(self, candles):
        if len(candles) < 2:
            return []
        closes = [c for c in candles]
        min_c, max_c = min(closes), max(closes)
        if max_c == min_c:
            return [0.5] * len(closes)
        return [(c - min_c) / (max_c - min_c) for c in closes]
    
    def pattern_hash(self, normalized):
        pattern_str = ','.join([f"{v:.3f}" for v in normalized])
        return hashlib.md5(pattern_str.encode()).hexdigest()[:8]
    
    def add_pattern(self, asset, candles, result):
        if asset not in self.history:
            self.history[asset] = deque(maxlen=self.max_history)
        
        normalized = self.normalize_pattern(candles)
        if normalized:
            self.history[asset].append({
                'pattern': normalized,
                'result': result,
                'hash': self.pattern_hash(normalized)
            })
    
    def find_similar_patterns(self, asset, current_candles, threshold=0.15):
        if asset not in self.history or len(self.history[asset]) == 0:
            return []
        
        current_norm = self.normalize_pattern(current_candles)
        if not current_norm:
            return []
        
        matches = []
        for hist in self.history[asset]:
            if len(hist['pattern']) != len(current_norm):
                continue
            
            diff = sum(abs(a - b) for a, b in zip(current_norm, hist['pattern'])) / len(current_norm)
            if diff < threshold:
                matches.append({
                    'similarity': 1 - diff,
                    'result': hist['result']
                })
        
        return sorted(matches, key=lambda x: x['similarity'], reverse=True)[:5]


class CandlePatterns:
    @staticmethod
    def is_hammer(o, h, l, c):
        body = abs(c - o)
        lower_shadow = min(o, c) - l
        upper_shadow = h - max(o, c)
        
        if body == 0:
            return False
        
        return (lower_shadow > 2 * body and 
                upper_shadow < body and 
                c > o)
    
    @staticmethod
    def is_shooting_star(o, h, l, c):
        body = abs(c - o)
        lower_shadow = min(o, c) - l
        upper_shadow = h - max(o, c)
        
        if body == 0:
            return False
        
        return (upper_shadow > 2 * body and 
                lower_shadow < body and 
                c < o)
    
    @staticmethod
    def is_engulfing_bullish(prev_o, prev_c, o, c):
        return (prev_c < prev_o and 
                c > o and 
                o < prev_c and 
                c > prev_o)
    
    @staticmethod
    def is_engulfing_bearish(prev_o, prev_c, o, c):
        return (prev_c > prev_o and 
                c < o and 
                o > prev_c and 
                c < prev_o)
    
    @staticmethod
    def is_doji(o, h, l, c):
        body = abs(c - o)
        total_range = h - l
        if total_range == 0:
            return False
        return body / total_range < 0.1


class Indicators:
    @staticmethod
    def ema(series, period):
        return series.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0).rolling(window=period).mean()
        loss = (-delta.clip(upper=0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(series, fast=12, slow=26, signal=9):
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def support_resistance(highs, lows, window=20):
        recent_highs = highs.rolling(window).max()
        recent_lows = lows.rolling(window).min()
        return recent_lows.iloc[-1], recent_highs.iloc[-1]


class AdvancedStrategy:
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
    
    def analyze(self, df, asset=None):
        if df.empty or len(df) < 30:
            return 'hold', None
        
        df = df.copy().reset_index(drop=True)
        
        close = df['close'].astype(float)
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        open_price = df['open'].astype(float)
        
        ema10 = Indicators.ema(close, 10)
        ema20 = Indicators.ema(close, 20)
        rsi14 = Indicators.rsi(close, 14)
        macd_line, signal_line, histogram = Indicators.macd(close)
        
        support, resistance = Indicators.support_resistance(high, low, 20)
        
        last_close = close.iloc[-1]
        last_open = open_price.iloc[-1]
        last_high = high.iloc[-1]
        last_low = low.iloc[-1]
        
        prev_close = close.iloc[-2]
        prev_open = open_price.iloc[-2]
        
        hammer = CandlePatterns.is_hammer(last_open, last_high, last_low, last_close)
        shooting_star = CandlePatterns.is_shooting_star(last_open, last_high, last_low, last_close)
        bullish_engulfing = CandlePatterns.is_engulfing_bullish(prev_open, prev_close, last_open, last_close)
        bearish_engulfing = CandlePatterns.is_engulfing_bearish(prev_open, prev_close, last_open, last_close)
        
        ema_crossover_bullish = ema10.iloc[-1] > ema20.iloc[-1] and ema10.iloc[-2] <= ema20.iloc[-2]
        ema_crossover_bearish = ema10.iloc[-1] < ema20.iloc[-1] and ema10.iloc[-2] >= ema20.iloc[-2]
        
        rsi_oversold = rsi14.iloc[-1] < 30
        rsi_overbought = rsi14.iloc[-1] > 70
        
        macd_bullish = histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0
        macd_bearish = histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0
        
        pattern_closes = close.tail(20).tolist()
        similar_patterns = []
        if asset:
            similar_patterns = self.pattern_matcher.find_similar_patterns(asset, pattern_closes)
        
        signal = 'hold'
        confidence = 0
        
        bullish_score = 0
        bearish_score = 0
        
        if hammer or bullish_engulfing:
            bullish_score += 2
        if ema_crossover_bullish:
            bullish_score += 2
        if rsi_oversold:
            bullish_score += 1
        if macd_bullish:
            bullish_score += 2
        if last_close > ema20.iloc[-1]:
            bullish_score += 1
        if last_close <= support * 1.01:
            bullish_score += 1
        
        if shooting_star or bearish_engulfing:
            bearish_score += 2
        if ema_crossover_bearish:
            bearish_score += 2
        if rsi_overbought:
            bearish_score += 1
        if macd_bearish:
            bearish_score += 2
        if last_close < ema20.iloc[-1]:
            bearish_score += 1
        if last_close >= resistance * 0.99:
            bearish_score += 1
        
        if similar_patterns:
            top_match = similar_patterns[0]
            if top_match['similarity'] > 0.85:
                if top_match['result'] == 'call':
                    bullish_score += 2
                elif top_match['result'] == 'put':
                    bearish_score += 2
        
        if bullish_score >= 5 and bullish_score > bearish_score:
            signal = 'call'
            confidence = min(bullish_score / 10.0, 1.0)
        elif bearish_score >= 5 and bearish_score > bullish_score:
            signal = 'put'
            confidence = min(bearish_score / 10.0, 1.0)
        
        analysis = {
            'ema10': ema10.iloc[-1],
            'ema20': ema20.iloc[-1],
            'rsi': rsi14.iloc[-1],
            'macd_hist': histogram.iloc[-1],
            'support': support,
            'resistance': resistance,
            'bullish_score': bullish_score,
            'bearish_score': bearish_score,
            'confidence': confidence
        }
        
        return signal, analysis
    
    def update_pattern_result(self, asset, candles, result):
        self.pattern_matcher.add_pattern(asset, candles, result)
