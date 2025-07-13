from flask import Flask, request, jsonify
import os
import ccxt

app = Flask(__name__)

# 从环境变量获取密钥与交易所信息
API_KEY = os.getenv('EXCHANGE_API_KEY')
API_SECRET = os.getenv('EXCHANGE_API_SECRET')
SECURITY_KEY = os.getenv('SECURITY_KEY')  # 自定义的安全验证密钥

# 初始化交易所，以币安现货（Binance）为例
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
})

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    # 验证安全密钥
    if data.get('key') != SECURITY_KEY:
        return jsonify({"error": "Invalid security key"}), 401
    
    symbol = data.get('symbol')
    side = data.get('side').lower()
    qty = data.get('qty')
    order_type = data.get('order_type', 'market').lower()
    price = data.get('price', None)
    
    try:
        # 构造交易订单
        if order_type == 'market':
            order = exchange.create_order(symbol, 'market', side, qty)
        elif order_type == 'limit' and price is not None:
            order = exchange.create_order(symbol, 'limit', side, qty, price)
        else:
            return jsonify({"error": "Invalid order parameters"}), 400
            
        return jsonify({"status": "success", "order": order})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
