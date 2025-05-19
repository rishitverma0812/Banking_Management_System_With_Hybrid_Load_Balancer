from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import csv
import time
import threading
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Load user credentials from CSV
USER_CREDENTIALS_FILE = 'd:/Apna_Bank/user_credentials.csv'
users_df = pd.read_csv(USER_CREDENTIALS_FILE)

TRANSACTIONS_FILE = r'd:\Apna_Bank\realistic_indian_transactions.csv'

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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

# Update the calculate_balance function to properly get the current balance
def calculate_balance(username):
    try:
        # Read the transactions CSV file
        transactions_df = pd.read_csv(TRANSACTIONS_FILE)
        
        # Filter transactions for the logged-in user
        user_transactions = transactions_df[transactions_df['username'] == username]
        
        if not user_transactions.empty:
            # Get the latest dynamic_balance from the most recent transaction
            # If you have a proper datetime column, you can sort by it:
            # user_transactions = user_transactions.sort_values('time_of_transaction')
            
            # Based on your CSV structure, the dynamic_balance column already shows
            # the current balance after each transaction
            latest_balance = user_transactions.iloc[-1]['dynamic_balance']
            return float(latest_balance)
        else:
            return 0.0  # Default balance if no transactions exist
    except FileNotFoundError:
        flash('Transactions file not found.', 'danger')
        return 0.0
    except Exception as e:
        flash(f'Error retrieving balance: {str(e)}', 'danger')
        return 0.0

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# Load user by ID
@login_manager.user_loader
def load_user(user_id):
    print(f"Loading user with ID: {user_id}")  # Debug log
    user_row = users_df.loc[users_df.index == int(user_id)]
    if not user_row.empty:
        user_data = user_row.iloc[0]
        print(f"User loaded: {user_data['username']}")  # Debug log
        return User(id=user_row.index[0], username=user_data['username'], password=user_data['password'])
    print("User not found")  # Debug log
    return None

@app.route('/')
def index():
    # Read the CSV file
    df = pd.read_csv(TRANSACTIONS_FILE)
    
    # Select relevant columns (including dynamic_balance)
    transactions = df[['username', 'transaction_type', 'amount', 'dynamic_balance', 'time_of_transaction']].to_dict(orient='records')
    
    # Pass the transactions to the HTML template
    return render_template('index.html', transactions=transactions)

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
    
    # Start a thread to update metrics after processing
    threading.Thread(target=update_server_metrics, args=(best_server["id"], response_time)).start()

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate username and password
        user_row = users_df.loc[users_df['username'] == username]
        if not user_row.empty:
            user_data = user_row.iloc[0]
            if password == user_data['password']:  # Compare plaintext passwords
                user = User(id=user_row.index[0], username=user_data['username'], password=user_data['password'])
                login_user(user)
                flash('Login Successful!', 'success')  # Success alert
                return redirect(url_for('account'))
            else:
                flash('Invalid password. Please try again.', 'danger')  # Danger alert
        else:
            flash('Invalid username. Please try again.', 'danger')  # Danger alert
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    global users_df  # Declare users_df as global at the beginning of the function
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        user_row = users_df.loc[users_df['username'] == username]
        if not user_row.empty:
            flash('Username already exists', 'danger')  # Danger alert for duplicate username
            return redirect(url_for('register'))

        # Add the new user to the DataFrame using pd.concat
        new_user = pd.DataFrame([{
            'first_name': firstname,
            'last_name': lastname,
            'username': username,
            'password': password
        }])
        users_df = pd.concat([users_df, new_user], ignore_index=True)

        # Save the updated DataFrame back to the CSV file
        users_df.to_csv(USER_CREDENTIALS_FILE, index=False)

        flash('Registration successful! Please log in.', 'success')  # Success alert
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/api/get-balance', methods=['GET'])
@login_required
def get_balance():
    # Get the current user's username
    username = current_user.username
    print(f"Getting balance for user: {username}")  # Debug log

    try:
        # Read the transactions file
        transactions_df = pd.read_csv(TRANSACTIONS_FILE)
        print(f"CSV file loaded, shape: {transactions_df.shape}")  # Debug log
        
        # Check if the username exists in the dataframe
        user_exists = username in transactions_df['username'].values
        print(f"User exists in transactions: {user_exists}")  # Debug log
        
        # Filter transactions for the logged-in user
        user_transactions = transactions_df[transactions_df['username'] == username]
        print(f"Found {len(user_transactions)} transactions for user")  # Debug log
        
        if not user_transactions.empty:
            # Get the latest dynamic_balance from the last transaction
            latest_balance = user_transactions.iloc[-1]['dynamic_balance']
            print(f"Latest balance: {latest_balance}")  # Debug log
            return jsonify({"balance": float(latest_balance)})
        else:
            print("No transactions found, returning 0")  # Debug log
            return jsonify({"balance": 0.0})
    except Exception as e:
        print(f"Error in get_balance: {str(e)}")  # Debug log
        return jsonify({"balance": 0.0, "error": str(e)})

