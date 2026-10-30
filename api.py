from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from quiz_engine import QuizEngine

app = FastAPI(title="QuizUp API")

engine = QuizEngine()


@app.get("/")
def home():
    return {"message": "QuizUp API is running!"}


@app.get("/categories")
def categories():
    return engine.get_categories()


@app.get("/questions")
def questions(category: str = "Technology",
              difficulty: str = "easy",
              count: int = 5):

    session = engine.create_session(
        category=category,
        difficulty=difficulty,
        question_count=count,
        shuffle_options=False
    )

    return [
        {
            "id": q.id,
            "category": q.category,
            "difficulty": q.difficulty,
            "question": q.question_text,
            "options": q.options
        }
        for q in session.questions
    ]
