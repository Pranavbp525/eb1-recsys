# EB-1A Lawyer Recommendation API

This project provides a FastAPI-based API that recommends EB-1A immigration lawyers based on a user's profile. The recommendation engine is powered by LangGraph and uses AI models from Perplexity and OpenRouter.

## Quickstart with Docker

This is the easiest way to get the API running.

### Prerequisites

*   Docker installed on your machine.
*   An internet connection.
*   Install requirements using pip install -r requirements.txt

### Step 1: Create the Environment File

The application requires API keys for its AI services. Create a file named `.env` in the root of this project and add your keys like this:

```env
# .env
PERPLEXITY_API_KEY="YOUR_PERPLEXITY_API_KEY"
OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY"
```

### Step 2:Run Uvicorn

Open your terminal and navigate to api dir
```bash
cd api
```

Then run :
```bash
uvicorn run api:app --reload
```

Your api is running on port 8000


### Step 4: Test the API

You can test the API by sending a POST request to the `/recommendations` endpoint.

#### Input Payload

The endpoint expects a JSON object with the following `UserProfile` structure:

```json
{
  "name": "string",
  "occupation": "string",
  "industry": "string",
  "nationality": "string",
  "budget_range": {
    "min": "number",
    "max": "number"
  },
  "location_preference": "string (optional)",
  "timeline_urgency": "string (e.g., 'urgent', 'moderate', 'flexible')",
  "achievements": [
    "string"
  ],
  "publications": "integer (optional)",
  "citations": "integer (optional)",
  "awards": [
    "string (optional)"
  ],
  "priority_factors": [
    "string (e.g., 'success_rate', 'cost', 'location')"
  ]
}
```

The `api/test_client.py` script is pre-configured with a sample payload. You can run it directly:

```bash
python api/test_client.py
```

#### Output Response

If successful, the API will return a `200 OK` status and a JSON array of `LawyerProfile` objects:

```json
[
  {
    "name": "string",
    "firm": "string",
    "contact_info": {
      "email": "string",
      "phone": "string",
      "website": "string"
    }
  }
]
```


### Managing the Container

*   **To see the logs:** `docker logs eb1a-api`
*   **To stop the container:** `docker stop eb1a-api`
*   **To remove the container:** `docker rm eb1a-api` 
