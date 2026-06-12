from SmartApi import SmartConnect
import pyotp
import time
import pandas as pd
from datetime import datetime, timedelta
import os

API_KEY = os.environ['API_KEY']
CLIENT_ID = os.environ['CLIENT_ID']
PASSWORD = os.environ['PASSWORD']
TOTP_SECRET = os.environ['TOTP_SECRET']

STOCKS = [
    {"symbol": "ADANIENT-EQ",   "token": "25",    "name": "ADANIENT"},
    {"symbol": "ADANIPORTS-EQ", "token": "15083", "name": "ADANIPORTS"},
    {"symbol": "APOLLOHOSP-EQ", "token": "157",   "name": "APOLLOHOSP"},
    {"symbol": "ASIANPAINT-EQ", "token": "236",   "name": "ASIANPAINT"},
    {"symbol": "AXISBANK-EQ",   "token": "5900",  "name": "AXISBANK"},
    {"symbol": "BAJAJ-AUTO-EQ", "token": "16669", "name": "BAJAJ-AUTO"},
    {"symbol": "BAJFINANCE-EQ", "token": "317",   "name": "BAJFINANCE"},
    {"symbol": "BAJAJFINSV-EQ", "token": "16675", "name": "BAJAJFINSV"},
    {"symbol": "BPCL-EQ",       "token": "526",   "name": "BPCL"},
    {"symbol": "BHARTIARTL-EQ", "token": "10604", "name": "BHARTIARTL"},
    {"symbol": "BRITANNIA-EQ",  "token": "547",   "name": "BRITANNIA"},
    {"symbol": "CIPLA-EQ",      "token": "694",   "name": "CIPLA"},
    {"symbol": "COALINDIA-EQ",  "token": "20374", "name": "COALINDIA"},
    {"symbol": "DIVISLAB-EQ",   "token": "10940", "name": "DIVISLAB"},
    {"symbol": "DRREDDY-EQ",    "token": "881",   "name": "DRREDDY"},
    {"symbol": "EICHERMOT-EQ",  "token": "910",   "name": "EICHERMOT"},
    {"symbol": "GRASIM-EQ",     "token": "1232",  "name": "GRASIM"},
    {"symbol": "HCLTECH-EQ",    "token": "1363",  "name": "HCLTECH"},
    {"symbol": "HDFCBANK-EQ",   "token": "1333",  "name": "HDFCBANK"},
    {"symbol": "HDFCLIFE-EQ",   "token": "467",   "name": "HDFCLIFE"},
    {"symbol": "HEROMOTOCO-EQ", "token": "1348",  "name": "HEROMOTOCO"},
    {"symbol": "HINDALCO-EQ",   "token": "1564",  "name": "HINDALCO"},
    {"symbol": "HINDUNILVR-EQ", "token": "1394",  "name": "HINDUNILVR"},
    {"symbol": "ICICIBANK-EQ",  "token": "4963",  "name": "ICICIBANK"},
    {"symbol": "ITC-EQ",        "token": "1660",  "name": "ITC"},
    {"symbol": "INDUSINDBK-EQ", "token": "5258",  "name": "INDUSINDBK"},
    {"symbol": "INFY-EQ",       "token": "1594",  "name": "INFY"},
    {"symbol": "JSWSTEEL-EQ",   "token": "11723", "name": "JSWSTEEL"},
    {"symbol": "KOTAKBANK-EQ",  "token": "1922",  "name": "KOTAKBANK"},
    {"symbol": "LT-EQ",         "token": "11483", "name": "LT"},
    {"symbol": "M&M-EQ",        "token": "2031",  "name": "M&M"},
    {"symbol": "MARUTI-EQ",     "token": "10999", "name": "MARUTI"},
    {"symbol": "NESTLEIND-EQ",  "token": "17963", "name": "NESTLEIND"},
    {"symbol": "NTPC-EQ",       "token": "11630", "name": "NTPC"},
    {"symbol": "ONGC-EQ",       "token": "2475",  "name": "ONGC"},
    {"symbol": "POWERGRID-EQ",  "token": "14977", "name": "POWERGRID"},
    {"symbol": "RELIANCE-EQ",   "token": "2885",  "name": "RELIANCE"},
    {"symbol": "SBILIFE-EQ",    "token": "21808", "name": "SBILIFE"},
    {"symbol": "SBIN-EQ",       "token": "3045",  "name": "SBIN"},
    {"symbol": "SUNPHARMA-EQ",  "token": "3351",  "name": "SUNPHARMA"},
    {"symbol": "TCS-EQ",        "token": "11536", "name": "TCS"},
    {"symbol": "TATACONSUM-EQ", "token": "3432",  "name": "TATACONSUM"},
    {"symbol": "TATAMOTORS-EQ", "token": "3456",  "name": "TATAMOTORS"},
    {"symbol": "TATASTEEL-EQ",  "token": "3499",  "name": "TATASTEEL"},
    {"symbol": "TECHM-EQ",      "token": "13538", "name": "TECHM"},
    {"symbol": "TITAN-EQ",      "token": "3506",  "name": "TITAN"},
    {"symbol": "ULTRACEMCO-EQ", "token": "11532", "name": "ULTRACEMCO"},
    {"symbol": "UPL-EQ",        "token": "11287", "name": "UPL"},
    {"symbol": "WIPRO-EQ",      "token": "3787",  "name": "WIPRO"},
    {"symbol": "ZOMATO-EQ",     "token": "5097",  "name": "ZOMATO"},
]

