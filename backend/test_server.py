from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, 
     supports_credentials=True, 
     origins=['http://localhost:5173'],
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/api/strategy', methods=['GET'])
def get_strategies():
    return jsonify({
        'strategies': [
            {'id': 1, 'name': 'Fast Strategy', 'type': 'fast'},
            {'id': 2, 'name': 'Slow Strategy', 'type': 'slow'},
            {'id': 3, 'name': 'Scalping Strategy', 'type': 'scalping'}
        ]
    })

@app.route('/api/signal', methods=['GET'])
def get_signal():
    return jsonify({
        'signal': 'BUY',
        'symbol': 'BTCUSDT',
        'price': 45000.00,
        'confidence': 0.85,
        'timestamp': '2025-01-14T14:30:00Z',
        'strategy': 'Fast Strategy'
    })

@app.route('/api/signal/stats', methods=['GET'])
def get_signal_stats():
    return jsonify({
        'totalSignals': 150,
        'averageConfidence': 82.5,
        'history': [
            {'timestamp': '2025-01-14T14:30:00Z', 'confidence': 85, 'direction': 'BUY', 'asset': 'BTCUSDT'},
            {'timestamp': '2025-01-14T13:30:00Z', 'confidence': 78, 'direction': 'SELL', 'asset': 'ETHUSDT'},
            {'timestamp': '2025-01-14T12:30:00Z', 'confidence': 92, 'direction': 'BUY', 'asset': 'BNBUSDT'},
            {'timestamp': '2025-01-14T11:30:00Z', 'confidence': 75, 'direction': 'SELL', 'asset': 'ADAUSDT'},
            {'timestamp': '2025-01-14T10:30:00Z', 'confidence': 82, 'direction': 'BUY', 'asset': 'SOLUSDT'}
        ],
        'successful_trades': 120,
        'failed_trades': 30,
        'success_rate': 80.0,
        'total_profit': 2500.50,
        'average_profit_per_trade': 20.83
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Server is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)