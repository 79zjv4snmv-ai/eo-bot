import requests
import asyncio
import time
from datetime import datetime, timedelta, timezone
from telegram import Bot

TELEGRAM_BOT_TOKEN = "8963611921:AAHr0jtCdhwoM5GwIQSou8-hZu2u6xYhYmg"
TELEGRAM_CHAT_ID = "373404939"
TWELVE_DATA_API_KEY = "4b8d4e01d3ec4c219f918fbdf849c35e"

SYMBOLS = ["SOL/USD", "DOGE/USD"]
INTERVAL = "1min"
EMA_FAST = 9
EMA_SLOW = 21
RSI_PERIOD = 14
CHECK_INTERVAL_SECONDS = 180

SAUDI_TZ = timezone(timedelta(hours=3))
def saudi_now():
    return datetime.now(SAUDI_TZ)

def fetch_data(symbol):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol, "interval": INTERVAL, "outputsize": 100,
        "apikey": TWELVE_DATA_API_KEY, "format": "JSON"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if "values" not in data:
            print("API Error")
            return None
        values = data["values"][::-1]
        return [float(v["close"]) for v in values]
    except Exception as e:
        print("Connection Error")
        return None

def calculate_ema(prices, period):
    if len(prices) < period: return [0] * len(prices)
    ema = [sum(prices[:period]) / period]
    k = 2 / (period + 1)
    for p in prices[period:]:
        ema.append((p - ema[-1]) * k + ema[-1])
    return [0]*(period-1) + ema

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return [50] * len(prices)
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    seed = deltas[:period]
    up = sum([x for x in seed if x > 0]) / period
    down = -sum([x for x in seed if x < 0]) / period
    rs = up / down if down != 0 else 100
    rsi = [100 - 100 / (1 + rs)]
    for i in range(period, len(deltas)):
        delta = deltas[i]
        upval = delta if delta > 0 else 0
        downval = -delta if delta < 0 else 0
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 100
        rsi.append(100 - 100 / (1 + rs))
    return [50] * (len(prices) - len(rsi)) + rsi

def generate_signal(prices):
    ema_fast = calculate_ema(prices, EMA_FAST)
    ema_slow = calculate_ema(prices, EMA_SLOW)
    rsi_values = calculate_rsi(prices, RSI_PERIOD)
    current_rsi = rsi_values[-1]
    current_price = prices[-1]
    cross_up = ema_fast[-2] <= ema_slow[-2] and ema_fast[-1] > ema_slow[-1]
    cross_down = ema_fast[-2] >= ema_slow[-2] and ema_fast[-1] < ema_slow[-1]
    print("Price:", current_price, "RSI:", current_rsi)
    if cross_up and 50 < current_rsi < 70:
        return "BUY"
    elif cross_down and 30 < current_rsi < 50:
        return "SELL"
    return None

async def send_signal(symbol, signal_type):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    if signal_type == "BUY":
        action = "CALL UP"
    else:
        action = "PUT DOWN"
    entry_time = saudi_now().strftime("%I:%M:%S %p")
    msg = "Symbol: " + symbol + "\n"
    msg += "Time: " + entry_time + "\n"
    msg += "Duration: 1 Minute\n"
    msg += "Action: " + action
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        print("Signal Sent")
    except Exception as e:
        print("Send Error")

async def main_loop():
    print("Bot Started...")
    while True:
        for symbol in SYMBOLS:
            try:
                prices = fetch_data(symbol)
                if prices and len(prices) > 30:
                    signal = generate_signal(prices)
                    if signal:
                        await send_signal(symbol, signal)
                time.sleep(2)
            except Exception as e:
                print("Loop Error")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(main_loop())
