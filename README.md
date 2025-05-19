# Banking Management System with Hybrid Load Balancer

## Overview
This project is a Flask-based Banking Management System that incorporates a hybrid load balancer for efficient request routing. It provides features like user authentication, transaction management, and server health monitoring.

## Features
- **User Authentication**: Login and registration functionality.
- **Transaction Management**: View balance, transaction history, and perform fund transfers.
- **Hybrid Load Balancer**: Routes requests to backend servers based on active connections and response time.
- **Server Management**: Register, deregister, and monitor backend servers.
- **Admin Metrics**: View server metrics and user transaction summaries.

## Technologies Used
- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS (via Flask templates)
- **Database**: CSV files for user credentials and transactions
- **Load Balancer**: Custom hybrid algorithm using threading and server metrics

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/rishitverma0812/Banking_Management_System_With_Hybrid_Load_Balancer.git
   ```
2. Navigate to the project directory:
   ```bash
   cd Banking_Management_System_With_Hybrid_Load_Balancer
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Flask application:
   ```bash
   python app.py
   ```
5. Open your browser and navigate to `http://127.0.0.1:5000`.

## Usage
### User Features
- **Login**: Access your account using your username and password.
- **Register**: Create a new account.
- **View Balance**: Check your current account balance.
- **Transaction History**: View your past transactions.
- **Fund Transfer**: Transfer money to other users.

### Admin Features
- **Server Metrics**: Monitor backend server health and performance.
- **Register/Deregister Servers**: Add or remove backend servers.

## File Structure
- `app.py`: Main Flask application.
- `user_credentials.csv`: Stores user credentials.
- `realistic_indian_transactions.csv`: Stores transaction data.
- `templates/`: HTML templates for the web interface.
- `static/`: Static files like CSS and JavaScript.

## API Endpoints
- **User Authentication**:
  - `POST /login`: Login to the system.
  - `POST /register`: Register a new user.
- **Transaction Management**:
  - `GET /api/get-balance`: Get the current balance.
  - `GET /api/get-user-transactions`: Get all user transactions.
  - `GET /api/get-last-5-transactions`: Get the last 5 transactions.
- **Load Balancer**:
  - `POST /request`: Route a request to the best server.
  - `GET /health`: Check server health.
- **Admin**:
  - `GET /admin/servers`: View server metrics.
  - `POST /register`: Register a new server.
  - `POST /deregister`: Deregister a server.

## License
This project is licensed under the MIT License. Feel free to use and modify it as needed.
