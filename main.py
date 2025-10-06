import os
import sys
import time
import signal

# Asegura que el directorio donde está el script/exe esté en PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# base_dir apunta a la carpeta del exe cuando está empaquetado con PyInstaller
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# cargamos dotenv desde BASE_DIR (si existe .env empaquetado)
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Intentamos importar connector de la forma habitual; si falla, lo cargamos manualmente
try:
    import connector
except ModuleNotFoundError:
    import importlib.util
    connector_path = os.path.join(BASE_DIR, 'connector.py')
    if os.path.exists(connector_path):
        spec = importlib.util.spec_from_file_location("connector", connector_path)
        connector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(connector)
    else:
        # re-raise para que el error sea visible si realmente falta el archivo
        raise

# y ahora importamos la clase concreta
from connector import IQConnector

from strategy import AdvancedStrategy
from manager import TradeManager
import pandas as pd
import threading

load_dotenv()

EMAIL = os.getenv('IQ_EMAIL')
PASSWORD = os.getenv('IQ_PASSWORD')
TRADE_MODE = os.getenv('TRADE_MODE', 'PRACTICE')
BASE_AMOUNT = float(os.getenv('BASE_AMOUNT', 1))
MARTINGALE_MULTIPLIER = float(os.getenv('MARTINGALE_MULTIPLIER', 2.2))
TAKE_PROFIT = float(os.getenv('TAKE_PROFIT', 50))
START_BALANCE = float(os.getenv('START_BALANCE', 24.65))
MAX_LOSSES = int(os.getenv('MAX_LOSSES', 5))
TIMEFRAME = os.getenv('TIMEFRAME', '1m')
ASSETS_ENV = os.getenv('ASSETS', '')

TIMEFRAME_SEC = 60 if TIMEFRAME == '1m' else int(TIMEFRAME)
CANDLES_COUNT = 120

running = True

def signal_handler(sig, frame):
    global running
    running = False
    print('\n⚠️ Shutdown signal received, stopping bot...')

signal.signal(signal.SIGINT, signal_handler)

def df_from_candles(candles):
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles)
    for col in ['ts', 'open', 'high', 'low', 'close', 'volume']:
        if col not in df.columns:
            df[col] = None
    return df[['ts', 'open', 'high', 'low', 'close', 'volume']]

