from flask import Flask, jsonify, render_template
import datetime
import platform
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/info')
def info():
    return jsonify({
        'app_name': 'Flask Test App',
        'version': '1.0.0',
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'timestamp': datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 