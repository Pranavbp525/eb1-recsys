import uvicorn
import os
from fastapi import FastAPI
from models import UserProfile
from main import find_eb1a_lawyers

# --- Start of Debugging Code ---
print("--- Verifying Environment Variables at Startup ---")
perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
openrouter_key = os.environ.get("OPENROUTER_API_KEY")

if perplexity_key:
    print("SUCCESS: PERPLEXITY_API_KEY is loaded.:")
else:
    print("ERROR: PERPLEXITY_API_KEY is NOT found.")

if openrouter_key:
    print("SUCCESS: OPENROUTER_API_KEY is loaded.")
else:
    print("ERROR: OPENROUTER_API_KEY is NOT found.")
print("----------------------------------------------")
# --- End of Debugging Code ---

app = FastAPI(
    title="EB-1A Lawyer Recommendation API",
    description="An API to recommend EB-1A immigration lawyers based on user profiles.",
    version="1.0.0"
)

@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "ok"}

@app.post("/recommendations", tags=["Recommendations"])
async def get_recommendations(user_profile: UserProfile):
    """
    Takes a user profile and returns a list of recommended EB-1A lawyers.
    """
    full_output = await find_eb1a_lawyers(user_profile)
    
    # Extract just the lawyer profiles from the full output
    lawyer_profiles = [rec["lawyer"] for rec in full_output.get("recommendations", [])]
    
    return lawyer_profiles

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
