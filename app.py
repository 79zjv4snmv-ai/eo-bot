import requests
import asyncio
import time
from datetime import datetime, timedelta, timezone
from telegram import Bot

# ========== الإعدادات ==========
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
            print(f"⚠️ خطأ من API لـ {symbol}: {data.get('message', 'Unknown error')}")
            return None
        values = data["values"][::-1]
        return [float(v["close"]) for v in values]
    except Exception as e:
        print(f"⚠️ فشل الاتصال بـ {symbol}: {e}")
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
    
    print(f"   📊 السعر: {current_price:.4f} | RSI: {current_rsi:.2f} | EMA9: {ema_fast[-1]:.4f} | EMA21: {ema_slow[-1]:.4f}")
    
    if cross_up and 50 < current_rsi < 70:
        return "BUY"
    elif cross_down and 30 < current_rsi < 50:
        return "SELL"
    return None

async def send_signal(symbol, signal_type):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    action = "🟢 CALL UP ⬆️" if signal_type == "BUY" else "🔴 PUT DOWN ⬇️"
    entry_time = saudi_now().strftime("%I:%M:%S %p")
    
    message = (
        f"📊 {symbol}\n"
        f"⏰ {entry_time}\n"
        f"⏳ 1 Minutes\n"
        f"{action}"
    )
    
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"✅ إشارة {signal_type} لـ {symbol} في {entry_time}")
    except Exception as e:
        print(f"❌ فشل إرسال الإشارة: {e}")

async def main_loop():
    print(f"🚀 بدء مراقبة {SYMBOLS} على إطار دقيقة واحدة...")
    while True:
        for symbol in SYMBOLS:
            try:
                prices = fetch_data(symbol)
                if prices and len(prices) > max(EMA_SLOW, RSI_PERIOD):
                    signal = generate_signal(prices)
                    if signal:
                        await send_signal(symbol, signal)
                    else:
                        print(f"   ⏳ لا توجد إشارة لـ {symbol}")
                else:
                    print(f"   ⚠️ بيانات غير كافية لـ {symbol}")
                time.sleep(2)
            except Exception as e:
                print(f"❌ خطأ في {symbol}: {e}")
        
        print(f"⏳ انتظار {CHECK_INTERVAL_SECONDS} ثانية قبل الفحص التالي...\n")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(main_loop())
