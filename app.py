from flask import Flask, request, jsonify
import os
import ccxt

app = Flask(__name__)

# 从环境变量读取密钥
API_KEY       = os.getenv("EXCHANGE_API_KEY")
API_SECRET    = os.getenv("EXCHANGE_API_SECRET")
API_PASSWORD  = os.getenv("EXCHANGE_API_PASSWORD")   # ← Bitget 的 Passphrase
SECURITY_KEY  = os.getenv("SECURITY_KEY")            # TradingView 验证密钥

exchange = ccxt.bitget({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWORD
})


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    # 1️⃣ 验证安全密钥
    if data.get("key") != SECURITY_KEY:
        return jsonify({"error": "Invalid security key"}), 401

    # 2️⃣ 解析参数
    symbol      = data.get("symbol")
    side        = data.get("side", "").lower()
    qty         = data.get("qty")
    order_type  = data.get("order_type", "market").lower()
    price       = data.get("price")           # 限价单才用

    try:
        # 3️⃣ 下单
        if order_type == "market":
            order = exchange.create_order(symbol, "market", side, qty)
        elif order_type == "limit" and price:
            order = exchange.create_order(symbol, "limit", side, qty, price)
        else:
            return jsonify({"error": "Invalid order parameters"}), 400

        return jsonify({"status": "success", "order": order})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
