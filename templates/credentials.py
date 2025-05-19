from faker import Faker
import pandas as pd

# Initialize Faker
fake = Faker()

# List of Indian first and last names
indian_first_names = [
    "Amit", "Rahul", "Priya", "Anjali", "Rohit", "Deepak", "Sanjay", "Rajesh", "Sunita", "Kavita"
]
indian_last_names = [
    "Sharma", "Verma", "Gupta", "Patel", "Reddy", "Mehta", "Chopra", "Singh", "Nair", "Iyer"
]

# Function to create username and password dataset
def generate_user_credentials(indian_first_names, indian_last_names, num_users=1000):
    credentials_dataset = []
    for _ in range(num_users):
        first_name = fake.random_element(indian_first_names)
        last_name = fake.random_element(indian_last_names)
        username = f"{first_name.lower()}.{last_name.lower()}"
        password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        credentials_dataset.append({
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "password": password
        })
    return pd.DataFrame(credentials_dataset)

# Generate the dataset
credentials_dataset = generate_user_credentials(indian_first_names, indian_last_names)

# Save to a CSV file
file_path = "user_credentials.csv"
credentials_dataset.to_csv(file_path, index=False)

# Print the file location
print(f"The credentials dataset has been saved to the following location:\n{file_path}")
