from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app

def test_prediction_and_validation():
    model = Mock(); model.predict.return_value = ['standard']
    with patch('app.main.joblib.load', return_value=model), TestClient(app) as client:
        assert client.get('/health').status_code == 200
        response = client.post('/predict', json={'item_description':'software','product_category':'software','destination_state':'CA','exemption_certificate':'none', 'amount':100, 'country':'US', 'customer_type':'business'})
        assert response.status_code == 200
        assert response.json()['prediction'] == 'standard'
        assert client.post('/predict', json={'description':''}).status_code == 422
