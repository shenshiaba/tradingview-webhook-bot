from flask import Flask, request, jsonify
import os
import ccxt

app = Flask(__name__)

exchange = ccxt.bitget({
    "apiKey": os.getenv("EXCHANGE_API_KEY"),
    "secret": os.getenv("EXCHANGE_API_SECRET"),
    "password": os.getenv("EXCHANGE_API_PASSWORD"),
    "options": {
        "defaultType": "swap",
        "loadMarkets": False  # 跳过现货市场，避免404问题
    },
    "hostname": "bitgetapi.com"  # 明确使用bitgetapi.com镜像域
})

exchange.load_markets(['swap'])  # 只加载swap合约市场，跳过现货

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    SECURITY_KEY = os.getenv('SECURITY_KEY')
    if data.get('key') != SECURITY_KEY:
        return jsonify({"error": "Invalid security key"}), 401
    
    symbol = data.get('symbol')
    side = data.get('side').lower()
    qty = data.get('qty')
    order_type = data.get('order_type', 'market').lower()
    posSide = data.get('posSide', 'long')

    params = {'posSide': posSide}

    try:
        if order_type == 'market':
            order = exchange.create_order(symbol, 'market', side, qty, None, params)
        elif order_type == 'limit':
            price = data.get('price')
            if not price:
                return jsonify({"error": "Limit order requires a price"}), 400
            order = exchange.create_order(symbol, 'limit', side, qty, price, params)
        else:
            return jsonify({"error": "Invalid order type"}), 400

        return jsonify({"status": "success", "order": order})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
