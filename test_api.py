import requests
import json

# The URL where our FastAPI server is running
url = "http://127.0.0.1:8000/webhook"

# The data we want to send, matching the structure of our Pydantic model
payload = {
    "message": "I need to schedule a dentist appointment for next Tuesday"
}

print(f"Sending test message to {url}...")

try:
    # Make the POST request to our API
    response = requests.post(url, json=payload)

    # Raise an exception if the request returned an error code
    response.raise_for_status() 

    # Print the JSON response from the server
    print("Server responded successfully!")
    print("Response JSON:", response.json())

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")