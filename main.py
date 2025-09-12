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
    On startup, connect to the database and create the table if it doesn't exist.
    """
    try:
        with engine.connect() as connection:
            # This is a simplified schema for Phase 2
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS interactions (
                    interaction_id UUID PRIMARY KEY,
                    user_query TEXT,
                    bot_response TEXT,
                    feedback SMALLINT DEFAULT 0,
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                );
            """))
        print("Database connection successful and table checked/created.")
    except Exception as e:
        print(f"Database connection failed: {e}")
        # In a real app, you might want to handle this more gracefully
        # For now, we'll let it fail and see the error in the logs.

@app.post("/feedback")
def receive_feedback(feedback: Feedback):
    """
    Receives feedback and updates the corresponding interaction in the database.
    """
    try:
        with engine.connect() as connection:
            connection.execute(
                text("UPDATE interactions SET feedback = :score WHERE interaction_id = :id"),
                {"score": feedback.feedback_score, "id": feedback.interaction_id}
            )
            connection.commit()
        return {"status": "success", "interaction_id": feedback.interaction_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating feedback: {str(e)}")
