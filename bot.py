from SmartApi import SmartConnect
import pyotp
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import schedule
import requests

API_KEY = os.environ['API_KEY']
CLIENT_ID = os.environ['CLIENT_ID']
PASSWORD = os.environ['PASSWORD']
TOTP_SECRET = os.environ['TOTP_SECRET']

STOCKS = [
    # Nifty 50
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

    # 🥇 Gold ETF
    {"symbol": "GOLDBEES-EQ",   "token": "13611", "name": "GOLDBEES"},
    {"symbol": "HDFCGOLD-EQ",   "token": "27446", "name": "HDFCGOLD"},
    {"symbol": "NIPGOLD-EQ",    "token": "29114", "name": "NIPGOLD"},
    {"symbol": "AXISGOLD-EQ",   "token": "21798", "name": "AXISGOLD"},
    {"symbol": "SBIGOLD-EQ",    "token": "31061", "name": "SBIGOLD"},

    # 🥈 Silver ETF
    {"symbol": "SILVERBEES-EQ", "token": "67106", "name": "SILVERBEES"},
    {"symbol": "SILVERIETF-EQ", "token": "67119", "name": "SILVERIETF"},
    {"symbol": "LICSILVER-EQ",  "token": "67285", "name": "LICSILVER"},
]

STOP_LOSS_PCT = 0.98
TARGET_PCT = 1.04
EXCHANGE = "NSE"
api = None

def get_ist_time():
    IST = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(IST)

def is_market_open():
    now = get_ist_time()
    if now.weekday() > 4:
        return False
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=14, second=0, microsecond=0)
    return market_open <= now <= market_close

def is_force_exit_time():
    now = get_ist_time()
    return (now.hour == 15 and now.minute >= 14) or (now.hour > 15)

def login():
    global api
    totp = pyotp.TOTP(TOTP_SECRET).now()
    api = SmartConnect(api_key=API_KEY)
    data = api.generateSession(CLIENT_ID, PASSWORD, totp)
    if data['status']:
        print("✅ Login Success!")
        return True
    print("❌ Login Failed!")
    return False

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

