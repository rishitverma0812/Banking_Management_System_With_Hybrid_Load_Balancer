import pytest
from flask import Flask
from flask.testing import FlaskClient
from unittest.mock import patch, MagicMock
import json
import pandas as pd

from app import app, select_best_server, forward_request_to_server, calculate_balance

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_request_routing_to_best_server(client: FlaskClient, mocker):
    # Mock the select_best_server function to return a specific server
    mock_best_server = {"id": 1, "url": "http://mockserver.com", "active_connections": 0, "response_time": 0}
    mocker.patch('app.select_best_server', return_value=mock_best_server)

    # Mock the forward_request_to_server function to simulate a successful request
    mock_response_data = {"success": True}
    mocker.patch('app.forward_request_to_server', return_value=(mock_response_data, 200))

    # Simulate a POST request to the /request endpoint
    response = client.post('/request', json={"data": "test"})

    # Assert that the response is as expected
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["server"] == mock_best_server["url"]
    assert response_data["server_response"] == mock_response_data

def test_user_login_success(client: FlaskClient, mocker):
    mocker.patch('app.users_df', return_value=pd.DataFrame({
        'username': ['testuser'],
        'password': ['testpass']
    }))
    response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 302  # Redirect to account page
    assert b'Login Successful!' in response.data

def test_user_registration_success(client: FlaskClient, mocker):
    mocker.patch('app.users_df', return_value=pd.DataFrame(columns=['username', 'password']))
    mock_to_csv = mocker.patch('app.pd.DataFrame.to_csv')
    response = client.post('/register', data={
        'firstname': 'Test',
        'lastname': 'User',
        'username': 'newuser',
        'password': 'newpass'
    })
    assert response.status_code == 302  # Redirect to login page
    assert b'Registration successful!' in response.data
    mock_to_csv.assert_called_once()

def test_login_incorrect_password(client: FlaskClient, mocker):
    mocker.patch('app.users_df', return_value=pd.DataFrame({
        'username': ['testuser'],
        'password': ['testpass']
    }))
    response = client.post('/login', data={'username': 'testuser', 'password': 'wrongpass'})
    assert response.status_code == 200  # Stay on login page
    assert b'Invalid password. Please try again.' in response.data

def test_no_available_servers(client: FlaskClient, mocker):
    mocker.patch('app.select_best_server', return_value=None)
    response = client.post('/request', json={"data": "test"})
    assert response.status_code == 503
    assert b'No available servers' in response.data

def test_transaction_file_not_found(client: FlaskClient, mocker):
    mocker.patch('app.pd.read_csv', side_effect=FileNotFoundError)
    response = client.get('/api/get-balance')
    assert response.status_code == 200
    assert b'Transactions file not found.' in response.data