STOP_LOSS_PCT = 0.98
TARGET_PCT = 1.04
EXCHANGE = "NSE"

def calculate_rsi(prices, period=14):
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

def calculate_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]

def calculate_macd(prices):
    ema12 = pd.Series(prices).ewm(span=12, adjust=False).mean()
    ema26 = pd.Series(prices).ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd.iloc[-1], signal.iloc[-1]

def calculate_bollinger(prices, period=20):
    series = pd.Series(prices)
    mid = series.rolling(period).mean().iloc[-1]
    std = series.rolling(period).std().iloc[-1]
    return mid - 2*std, mid + 2*std

def get_candle_prices(api, token):
    to_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    from_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M")
    params = {
        "exchange": EXCHANGE,
        "symboltoken": token,
        "interval": "FIFTEEN_MINUTE",
        "fromdate": from_date,
        "todate": to_date
    }
    data = api.getCandleData(params)
    return [candle[4] for candle in data['data']]

def get_available_budget(api):
    try:
        funds = api.rmsLimit()
        budget = float(funds['data']['availablecash'])
        print(f"\n💰 Available Balance: ₹{budget}")
        if budget < 500:
            print("❌ Insufficient Balance! Minimum ₹500 needed.")
            exit()
        return budget
    except Exception as e:
        print(f"❌ Balance fetch error: {e}")
        exit()

def analyze_stock(api, stock):
    try:
        prices = get_candle_prices(api, stock['token'])
        if len(prices) < 26:
            return None

        price = prices[-1]
        rsi = calculate_rsi(prices)
        ema9 = calculate_ema(prices, 9)
        ema21 = calculate_ema(prices, 21)
        macd, signal = calculate_macd(prices)
        bb_lower, bb_upper = calculate_bollinger(prices)

        uptrend = ema9 > ema21

        # ✅ Maximum Relaxed Signals
        buy_signal = (
            uptrend and
            rsi < 60
        )

        sell_signal = (
            not uptrend and
            rsi > 45 and
            macd < signal
        )

        buy_score = 0
        if rsi < 60: buy_score += (60 - rsi)
        if macd > signal: buy_score += 10
        if uptrend: buy_score += 10
        if price <= bb_lower * 1.02: buy_score += 20

        sell_score = 0
        if rsi > 45: sell_score += (rsi - 45)
        if macd < signal: sell_score += 10
        if not uptrend: sell_score += 10
        if price >= bb_upper * 0.98: sell_score += 20

        trend = "📈 UPTREND" if uptrend else "📉 DOWNTREND"
        signal_str = "🟢 BUY" if buy_signal else ("🔴 SHORT" if sell_signal else "❌")
        print(f"{stock['name']:15} | ₹{price:8.2f} | {trend} | RSI:{round(rsi,1):5} | {signal_str}")

        return {
            "stock": stock,
            "price": price,
            "buy_signal": buy_signal,
            "sell_signal": sell_signal,
            "buy_score": buy_score,
            "sell_score": sell_score
        }
    except Exception as e:
        print(f"{stock['name']:15} | Error: {e}")
        return None

def place_order(api, stock, transaction, quantity):
    return api.placeOrder({
        "variety": "NORMAL",
        "tradingsymbol": stock['symbol'],
        "symboltoken": stock['token'],
        "transactiontype": transaction,
        "exchange": EXCHANGE,
        "ordertype": "MARKET",
        "producttype": "INTRADAY",
        "duration": "DAY",
        "quantity": quantity
    })

