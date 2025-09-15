from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import os

app = FastAPI()

# --- Database Connection ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

class Feedback(BaseModel):
    interaction_id: str
    feedback_score: int # e.g., 1 for up, -1 for down

@app.on_event("startup")
def startup_event():
    """
    On startup, simply check the database connection.
    The bot-service is responsible for creating the table.
    """
    try:
        with engine.connect() as connection:
            # We just need to verify the connection is alive.
            connection.execute(text("SELECT 1"))
        print("Database connection successful.")
    except Exception as e:
        print(f"Database connection failed during startup: {e}")
        # The pod will likely fail to start, which is what we want
        # if the database is not available.
        raise e

@app.post("/feedback")
def receive_feedback(feedback: Feedback):
    """
    Receives feedback and updates the corresponding interaction in the database.
    """
    try:
        with engine.connect() as connection:
            # Use text() to construct the SQL statement safely
            stmt = text("UPDATE interactions SET feedback = :score WHERE interaction_id = :id")
            connection.execute(
                stmt,
                {"score": feedback.feedback_score, "id": feedback.interaction_id}
            )
            connection.commit()
        return {"status": "success", "interaction_id": feedback.interaction_id}
    except Exception as e:
        # Log the error for debugging
        print(f"Error updating feedback for interaction {feedback.interaction_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating feedback: {str(e)}")
