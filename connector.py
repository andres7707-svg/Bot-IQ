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
    """
    Return a list of OTC assets that are actually available/open.
    Strategy:
     - Prefer using self.Iq.get_all_open_time() (most reliable).
     - If that fails, fallback to older calls (get_all_ACTIVES_OPCODE).
     - As a last resort return sensible defaults.
    """
    try:
        otc_list = []

        # 1) Try get_all_open_time() first (preferred)
        all_open = None
        try:
            if hasattr(self.Iq, 'get_all_open_time'):
                all_open = self.Iq.get_all_open_time()
        except Exception:
            all_open = None

        if isinstance(all_open, dict):
            # The structure can vary by wrapper version, be flexible
            for key, info in all_open.items():
                # Build candidate normalized names
                candidates = [key, f"{key}-OTC", key.upper(), f"{key.upper()}-OTC"]
                # Inspect info: it may be a dict of timeframes -> { 'open': True/False } etc.
                found_open = False
                # check whether any nested entry declares open=True
                if isinstance(info, dict):
                    # If the dict itself has an 'open' key
                    if info.get('open') is True:
                        found_open = True
                    else:
                        # otherwise check nested dictionaries
                        for subv in info.values():
                            if isinstance(subv, dict) and subv.get('open') is True:
                                found_open = True
                                break
                # If we found 'open', normalize name to <PAIR>-OTC
                if found_open:
                    # prefer explicit -OTC form
                    name = f"{key}-OTC"
                    if name not in otc_list:
                        otc_list.append(name)

            # If we found items via get_all_open_time, return them (limit to avoid overload)
            if otc_list:
                return otc_list[:30]

        # 2) Fallback: try older API call get_all_ACTIVES_OPCODE
        try:
            if hasattr(self.Iq, 'get_all_ACTIVES_OPCODE'):
                actives = self.Iq.get_all_ACTIVES_OPCODE()
                if isinstance(actives, dict):
                    for pair in actives.keys():
                        name = f"{pair}-OTC"
                        if name not in otc_list:
                            otc_list.append(name)
                    if otc_list:
                        return otc_list[:30]
        except Exception:
            pass

        # 3) Final fallback: sensible defaults
        defaults = [
            'EURUSD-OTC','GBPUSD-OTC','USDJPY-OTC','EURJPY-OTC',
            'GBPJPY-OTC','AUDCAD-OTC','NZDUSD-OTC'
        ]
        return defaults

    except Exception as e:
        print("Error in get_all_assets:", e)
        # return safe defaults if anything goes wrong
        return ['EURUSD-OTC','GBPUSD-OTC','USDJPY-OTC','EURJPY-OTC']

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
    """
    Normaliza direction y realiza la compra.
    direction puede venir como 'CALL','call','Put','PUT' etc.
    Retorna el objeto respuesta que provea la API (o None).
    """
    # Normalize direction to 'call' or 'put'
    d = str(direction).strip().lower()
    if d in ('put', 'sell', 'down', 'p'):
        dir_norm = 'put'
    else:
        # default to 'call' for safety
        dir_norm = 'call'

    # try digital spot first (library-dependent)
    try:
        # many wrappers accept ('asset', amount, 'call'/'put', expiration_minutes)
        resp = None
        try:
            resp = self.Iq.buy_digital_spot(asset, amount, dir_norm, expiration_minutes)
            return resp
        except Exception:
            # fallback to classic buy (some wrappers use seconds for expiry)
            exp_sec = int(expiration_minutes * 60)
            if hasattr(self.Iq, 'buy'):
                try:
                    return self.Iq.buy(asset, amount, dir_norm, exp_sec)
                except Exception:
                    pass
            if hasattr(self.Iq, 'buy_option'):
                try:
                    return self.Iq.buy_option(asset, amount, dir_norm, exp_sec)
                except Exception:
                    pass
        return resp
    except Exception as e:
        print('Buy failed (connector.buy_asset):', e)
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
