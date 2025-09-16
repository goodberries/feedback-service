from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx

app = FastAPI()

# --- Configuration ---
INTERACTIONS_SERVICE_URL = os.getenv("INTERACTIONS_SERVICE_URL", "http://interactions-service:8003")

class Feedback(BaseModel):
    interaction_id: str
    feedback_score: int # e.g., 1 for up, -1 for down

@app.post("/feedback")
async def receive_feedback(feedback: Feedback):
    """
    Receives feedback and forwards it to the interactions-service.
    """
    try:
        feedback_update_url = f"{INTERACTIONS_SERVICE_URL}/interactions/{feedback.interaction_id}/feedback"
        async with httpx.AsyncClient() as client:
            response = await client.patch(feedback_update_url, json={"feedback_score": feedback.feedback_score})
            response.raise_for_status()
        
        return {"status": "success", "interaction_id": feedback.interaction_id}
    
    except httpx.HTTPStatusError as e:
        # Log and forward the error from the downstream service
        print(f"Error from interactions-service: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Error from interactions-service: {e.response.text}")
    except Exception as e:
        # Log the error for debugging
        print(f"An unexpected error occurred while updating feedback for interaction {feedback.interaction_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")
