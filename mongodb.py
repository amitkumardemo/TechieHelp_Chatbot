from pymongo import MongoClient
from hashlib import sha256
from datetime import datetime

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI
db = client["mongodb"]  # Replace with your database name
users_collection = db["users"]  # For storing user credentials
chat_collection = db["chat_history"]  # For storing chat history

# Store user in the database
def store_user(email, password):
    """
    Stores a new user in the MongoDB database.
    :param email: User's email
    :param password: User's password (plain text, will be hashed before storage)
    """
    hashed_password = sha256(password.encode()).hexdigest()
    users_collection.insert_one({"email": email, "password": hashed_password})

# Validate user credentials
def validate_user(email, password):
    """
    Validates if a user exists in the database with the given credentials.
    :param email: User's email
    :param password: User's password (plain text, will be hashed before comparison)
    :return: True if user exists and credentials match, False otherwise
    """
    hashed_password = sha256(password.encode()).hexdigest()
    user = users_collection.find_one({"email": email, "password": hashed_password})
    return user is not None

# Store chat messages in the database
def store_message(query, response):
    """
    Stores a chat message (query and response) in the MongoDB database.
    :param query: User's query
    :param response: AI's response
    """
    message = {
        "query": query,
        "response": response,
        "timestamp": datetime.now()
    }
    chat_collection.insert_one(message)

# Fetch chat history
def fetch_chat_history():
    """
    Fetches chat history from the MongoDB database, sorted by timestamp in descending order.
    :return: List of chat messages (query, response, timestamp)
    """
    messages = chat_collection.find().sort("timestamp", -1)
    chat_history = [
        {
            "query": msg["query"],
            "response": msg["response"],
            "timestamp": msg["timestamp"]
        }
        for msg in messages
    ]
    return chat_history
