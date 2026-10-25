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
    item = list(PRICES.keys())[0]
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
