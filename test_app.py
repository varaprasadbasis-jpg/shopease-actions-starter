# 1. Make sure you are at the absolute root folder of your Git repository
cd /workspaces/shopease-actions-starter/

# 2. Overwrite the broken root 'test_app.py' with the correct test script
cat << 'EOF' > test_app.py
import pytest
from unittest.mock import patch
import redis
from app import app, PRICES 

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_route(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['service'] == 'shopease-api'

def test_price_route_valid_item(client):
    item = list(PRICES.keys())[0]  # grabs the first item dynamically
    response = client.get(f'/price/{item}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['item'] == item
    assert data['price'] == PRICES[item]

def test_price_route_invalid_item(client):
    response = client.get('/price/non_existent_item')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'unknown item'

@patch('app.get_cache')
def test_visit_route_success(mock_get_cache, client):
    mock_redis = mock_get_cache.return_value
    mock_redis.incr.return_value = 5
    response = client.get('/visit')
    assert response.status_code == 200
    assert response.get_json() == {"visits": 5}

@patch('app.get_cache')
def test_visit_route_cache_unavailable(mock_get_cache, client):
    mock_redis = mock_get_cache.return_value
    mock_redis.incr.side_effect = redis.exceptions.RedisError("Connection failed")
    response = client.get('/visit')
    assert response.status_code == 503
    assert response.get_json() == {"error": "cache unavailable"}
EOF

# 3. Create the correct 'app.py' file right next to it in the root directory
cat << 'EOF' > app.py
import os
import redis
from flask import Flask, jsonify

app = Flask(__name__)

PRICES = {
    "laptop": 45000,
    "phone": 15000,
    "headphones": 2000
}

def get_cache():
    return redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379,
                       socket_connect_timeout=2, decode_responses=True)

@app.route("/health")
def health():
    return jsonify(status="ok", service="shopease-api",
                  version=os.getenv("APP_VERSION", "dev"))

@app.route("/price/<item>")
def price(item):
    if item not in PRICES:
        return jsonify(error="unknown item"), 404
    return jsonify(item=item, price=PRICES[item], currency="INR")

@app.route("/visit")
def visit():
    try:
        return jsonify(visits=get_cache().incr("visits"))
    except redis.exceptions.RedisError:
        return jsonify(error="cache unavailable"), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF

