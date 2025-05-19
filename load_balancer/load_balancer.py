from flask import Flask, request, jsonify
import time
import threading
import requests

app = Flask(__name__)

# Backend server registry
backend_servers = [
    {"id": 1, "url": "http://server1.com", "active_connections": 0, "response_time": 0, "last_update": time.time()},
    {"id": 2, "url": "http://server2.com", "active_connections": 0, "response_time": 0, "last_update": time.time()},
    {"id": 3, "url": "http://server3.com", "active_connections": 0, "response_time": 0, "last_update": time.time()},
]

# Weights for the hybrid algorithm
WEIGHT_CONNECTIONS = 0.6
WEIGHT_RESPONSE_TIME = 0.4

# Lock for thread-safe updates
lock = threading.Lock()

def update_server_metrics(server_id, response_time):
    """Update server metrics after a request is processed."""
    with lock:
        for server in backend_servers:
            if server["id"] == server_id:
                server["active_connections"] -= 1
                server["response_time"] = (server["response_time"] + response_time) / 2
                server["last_update"] = time.time()
                break

def select_best_server():
    """Select the best server using the hybrid algorithm."""
    best_server = None
    best_score = float('inf')

    for server in backend_servers:
        score = (WEIGHT_CONNECTIONS * server["active_connections"]) + (WEIGHT_RESPONSE_TIME * server["response_time"])
        if score < best_score:
            best_score = score
            best_server = server

    return best_server

def forward_request_to_server(server_url, request_data):
    """Forward the request to the selected backend server."""
    try:
        response = requests.post(server_url, json=request_data, timeout=5)
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 503

@app.route('/request', methods=['POST'])
def handle_request():
    """Route incoming requests to the best backend server."""
    best_server = select_best_server()

    if not best_server:
        return jsonify({"error": "No available servers"}), 503

    # Simulate forwarding the request and measuring response time
    start_time = time.time()
    request_data = request.json
    response_data, status_code = forward_request_to_server(best_server["url"], request_data)
    response_time = time.time() - start_time

    # Update server metrics
    with lock:
        best_server["active_connections"] += 1
    update_server_metrics(best_server["id"], response_time)

    return jsonify({
        "message": "Request routed",
        "server": best_server["url"],
        "response_time": response_time,
        "server_response": response_data
    }), status_code

@app.route('/health', methods=['GET'])
def health_check():
    """Provide health status of the load balancer and backend servers."""
    return jsonify({
        "status": "healthy",
        "servers": backend_servers
    })

@app.route('/register', methods=['POST'])
def register_server():
    """Register a new backend server with the load balancer."""
    new_server = request.json
    with lock:
        backend_servers.append(new_server)
    return jsonify({"message": "Server registered", "server": new_server})

@app.route('/deregister', methods=['POST'])
def deregister_server():
    """Deregister a backend server from the load balancer."""
    server_id = request.json.get("id")
    with lock:
        global backend_servers
        backend_servers = [server for server in backend_servers if server["id"] != server_id]
    return jsonify({"message": "Server deregistered", "server_id": server_id})

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Display real-time metrics."""
    return jsonify({
        "servers": backend_servers,
        "timestamp": time.time()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)