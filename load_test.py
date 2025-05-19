import requests
import threading
import time
import json
import matplotlib.pyplot as plt
from collections import defaultdict

# Configuration
BASE_URL = "http://127.0.0.1:5000/"  # Change if your app runs on a different port
USERNAME = "your_username"  # Replace with your actual username
PASSWORD = "your_password"  # Replace with your actual password
NUM_REQUESTS = 50          # Number of requests to simulate
CONCURRENT_THREADS = 10    # Maximum concurrent threads

# Store results
results = {
    "response_times": [],
    "server_distribution": defaultdict(int),
    "status_codes": defaultdict(int)
}

# Create a session to maintain cookies
session = requests.Session()

def login():
    """Log in to the application"""
    response = session.post(
        f"{BASE_URL}/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        print("Successfully logged in")
        return True
    else:
        print("Failed to log in")
        return False

def make_request(request_id):
    """Make a request to the API and record results"""
    try:
        start_time = time.time()
        
        # Choose one of these endpoints to test
        response = session.get(f"{BASE_URL}/api/get-user-transactions")
        # Alternative endpoints:
        # response = session.get(f"{BASE_URL}/api/get-balance")
        # response = session.get(f"{BASE_URL}/api/get-last-5-transactions")
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        results["response_times"].append(response_time)
        results["status_codes"][response.status_code] += 1
        
        if response.status_code == 200:
            data = response.json()
            server = data.get("served_by", "unknown")
            results["server_distribution"][server] += 1
            print(f"Request {request_id}: Status {response.status_code}, Server: {server}, Time: {response_time:.2f}ms")
        else:
            print(f"Request {request_id}: Status {response.status_code}, Time: {response_time:.2f}ms")
    
    except Exception as e:
        print(f"Request {request_id}: Error - {str(e)}")

def get_metrics():
    """Get current metrics from the server"""
    try:
        response = session.get(f"{BASE_URL}/metrics")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get metrics: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting metrics: {str(e)}")
        return None

def analyze_results():
    """Analyze and display test results"""
    # Calculate statistics
    avg_response_time = sum(results["response_times"]) / len(results["response_times"]) if results["response_times"] else 0
    
    print("\n--- Test Results ---")
    print(f"Total Requests: {len(results['response_times'])}")
    print(f"Average Response Time: {avg_response_time:.2f}ms")
    print("\nStatus Code Distribution:")
    for code, count in results["status_codes"].items():
        print(f"  {code}: {count} requests")
    
    print("\nServer Distribution:")
    for server, count in results["server_distribution"].items():
        print(f"  {server}: {count} requests ({count/NUM_REQUESTS*100:.1f}%)")
    
    # Visualize results
    plt.figure(figsize=(12, 8))
    
    # Response time plot
    plt.subplot(2, 1, 1)
    plt.plot(results["response_times"])
    plt.title('Response Times')
    plt.xlabel('Request #')
    plt.ylabel('Response Time (ms)')
    
    # Server distribution plot
    plt.subplot(2, 1, 2)
    servers = list(results["server_distribution"].keys())
    counts = list(results["server_distribution"].values())
    plt.bar(servers, counts)
    plt.title('Server Distribution')
    plt.xlabel('Server')
    plt.ylabel('Number of Requests')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('load_test_results.png')
    plt.show()

# Main test function
def run_test():
    """Run the load test"""
    if not login():
        return
    
    print(f"Starting load test with {NUM_REQUESTS} requests, max {CONCURRENT_THREADS} concurrent...")
    
    # Get initial metrics
    initial_metrics = get_metrics()
    if initial_metrics:
        print("Initial server status:")
        for server in initial_metrics["servers"]:
            print(f"  Server #{server['id']}: {server['active_connections']} connections, {server['response_time']:.2f}ms response time")
    
    # Create and start threads
    threads = []
    for i in range(NUM_REQUESTS):
        thread = threading.Thread(target=make_request, args=(i,))
        threads.append(thread)
        thread.start()
        
        # Limit concurrent threads
        if len(threads) >= CONCURRENT_THREADS:
            threads[0].join()
            threads.pop(0)
        
        # Small delay between thread starts
        time.sleep(0.1)
    
    # Wait for remaining threads to complete
    for thread in threads:
        thread.join()
    
    # Get final metrics
    final_metrics = get_metrics()
    if final_metrics:
        print("\nFinal server status:")
        for server in final_metrics["servers"]:
            print(f"  Server #{server['id']}: {server['active_connections']} connections, {server['response_time']:.2f}ms response time")
    
    # Analyze the results
    analyze_results()

if __name__ == "__main__":
    run_test()