@app.route('/api/get-user-transactions', methods=['GET'])
@login_required
def get_user_transactions():
    username = current_user.username

    # Use load balancer to route the request
    best_server = select_best_server()
    if best_server:
        start_time = time.time()
        try:
            with lock:
                best_server["active_connections"] += 1
            
            # Normally we'd forward to the server, but for now we'll process it locally
            # and simulate using the load balancer
            transactions_df = pd.read_csv(TRANSACTIONS_FILE)
            user_transactions = transactions_df[transactions_df['username'] == username]
            transactions = user_transactions.to_dict(orient='records')
            
            response_time = time.time() - start_time
            # Update metrics in a separate thread
            threading.Thread(target=update_server_metrics, args=(best_server["id"], response_time)).start()
            
            return jsonify({
                "transactions": transactions,
                "served_by": best_server["url"],
                "response_time": response_time
            })
        except Exception as e:
            print(f"Error in /api/get-user-transactions: {str(e)}")
            return jsonify({"error": "Unable to fetch transactions"}), 500
    else:
        return jsonify({"error": "No available servers"}), 503

@app.route('/api/get-last-5-transactions', methods=['GET'])
@login_required
def get_last_5_transactions():
    username = current_user.username
    print(f"Fetching transactions for user: {username}")

    # Check if the file exists
    import os
    if not os.path.exists(TRANSACTIONS_FILE):
        print(f"Error: Transactions file not found at {TRANSACTIONS_FILE}")
        return jsonify({"error": "Transactions file not found"}), 500
    
    best_server = select_best_server()
    if best_server:
        start_time = time.time()
        try:
            with lock:
                best_server["active_connections"] += 1
            
            # Process request locally but simulate load balancing
            transactions_df = pd.read_csv(TRANSACTIONS_FILE)
            user_transactions = transactions_df[transactions_df['username'] == username]
            user_transactions = user_transactions.sort_values(by='time_of_transaction', ascending=False)
            
            # Convert the DataFrame to records and handle NaN values
            last_5_transactions = user_transactions.head(5).fillna("").to_dict(orient='records')
            
            # Ensure all numeric values are properly serialized to JSON
            for transaction in last_5_transactions:
                for key, value in transaction.items():
                    if pd.isna(value):
                        transaction[key] = None
            
            response_time = time.time() - start_time
            # Update metrics in a separate thread
            threading.Thread(target=update_server_metrics, args=(best_server["id"], response_time)).start()
            
            return jsonify({
                "transactions": last_5_transactions,
                "served_by": best_server["url"],
                "response_time": response_time
            })
            response.headers['Content-Type'] = 'application/json'
            return response   

        except Exception as e:
            print(f"Error in /api/get-last-5-transactions: {str(e)}")
            return jsonify({"error": f"Unable to fetch transactions: {str(e)}"}), 500
    else:
        return jsonify({"error": "No available servers"}), 503

@app.route('/account')
@login_required
def account():
    username = current_user.username
    print(f"Current logged-in user: {username}")  # Debug log

    try:
        # Read the transactions file
        transactions_df = pd.read_csv(TRANSACTIONS_FILE)

        # Get the user's full name and other details from the transactions file
        user_row = transactions_df[transactions_df['username'] == username]
        if not user_row.empty:
            full_name = user_row.iloc[0]['name']  # Get the first occurrence of the name
            email = user_row.iloc[0].get('email', 'N/A')
            phone = user_row.iloc[0].get('phone', 'N/A')
        else:
            full_name = username  # Fallback to username if no name is found
            email = 'N/A'
            phone = 'N/A'

        # Calculate the user's balance
        balance = calculate_balance(username)

        # Calculate total transactions, total incoming, and total outgoing
        user_transactions = transactions_df[transactions_df['username'] == username]
        total_transactions = len(user_transactions)
        total_incoming = user_transactions[user_transactions['transaction_type'] == 'incoming']['amount'].sum()
        total_outgoing = user_transactions[user_transactions['transaction_type'] == 'outgoing']['amount'].sum()

        # Get server health for admin display
        servers_health = backend_servers

        return render_template(
            'account.html', 
            full_name=full_name, 
            email=email,
            phone=phone,
            initial_balance=balance, 
            total_transactions=total_transactions, 
            total_incoming=total_incoming, 
            total_outgoing=total_outgoing, 
            servers=servers_health
        )
    except Exception as e:
        print(f"Error in /account route: {str(e)}")
        flash('An error occurred while loading your account details.', 'danger')
        return redirect(url_for('login'))

