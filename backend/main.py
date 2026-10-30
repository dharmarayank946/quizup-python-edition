"""QuizUp Python Edition — FastAPI Production Web API & Microservice.
==================================================================
REST microservice for the QuizUp trivia platform:
- Category discovery & question counts
- Daily Spark 5-question challenge
- Session generation (Exam & Learning modes)
- Server-side answer validation, XP calculation & coin rewards
- Hall of Fame leaderboard and player profile management
"""

import os
import sys
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure root QuizUp modules are in python sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from models import Question, PlayerProgress, QuizSession, PREDEFINED_ACHIEVEMENTS, AVAILABLE_AVATARS
from quiz_engine import QuizEngine, CATEGORIES
from storage import StorageManager

app = FastAPI(
    title="QuizUp Trivia API",
    description="Next-generation trivia gaming REST microservice with server-side validation and leaderboards.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = StorageManager()
engine = QuizEngine(storage_manager=storage)

# In-memory active game sessions
active_sessions: Dict[str, Dict[str, Any]] = {}

# Default leaderboard seed data
DEFAULT_LEADERBOARD = [
    {"rank": 1, "name": "Elena Rostova", "avatar": "👑", "level": 14, "xp": 4820, "coins": 1250, "accuracy": 94.2},
    {"rank": 2, "name": "Aarav Sharma", "avatar": "🚀", "level": 12, "xp": 3950, "coins": 980, "accuracy": 91.5},
    {"rank": 3, "name": "Kenji Sato", "avatar": "🧠", "level": 11, "xp": 3410, "coins": 820, "accuracy": 88.0},
    {"rank": 4, "name": "Sophia Miller", "avatar": "🦉", "level": 9, "xp": 2740, "coins": 640, "accuracy": 85.4},
    {"rank": 5, "name": "Lucas Silva", "avatar": "⚡", "level": 8, "xp": 2180, "coins": 510, "accuracy": 82.1}
]


# ---------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------
class SessionStartRequest(BaseModel):
    category: str = Field("Technology", example="Technology")
    difficulty: str = Field("easy", example="easy")
    mode: str = Field("learning", example="learning")  # "learning" or "exam"
    num_questions: int = Field(5, ge=3, le=20, example=5)


class AnswerSubmission(BaseModel):
    question_id: str
    selected_index: int
    time_spent_sec: float = 0.0


class SessionSubmitRequest(BaseModel):
    session_id: str
    category: Optional[str] = "Technology"
    difficulty: Optional[str] = "easy"
    mode: Optional[str] = "learning"
    answers: List[AnswerSubmission]
    player_name: Optional[str] = "Challenger"


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=32)
    avatar: Optional[str] = Field(None, max_length=4)


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe for Render and deployment orchestrators."""
    return {
        "status": "healthy",
        "service": "quizup-api",
        "version": "2.0.0",
        "total_questions": len(engine.questions),
        "categories_available": len(CATEGORIES)
    }


@app.get("/api/v1/quiz/categories", tags=["Quiz"])
def get_categories():
    """Retrieve all available categories with question counts and difficulty breakdown."""
    stats = {}
    for cat in CATEGORIES:
        q_list = [q for q in engine.questions if q.category.lower() == cat.lower()]
        easy = sum(1 for q in q_list if q.difficulty.lower() == "easy")
        med = sum(1 for q in q_list if q.difficulty.lower() == "medium")
        hard = sum(1 for q in q_list if q.difficulty.lower() == "hard")
        stats[cat] = {
            "name": cat,
            "total_questions": len(q_list),
            "difficulties": {"easy": easy, "medium": med, "hard": hard}
        }
    return {
        "categories": CATEGORIES,
        "category_details": stats
    }


@app.get("/api/v1/quiz/daily-spark", tags=["Quiz"])
def get_daily_spark():
    """Fetch today's 5-question Daily Spark challenge."""
    session = engine.create_daily_spark_session()
    questions = []
    for q in session.questions:
        questions.append({
            "id": q.id,
            "category": q.category,
            "difficulty": q.difficulty,
            "question": q.question_text,
            "options": q.options
        })
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "mode": "daily_spark",
        "category": "Daily Spark ⚡",
        "difficulty": "medium",
        "questions": session.questions,
        "created_at": datetime.now()
    }
    return {
        "session_id": session_id,
        "mode": "daily_spark",
        "title": "Daily Spark ⚡",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "questions": questions
    }


@app.post("/api/v1/quiz/session/start", tags=["Quiz"])
def start_quiz_session(req: SessionStartRequest):
    """Start a quiz session with category, difficulty, and mode."""
    session = engine.create_session(
        category=req.category,
        difficulty=req.difficulty,
        question_count=req.num_questions,
        mode=req.mode
    )
    if not session or not session.questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No questions found for category '{req.category}'."
        )

    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "mode": req.mode,
        "category": req.category,
        "difficulty": req.difficulty,
        "questions": session.questions,
        "created_at": datetime.now()
    }

    client_questions = []
    for q in session.questions:
        item = {
            "id": q.id,
            "category": q.category,
            "difficulty": q.difficulty,
            "question": q.question_text,
            "options": q.options
        }
        if req.mode == "learning":
            item["correct_index"] = q.correct_index
            item["explanation"] = q.explanation
        client_questions.append(item)

    return {
        "session_id": session_id,
        "mode": req.mode,
        "category": req.category,
        "difficulty": req.difficulty,
        "num_questions": len(client_questions),
        "questions": client_questions
    }


