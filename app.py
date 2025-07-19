from flask import Flask, request, jsonify
import os, logging, ccxt

# ────────────── 配置区 ────────────── #
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

API_KEY      = os.getenv("EXCHANGE_API_KEY")
API_SECRET   = os.getenv("EXCHANGE_API_SECRET")
API_PASSWORD = os.getenv("EXCHANGE_API_PASSWORD")     # Bitget passphrase
SECURITY_KEY = os.getenv("SECURITY_KEY")              # TradingView 校验密钥

# Bitget: defaultType = swap → U 本位永续
exchange = ccxt.bitget({
    "apiKey":   API_KEY,
    "secret":   API_SECRET,
    "password": API_PASSWORD,
    "options":  {"defaultType": "swap"},
    "hostname": "bitgetapi.com" 
})
exchange.load_markets()                               # 预加载市场表

# ────────────── Webhook 路由 ────────────── #
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}
    logging.info("Webhook in: %s", data)

    # 1) 校验密钥
    if data.get("key") != SECURITY_KEY:
        return _err("Invalid security key", 401)

    # 2) 基本字段
    symbol = data.get("symbol")              # 例: BTC/USDT:USDT
    qty    = data.get("qty")                 # TradingView 填的张数
    side   = data.get("side")                # "buy" or "sell"
    otype  = data.get("order_type", "market")
    price  = data.get("price")
    reduce = bool(data.get("reduceOnly", False))

    # 3) 合约 & 张数校验
    if symbol not in exchange.symbols:
        return _err(f"Symbol {symbol} not supported", 400)
    try:
        qty = float(qty)
    except (TypeError, ValueError):
        return _err("qty missing or not numeric", 400)
    if qty < 0.001:                          # Bitget BTC 最小张数
        return _err("qty must be ≥ 0.001", 400)

    # 4) 构造下单参数
    params = {"posSide": "long"}
    if reduce:
        params["reduceOnly"] = True

    try:
        if otype == "market":
            order = exchange.create_order(symbol, "market", side, qty, None, params)
        elif otype == "limit" and price:
            order = exchange.create_order(symbol, "limit", side, qty, price, params)
        else:
            return _err("Invalid order_type or price", 400)

        logging.info("Order OK: %s", order["id"])
        return jsonify({"status": "success", "order": order})

    except Exception as e:
        logging.exception("Order failed")
        return _err(str(e), 500)

# ────────────── 辅助函数 ────────────── #
def _err(msg, code):
    logging.error(msg)
    return jsonify({"status": "error", "message": msg}), code

# ────────────── 本地调试入口 ────────────── #
if __name__ == "__main__":
    app.run(debug=True)