@app.route('/transactions', methods=['GET'])
@login_required
def transactions():
    username = current_user.username

    try:
        # Read the transactions file
        transactions_df = pd.read_csv(TRANSACTIONS_FILE)

        # Filter transactions for the logged-in user
        user_transactions = transactions_df[transactions_df['username'] == username]

        # Pass the user's transactions to the template
        return render_template('transactions.html', transactions=user_transactions.to_dict(orient='records'))
    except Exception as e:
        print(f"Error in /transactions route: {str(e)}")
        flash('Unable to load transactions.', 'danger')
        return redirect(url_for('account'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/transfer', methods=['GET'])
@login_required
def transfer():
    return render_template('transfer.html')

@app.route('/transfer', methods=['POST'])
@login_required
def transfer_funds():
    recipient = request.form.get('recipient')
    amount = request.form.get('amount')

    # Use the load balancer to handle the transfer request
    best_server = select_best_server()
    if best_server:
        start_time = time.time()
        with lock:
            best_server["active_connections"] += 1
        
        try:
            # Convert amount to float
            amount = float(amount)

            # Get the current user's username
            sender = current_user.username

            # Get the current timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Append the transaction to the CSV file
            with open(TRANSACTIONS_FILE, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write sender's outgoing transaction
                writer.writerow([sender, 'outgoing', amount, timestamp, ''])
                # Write recipient's incoming transaction
                writer.writerow([recipient, 'incoming', amount, timestamp, ''])

            response_time = time.time() - start_time
            # Update metrics in a separate thread
            threading.Thread(target=update_server_metrics, args=(best_server["id"], response_time)).start()
            
            flash(f'Transfer successful! Processed by server {best_server["url"]}', 'success')
        except Exception as e:
            print(f"Error during transfer: {e}")
            flash('Transfer failed. Please try again.', 'danger')
    else:
        flash('No available servers to process your request.', 'danger')

    return redirect(url_for('transfer'))

@app.route('/admin/servers', methods=['GET'])
@login_required
def admin_servers():
    return render_template('admin_servers.html', servers=backend_servers)

@app.route('/api/get-all-user-transactions', methods=['GET'])
def get_all_user_transactions():
    try:
        # Read the transactions file
        transactions_df = pd.read_csv(r'd:\Apna_Bank\realistic_indian_transactions.csv')

        # Group by username and calculate metrics
        grouped = transactions_df.groupby('username').agg(
            total_transactions=('transaction_type', 'count'),
            total_incoming=('amount', lambda x: x[transactions_df['transaction_type'] == 'incoming'].sum()),
            total_outgoing=('amount', lambda x: x[transactions_df['transaction_type'] == 'outgoing'].sum())
        ).reset_index()

        # Convert to a list of dictionaries
        user_metrics = grouped.to_dict(orient='records')

        return jsonify({"users": user_metrics})
    except Exception as e:
        print(f"Error in /api/get-all-user-transactions: {str(e)}")
        return jsonify({"error": "Unable to fetch user transactions"}), 500

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Handle profile update logic here
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        # Update user details in the database or CSV
        user_index = users_df[users_df['username'] == current_user.username].index[0]
        users_df.loc[user_index, 'full_name'] = full_name
        users_df.loc[user_index, 'email'] = email
        users_df.loc[user_index, 'phone'] = phone
        users_df.to_csv(USER_CREDENTIALS_FILE, index=False)

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    # Load current user details
    user_row = users_df[users_df['username'] == current_user.username].iloc[0]
    return render_template('editprofile.html', user=user_row)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        user_index = users_df[users_df['username'] == current_user.username].index[0]
        users_df.loc[user_index, 'full_name'] = full_name
        users_df.loc[user_index, 'email'] = email
        users_df.loc[user_index, 'phone'] = phone
        users_df.to_csv(USER_CREDENTIALS_FILE, index=False)

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('edit_profile'))

    user_row = users_df[users_df['username'] == current_user.username].iloc[0]
    return render_template('edit.html', user=user_row)

if __name__ == '__main__':
    app.run(debug=True)