def get_candle_prices(token):
    now = get_ist_time()
    to_date = now.strftime("%Y-%m-%d %H:%M")
    from_date = (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M")
    params = {
        "exchange": EXCHANGE,
        "symboltoken": token,
        "interval": "FIFTEEN_MINUTE",
        "fromdate": from_date,
        "todate": to_date
    }
    data = api.getCandleData(params)
    return [candle[4] for candle in data['data']]

def get_available_budget():
    try:
        funds = api.rmsLimit()
        budget = float(funds['data']['availablecash'])
        print(f"💰 Available Balance: ₹{budget}")
        if budget < 500:
            print("❌ Insufficient Balance!")
            return None
        return budget
    except Exception as e:
        print(f"❌ Balance error: {e}")
        return None

def analyze_stock(stock):
    try:
        prices = get_candle_prices(stock['token'])
        if len(prices) < 26:
            return None
        price = prices[-1]
        rsi = calculate_rsi(prices)
        ema9 = calculate_ema(prices, 9)
        ema21 = calculate_ema(prices, 21)
        macd, signal = calculate_macd(prices)
        uptrend = ema9 > ema21
        buy_signal = uptrend and rsi < 60
        sell_signal = not uptrend and rsi > 45 and macd < signal
        buy_score = (60 - rsi if rsi < 60 else 0) + (10 if macd > signal else 0) + (10 if uptrend else 0)
        sell_score = (rsi - 45 if rsi > 45 else 0) + (10 if macd < signal else 0) + (10 if not uptrend else 0)
        trend = "📈 UP" if uptrend else "📉 DOWN"
        sig = "🟢 BUY" if buy_signal else ("🔴 SHORT" if sell_signal else "❌")
        print(f"{stock['name']:15} | ₹{price:8.2f} | {trend} | RSI:{round(rsi,1):5} | {sig}")
        return {"stock": stock, "price": price, "buy_signal": buy_signal,
                "sell_signal": sell_signal, "buy_score": buy_score, "sell_score": sell_score}
    except Exception as e:
        print(f"{stock['name']:15} | Error: {e}")
        return None

def place_order(stock, transaction, quantity):
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

def monitor_trade(stock, entry_price, quantity, is_short=False):
    stop_loss = entry_price * (STOP_LOSS_PCT if not is_short else (2 - STOP_LOSS_PCT))
    target = entry_price * (TARGET_PCT if not is_short else (2 - TARGET_PCT))
    trade_type = "SHORT" if is_short else "BUY"
    print(f"⏳ Monitoring {stock['name']} ({trade_type}) | SL:₹{round(stop_loss,2)} | Target:₹{round(target,2)}")

    for i in range(40):
        time.sleep(30)
        if is_force_exit_time():
            print(f"⛔ 3:14 PM Force Exit! — {stock['name']}")
            place_order(stock, "BUY" if is_short else "SELL", quantity)
            print("✅ Position Closed — Fine Avoided!")
            return
        if not is_market_open():
            print("🔔 Market closed — Auto Exit!")
            place_order(stock, "BUY" if is_short else "SELL", quantity)
            return
        try:
            quote = api.ltpData(EXCHANGE, stock['symbol'], stock['token'])
            current = quote['data']['ltp']
            pnl = round((entry_price - current if is_short else current - entry_price) * quantity, 2)
            print(f"[{i+1}/40] {stock['name']}: ₹{current} | P&L: ₹{pnl} | {get_ist_time().strftime('%H:%M')} IST")
            if (is_short and current <= target) or (not is_short and current >= target):
                print(f"🎯 Target Hit! Profit: ₹{pnl}")
                place_order(stock, "BUY" if is_short else "SELL", quantity)
                return
            if (is_short and current >= stop_loss) or (not is_short and current <= stop_loss):
                print(f"🛑 Stop Loss! Loss: ₹{abs(pnl)}")
                place_order(stock, "BUY" if is_short else "SELL", quantity)
                return
        except Exception as e:
            print(f"Monitor Error: {e}")
    print("⏰ 20 min — Auto Exit!")
    place_order(stock, "BUY" if is_short else "SELL", quantity)

def run_bot():
    now = get_ist_time()

    # ✅ IP always print
    try:
        ip = requests.get('https://api.ipify.org').text
        print(f"🌐 Railway IP: {ip}")
    except:
        pass

    if is_force_exit_time():
        print(f"⛔ 3:14 PM passed — No new trades! {now.strftime('%H:%M')} IST")
        return
    if not is_market_open():
        print(f"💤 Market closed. {now.strftime('%H:%M')} IST")
        return
    print(f"\n🚀 Bot running — {now.strftime('%H:%M')} IST")
    if not login():
        return
    budget = get_available_budget()
    if not budget:
        return
    buy_results, short_results = [], []
    for stock in STOCKS:
        result = analyze_stock(stock)
        if result:
            if result['buy_signal']:
                buy_results.append(result)
            elif result['sell_signal']:
                short_results.append(result)
        time.sleep(2)
    print(f"🟢 Buy: {len(buy_results)} | 🔴 Short: {len(short_results)}")
    if buy_results:
        best = max(buy_results, key=lambda x: x['buy_score'])
        s, price = best['stock'], best['price']
        qty = max(1, int(budget / price))
        print(f"🏆 BUY: {s['name']} @ ₹{price} | Qty: {qty}")
        order = place_order(s, "BUY", qty)
        print(f"📋 Order: {order}")
        monitor_trade(s, price, qty, is_short=False)
    elif short_results:
        best = max(short_results, key=lambda x: x['sell_score'])
        s, price = best['stock'], best['price']
        qty = max(1, int(budget / price))
        print(f"🏆 SHORT: {s['name']} @ ₹{price} | Qty: {qty}")
        order = place_order(s, "SELL", qty)
        print(f"📋 Order: {order}")
        monitor_trade(s, price, qty, is_short=True)
    else:
        print("⏳ No signals today.")

schedule.every(15).minutes.do(run_bot)

print("🤖 Trading Bot Started!")
run_bot()

while True:
    schedule.run_pending()
    time.sleep(60)