def monitor_trade(api, stock, entry_price, quantity, is_short=False):
    if is_short:
        stop_loss = entry_price * (2 - STOP_LOSS_PCT)
        target = entry_price * (2 - TARGET_PCT)
    else:
        stop_loss = entry_price * STOP_LOSS_PCT
        target = entry_price * TARGET_PCT

    trade_type = "SHORT SELL" if is_short else "BUY"
    print(f"\n⏳ Monitoring {stock['name']} ({trade_type})...")
    print(f"   Entry: ₹{entry_price} | SL: ₹{round(stop_loss,2)} | Target: ₹{round(target,2)} | Qty: {quantity}")

    max_checks = 40
    checks = 0

    while checks < max_checks:
        checks += 1
        time.sleep(30)
        try:
            quote = api.ltpData(EXCHANGE, stock['symbol'], stock['token'])
            current = quote['data']['ltp']

            if is_short:
                pnl = round((entry_price - current) * quantity, 2)
            else:
                pnl = round((current - entry_price) * quantity, 2)

            print(f"   [{checks}/40] {stock['name']}: ₹{current} | P&L: ₹{pnl}")

            if is_short:
                if current <= target:
                    print(f"🎯 Target Hit!")
                    place_order(api, stock, "BUY", quantity)
                    print(f"✅ Profit: ₹{pnl}")
                    return
                elif current >= stop_loss:
                    print(f"🛑 Stop Loss Hit!")
                    place_order(api, stock, "BUY", quantity)
                    print(f"❌ Loss: ₹{abs(pnl)}")
                    return
            else:
                if current >= target:
                    print(f"🎯 Target Hit!")
                    place_order(api, stock, "SELL", quantity)
                    print(f"✅ Profit: ₹{pnl}")
                    return
                elif current <= stop_loss:
                    print(f"🛑 Stop Loss Hit!")
                    place_order(api, stock, "SELL", quantity)
                    print(f"❌ Loss: ₹{abs(pnl)}")
                    return

        except Exception as e:
            print(f"Monitor Error: {e}")

    print(f"\n⏰ 20 minutes കഴിഞ്ഞു — Auto Exit!")
    if is_short:
        place_order(api, stock, "BUY", quantity)
    else:
        place_order(api, stock, "SELL", quantity)
    print(f"🚪 Position Closed.")

# === MAIN ===
totp = pyotp.TOTP(TOTP_SECRET).now()
api = SmartConnect(api_key=API_KEY)
data = api.generateSession(CLIENT_ID, PASSWORD, totp)

if data['status']:
    print("✅ Login Success!")

    BUDGET = get_available_budget(api)

    print(f"\n🔍 Scanning Nifty 50 stocks...\n")
    print(f"{'Stock':15} | {'Price':8} | {'Trend':15} | {'RSI':5} | Signal")
    print("-" * 65)

    buy_results = []
    short_results = []

    for stock in STOCKS:
        result = analyze_stock(api, stock)
        if result:
            if result['buy_signal']:
                buy_results.append(result)
            elif result['sell_signal']:
                short_results.append(result)
        time.sleep(2)  # ✅ 0.5 → 2 seconds (rate limit fix)

    print(f"\n{'='*65}")
    print(f"🟢 Buy Signals: {len(buy_results)}")
    print(f"🔴 Short Signals: {len(short_results)}")

    if buy_results:
        best = max(buy_results, key=lambda x: x['buy_score'])
        s = best['stock']
        price = best['price']
        quantity = max(1, int(BUDGET / price))
        print(f"\n🏆 Best BUY: {s['name']} @ ₹{price} | Qty: {quantity}")
        order = place_order(api, s, "BUY", quantity)
        print(f"📋 Order: {order}")
        monitor_trade(api, s, price, quantity, is_short=False)

    elif short_results:
        best = max(short_results, key=lambda x: x['sell_score'])
        s = best['stock']
        price = best['price']
        quantity = max(1, int(BUDGET / price))
        print(f"\n🏆 Best SHORT: {s['name']} @ ₹{price} | Qty: {quantity}")
        order = place_order(api, s, "SELL", quantity)
        print(f"📋 Order: {order}")
        monitor_trade(api, s, price, quantity, is_short=True)

    else:
        print("\n⏳ No good signals today. Try tomorrow!")

else:
    print("❌ Login Failed!")