def reconnect(email, password, mode, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"🔄 Reconnection attempt {attempt + 1}/{max_retries}...")
            conn = IQConnector(email, password, mode)
            conn.connect()
            print(f"✅ Reconnected successfully")
            return conn
        except Exception as e:
            print(f"❌ Reconnection failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    return None

def main():
    global running
    
    if not EMAIL or not PASSWORD:
        print('❌ ERROR: Please configure IQ_EMAIL and IQ_PASSWORD in Replit Secrets')
        return
    
    print("=" * 70)
    print("🤖 IQ OPTION ADVANCED TRADING BOT - STARTING")
    print("=" * 70)
    print(f"📊 Configuration:")
    print(f"   Mode: {TRADE_MODE}")
    print(f"   Base Amount: ${BASE_AMOUNT}")
    print(f"   Martingale Multiplier: {MARTINGALE_MULTIPLIER}x")
    print(f"   Take Profit Target: ${TAKE_PROFIT}")
    print(f"   Max Consecutive Losses: {MAX_LOSSES}")
    print(f"   Timeframe: {TIMEFRAME}")
    print("=" * 70)
    
    conn = IQConnector(EMAIL, PASSWORD, TRADE_MODE)
    print('\n🔌 Connecting to IQ Option...')
    
    try:
        conn.connect()
        print('✅ Connected successfully!')
    except Exception as e:
        print(f'❌ Failed to connect: {e}')
        return
    
    try:
        balance = conn.Iq.get_balance()
        print(f'💰 Current Balance: ${balance:.2f}')
    except:
        balance = START_BALANCE
        print(f'💰 Starting Balance: ${balance:.2f}')
    
    otc_assets = conn.get_all_assets()
    
    if not otc_assets:
        if ASSETS_ENV:
            otc_assets = [a.strip() for a in ASSETS_ENV.split(',') if a.strip()]
        else:
            otc_assets = ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'EURJPY-OTC']
    
    print(f'\n📈 Monitoring {len(otc_assets)} OTC assets:')
    print(f'   {", ".join(otc_assets[:10])}')
    if len(otc_assets) > 10:
        print(f'   ... and {len(otc_assets) - 10} more')
    
    strategy = AdvancedStrategy()
    manager = TradeManager(
        conn,
        base_amount=BASE_AMOUNT,
        martingale_multiplier=MARTINGALE_MULTIPLIER,
        take_profit=TAKE_PROFIT,
        start_balance=START_BALANCE,
        max_losses=MAX_LOSSES
    )

    # --- función auxiliar para ejecutar trades en un hilo separado ---
    def execute_signal(asset, direction, balance, analysis):
        try:
            result = manager.execute_trade(asset, direction, balance, analysis)
            if result:
                pattern_closes = df['close'].tail(20).tolist()
                strategy.update_pattern_result(asset, pattern_closes, direction)
        except Exception as e:
            print(f"⚠️ Error ejecutando operación en {asset}: {e}")

    print('\n🚀 Starting main trading loop...\n')
    print('🔍 The bot will now scan for patterns and execute trades automatically')
    print('   Press Ctrl+C to stop\n')
    
    last_reconnect = time.time()
    scan_interval = 5
    
    while running:
        loop_start = time.time()
        
        should_stop, reason = manager.should_stop_trading()
        if should_stop:
            print(f'\n🛑 STOPPING: {reason}')
            stats = manager.get_stats()
            print(f"\n📊 Final Statistics:")
            print(f"   Total Trades: {stats['trade_count']}")
            print(f"   Total Profit: ${stats['total_profit']:.2f}")
            print(f"   Final Amount: ${stats['current_amount']:.2f}")
            break
        
        if time.time() - last_reconnect > 300:
            try:
                if not conn.Iq or not hasattr(conn.Iq, 'check_connect') or not conn.Iq.check_connect():
                    print('\n⚠️ Connection lost, attempting to reconnect...')
                    conn = reconnect(EMAIL, PASSWORD, TRADE_MODE)
                    if not conn:
                        print('❌ Could not reconnect, stopping bot')
                        break
                    last_reconnect = time.time()
            except:
                pass
        
        for asset in otc_assets:
            if not running:
                break
            
            try:
                candles = conn.get_candles(asset, timeframe_seconds=TIMEFRAME_SEC, count=CANDLES_COUNT)
                df = df_from_candles(candles)
                
                if df.empty or len(df) < 30:
                    time.sleep(0.3)
                    continue
                
                signal, analysis = strategy.analyze(df, asset=asset)
                
                if signal in ('call', 'put'):
                    print(f'\n🎯 SIGNAL DETECTED: {signal.upper()} on {asset}')

                    try:
                        balance = conn.Iq.get_balance()
                    except:
                        balance = START_BALANCE + manager.total_profit

                    # --- lanzar operación en un hilo separado ---
                    t = threading.Thread(
                        target=execute_signal,
                        args=(asset, signal, balance, analysis),
                        daemon=True
                    )
                    t.start()

                    # seguir escaneando otros pares sin esperar a que termine
                    time.sleep(1)

                    should_stop, reason = manager.should_stop_trading()
                    if should_stop:
                        print(f'\n🛑 STOPPING: {reason}')
                        break
                    
                    time.sleep(2)
            
            except Exception as e:
                print(f'⚠️ Error processing {asset}: {e}')
                time.sleep(0.5)
                continue
        
        elapsed = time.time() - loop_start
        if elapsed < scan_interval:
            time.sleep(scan_interval - elapsed)
    
    stats = manager.get_stats()
    print("\n" + "=" * 70)
    print("🏁 BOT STOPPED")
    print("=" * 70)
    print(f"📊 Session Statistics:")
    print(f"   Total Trades: {stats['trade_count']}")
    print(f"   Total Profit/Loss: ${stats['total_profit']:.2f}")
    print(f"   Consecutive Losses: {stats['consecutive_losses']}")
    print(f"   Current Trade Amount: ${stats['current_amount']:.2f}")
    print("=" * 70)

try:
    main()
except Exception as e:
    import traceback
    print('ERROR:', e)
    traceback.print_exc()
    input("Presiona ENTER para salir...")

if __name__ == '__main__':
    main()