@app.post("/api/v1/quiz/session/submit", tags=["Quiz"])
def submit_quiz_session(req: SessionSubmitRequest):
    """Submit quiz answers, compute final score, XP, coins, and check achievements."""
    sess = active_sessions.get(req.session_id)
    if not sess:
        q_dict = {q.id: q for q in engine.questions}
        cat = req.category or "Technology"
        diff = req.difficulty or "easy"
        mode = req.mode or "learning"
    else:
        q_dict = {q.id: q for q in sess["questions"]}
        cat = sess.get("category", "Technology")
        diff = sess.get("difficulty", "easy")
        mode = sess.get("mode", "learning")

    results_details = []
    correct_count = 0
    total = len(req.answers)

    for ans in req.answers:
        q = q_dict.get(ans.question_id)
        if not q:
            continue
        is_correct = (ans.selected_index == q.correct_index)
        if is_correct:
            correct_count += 1
        results_details.append({
            "question_id": q.id,
            "question": q.question_text,
            "options": q.options,
            "selected_index": ans.selected_index,
            "correct_index": q.correct_index,
            "is_correct": is_correct,
            "explanation": q.explanation
        })

    accuracy = round((correct_count / max(1, total)) * 100, 1)
    base_xp = correct_count * 20
    streak_bonus = 25 if accuracy >= 80 else 0
    perfect_bonus = 50 if accuracy == 100 else 0
    total_xp = base_xp + streak_bonus + perfect_bonus
    coins_earned = correct_count * 10 + (25 if accuracy >= 80 else 0)

    # Record in PlayerProgress
    progress = storage.load_progress()
    session_data = {
        "score": correct_count,
        "total": total,
        "category": cat,
        "difficulty": diff,
        "mode": mode,
        "percentage": accuracy,
        "xp_earned": total_xp,
        "coins_earned": coins_earned,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    newly_unlocked = progress.record_session(session_data)
    storage.save_progress(progress)

    if req.session_id in active_sessions:
        del active_sessions[req.session_id]

    curr_xp, span_xp, pct_xp = progress.level_progress

    return {
        "session_id": req.session_id,
        "total_questions": total,
        "correct_answers": correct_count,
        "accuracy_percentage": accuracy,
        "xp_earned": total_xp,
        "coins_earned": coins_earned,
        "new_level": progress.level,
        "level_title": progress.level_title,
        "total_xp": progress.xp,
        "total_coins": progress.coins,
        "level_progress_pct": pct_xp,
        "newly_unlocked_achievements": newly_unlocked,
        "results": results_details
    }


@app.get("/api/v1/quiz/leaderboard", tags=["Social"])
def get_leaderboard():
    """Retrieve global Hall of Fame rankings."""
    progress = storage.load_progress()
    lb = list(DEFAULT_LEADERBOARD)
    player_entry = {
        "rank": 0,
        "name": progress.player_name,
        "avatar": progress.avatar,
        "level": progress.level,
        "xp": progress.xp,
        "coins": progress.coins,
        "accuracy": progress.overall_accuracy
    }
    lb.append(player_entry)
    lb.sort(key=lambda x: x["xp"], reverse=True)
    for idx, entry in enumerate(lb, start=1):
        entry["rank"] = idx

    return {
        "leaderboard": lb[:10],
        "player_rank": next((e["rank"] for e in lb if e["name"] == progress.player_name), len(lb))
    }


@app.get("/api/v1/quiz/profile", tags=["Profile"])
def get_player_profile():
    """Retrieve current player progress, stats, and achievements."""
    progress = storage.load_progress()
    curr_xp, span_xp, pct_xp = progress.level_progress
    return {
        "player_name": progress.player_name,
        "avatar": progress.avatar,
        "level": progress.level,
        "level_title": progress.level_title,
        "xp": progress.xp,
        "level_progress_pct": pct_xp,
        "coins": progress.coins,
        "quizzes_played": progress.quizzes_played,
        "total_questions": progress.total_questions,
        "total_correct": progress.total_correct,
        "overall_accuracy": progress.overall_accuracy,
        "best_scores": progress.best_scores,
        "history": progress.history[:10],
        "achievements": PREDEFINED_ACHIEVEMENTS,
        "available_avatars": AVAILABLE_AVATARS
    }


@app.post("/api/v1/quiz/profile", tags=["Profile"])
def update_player_profile(req: ProfileUpdateRequest):
    """Update player display name or avatar."""
    progress = storage.load_progress()
    if req.name:
        progress.player_name = req.name.strip()
    if req.avatar:
        progress.avatar = req.avatar.strip()
    storage.save_progress(progress)
    return {
        "message": "Profile updated successfully.",
        "player_name": progress.player_name,
        "avatar": progress.avatar
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
