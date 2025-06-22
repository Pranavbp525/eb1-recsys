import requests
import json

# Define the API endpoint
url = "http://127.0.0.1:8000/recommendations"

# Example user profile (based on the example in main.py)
user_profile = {
    "name": "Dr. Rajesh Patel",
    "occupation": "AI Research Scientist",
    "industry": "Technology",
    "nationality": "Indian",
    "budget_range": {"min": 15000, "max": 30000},
    "location_preference": "California",
    "timeline_urgency": "moderate",
    "achievements": [
        "Published 45 papers in top AI conferences",
        "Led team that developed breakthrough NLP model",
        "3 patents in machine learning",
        "Invited speaker at 10+ international conferences"
    ],
    "publications": 45,
    "citations": 1200,
    "awards": ["Best Paper Award NeurIPS 2023", "Google Research Award 2022"],
    "priority_factors": ["success_rate", "industry_expertise", "timeline"]
}

# Set headers
headers = {
    "Content-Type": "application/json"
}

# Send the POST request
print("Sending request to the API...")
try:
    response = requests.post(url, data=json.dumps(user_profile), headers=headers)
    response.raise_for_status()  # Raise an exception for bad status codes

    # Print the response
    print("\nAPI Response:")
    print(json.dumps(response.json(), indent=2))

except requests.exceptions.RequestException as e:
    print(f"\nAn error occurred: {e}")
    print("Please ensure the FastAPI server is running.") 