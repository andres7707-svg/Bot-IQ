# connector.py (supports digital & binary attempts + check result)
import time, traceback

from iqoptionapi.stable_api import IQ_Option

class IQConnector:
    def __init__(self, email, password, mode='PRACTICE'):
        self.email = email
        self.password = password
        self.mode = mode
        self.Iq = None
        self.asset_type_cache = {}

    def connect(self):
        self.Iq = IQ_Option(self.email, self.password)
        ok = self.Iq.connect()
        if not ok:
            raise RuntimeError("No se pudo conectar a IQ Option")
        if self.mode.upper() == 'PRACTICE':
            try:
                self.Iq.change_balance('PRACTICE')
            except Exception:
                pass
        else:
            try:
                self.Iq.change_balance('REAL')
            except Exception:
                pass
        return True

    def get_all_assets(self):
        try:
            actives = self.Iq.get_all_ACTIVES_OPCODE()
            if not actives:
                return ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'EURJPY-OTC']
            
            otc_list = []
            for pair_name in actives.keys():
                otc_name = f"{pair_name}-OTC"
                otc_list.append(otc_name)
                self.asset_type_cache[otc_name] = 'digital'
            
            if otc_list:
                return otc_list[:10]
            else:
                return ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'EURJPY-OTC']
        except Exception as e:
            print(f'Error getting assets: {e}')
            return ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'EURJPY-OTC']

    def get_candles(self, asset, timeframe_seconds=60, count=100):
        to = int(time.time())
        try:
            candles = self.Iq.get_candles(asset, timeframe_seconds, count, to)
            if not candles:
                return []
            result = []
            for c in candles:
                result.append({
                    'ts': c.get('from', int(time.time())),
                    'open': c.get('open'),
                    'close': c.get('close'),
                    'high': c.get('max', c.get('high')),
                    'low': c.get('min', c.get('low')),
                    'volume': c.get('volume', 0)
                })
            return result
        except Exception as e:
            time.sleep(0.5)
            return []

    def detect_asset_type(self, asset):
        if asset in self.asset_type_cache:
            return self.asset_type_cache[asset]
        try:
            allm = getattr(self.Iq, 'get_all_open_time', None)
            if callable(allm):
                data = self.Iq.get_all_open_time()
                info = data.get(asset)
                if isinstance(info, dict):
                    if any('digital' in k.lower() for k in info.keys()):
                        self.asset_type_cache[asset] = 'digital'
                        return 'digital'
                    if any(('classic' in k.lower() or 'binary' in k.lower() or 'option' in k.lower()) for k in info.keys()):
                        self.asset_type_cache[asset] = 'binary'
                        return 'binary'
        except Exception:
            pass
        self.asset_type_cache[asset] = None
        return None

    def buy_asset(self, asset, amount, direction, expiration_minutes=1):
        atype = self.detect_asset_type(asset)
        # try digital first if known
        if atype == 'digital':
            try:
                return self.Iq.buy_digital_spot(asset, amount, direction, expiration_minutes)
            except Exception as e:
                print('Error buy_digital_spot:', e)
        if atype == 'binary':
            try:
                exp_sec = int(expiration_minutes * 60)
                if hasattr(self.Iq, 'buy'):
                    return self.Iq.buy(asset, amount, direction, exp_sec)
                elif hasattr(self.Iq, 'buy_option'):
                    return self.Iq.buy_option(asset, amount, direction, exp_sec)
            except Exception as e:
                print('Error buy binary classic:', e)
        # fallback try digital then binary
        try:
            return self.Iq.buy_digital_spot(asset, amount, direction, expiration_minutes)
        except Exception as e1:
            try:
                exp_sec = int(expiration_minutes * 60)
                if hasattr(self.Iq, 'buy'):
                    return self.Iq.buy(asset, amount, direction, exp_sec)
                elif hasattr(self.Iq, 'buy_option'):
                    return self.Iq.buy_option(asset, amount, direction, exp_sec)
            except Exception as e2:
                print('Error fallback buy attempts:')
                traceback.print_exc()
                return None

    def check_trade_result(self, response):
        """Attempt to determine if a trade (response) resulted in profit or loss.
        Many wrappers return a dict with 'id' or 'position_id' or a boolean.
        We'll attempt several lookups. Returns: 'win', 'loss', or None if unknown."""
        try:
            if not response:
                return None
            # if response is boolean True, cannot know result
            if isinstance(response, bool):
                return None
            # try extract id
            trade_id = None
            if isinstance(response, dict):
                trade_id = response.get('id') or response.get('position_id') or response.get('order_id')
            # if we have an id, try to query history endpoints
            if trade_id:
                try:
                    # many wrappers provide get_digital_position_history or get_positions
                    if hasattr(self.Iq, 'get_digital_position_history'):
                        history = self.Iq.get_digital_position_history(trade_id)
                        # structure may vary; inspect and deduce
                        # This is best-effort; may need adaptation for your wrapper version.
                        if history and isinstance(history, dict):
                            # attempt simple heuristic
                            for k,v in history.items():
                                if isinstance(v, dict):
                                    if v.get('id') == trade_id:
                                        profit = v.get('profit') or v.get('win')
                                        if profit is not None:
                                            return 'win' if float(profit) > 0 else 'loss'
                        # else unable to deduce
                except Exception:
                    pass
            # If no id or unable, try to check recent closed positions
            try:
                if hasattr(self.Iq, 'get_positions'):
                    recent = self.Iq.get_positions()
                    # inspect recent for matching amount & direction
                    # Not reliable across wrapper versions
                    return None
            except Exception:
                pass
        except Exception:
            pass
        return None
