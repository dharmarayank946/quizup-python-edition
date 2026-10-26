"""
QuizUp Python Edition - Storage Manager
======================================
Provides resilient data persistence for:
- Quiz questions (data/questions.json)
- Player progress, lifetime stats, and history (data/progress.json)

Features:
- Safe JSON serialization & deserialization.
- Corrupted JSON detection and automatic recovery.
- Atomic writes via temporary files to prevent data corruption.
- Built-in embedded fallback questions to guarantee uninterrupted operation.
"""

import json
import os
import shutil
from typing import List, Optional

from models import Question, PlayerProgress


# Default relative data directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_QUESTIONS_PATH = os.path.join(DATA_DIR, "questions.json")
DEFAULT_PROGRESS_PATH = os.path.join(DATA_DIR, "progress.json")

# Minimal emergency fallback questions if questions.json is deleted or unreadable
FALLBACK_QUESTIONS = [
    {
        "id": "fallback_01",
        "category": "Technology",
        "difficulty": "easy",
        "question": "Which programming language was created by Guido van Rossum and released in 1991?",
        "options": ["Java", "C++", "Python", "Ruby"],
        "correct_index": 2,
        "explanation": "Guido van Rossum developed Python in the late 1980s and officially released it in 1991."
    },
    {
        "id": "fallback_02",
        "category": "Academics",
        "difficulty": "easy",
        "question": "What is the chemical formula for pure water?",
        "options": ["CO2", "H2O", "O2", "NaCl"],
        "correct_index": 1,
        "explanation": "Pure water is made of two hydrogen atoms and one oxygen atom (H2O)."
    },
    {
        "id": "fallback_03",
        "category": "General Knowledge",
        "difficulty": "easy",
        "question": "What is the capital city of France?",
        "options": ["Rome", "Berlin", "Paris", "Madrid"],
        "correct_index": 2,
        "explanation": "Paris is the capital and largest city of France."
    },
    {
        "id": "fallback_04",
        "category": "Competitive Exams",
        "difficulty": "easy",
        "question": "What is 15% of 200?",
        "options": ["20", "25", "30", "35"],
        "correct_index": 2,
        "explanation": "15% of 200 = (15 / 100) * 200 = 30."
    },
    {
        "id": "fallback_05",
        "category": "Sports",
        "difficulty": "easy",
        "question": "How many players are on the pitch for one team in a standard football (soccer) match?",
        "options": ["9", "10", "11", "12"],
        "correct_index": 2,
        "explanation": "Each football team fields 11 players including the goalkeeper."
    },
    {
        "id": "fallback_06",
        "category": "Entertainment",
        "difficulty": "easy",
        "question": "Which band recorded the famous rock ballad 'Bohemian Rhapsody' in 1975?",
        "options": ["The Beatles", "Queen", "Led Zeppelin", "Pink Floyd"],
        "correct_index": 1,
        "explanation": "Queen composed and performed Bohemian Rhapsody, written by Freddie Mercury."
    }
]


class StorageManager:
    """
    Manages loading and saving application data safely.
    """

    def __init__(
        self,
        questions_path: Optional[str] = None,
        progress_path: Optional[str] = None
    ) -> None:
        self.questions_path = questions_path or DEFAULT_QUESTIONS_PATH
        self.progress_path = progress_path or DEFAULT_PROGRESS_PATH
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create parent folders if they do not exist."""
        for path in (self.questions_path, self.progress_path):
            folder = os.path.dirname(os.path.abspath(path))
            os.makedirs(folder, exist_ok=True)

    def load_questions(self, filepath: Optional[str] = None) -> List[Question]:
        """
        Load questions from JSON. Recovers gracefully if file is missing or corrupted.
        """
        target = filepath or self.questions_path
        questions: List[Question] = []

        if not os.path.exists(target):
            # Attempt to write default fallback questions if file doesn't exist
            self._write_fallback_questions(target)

        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    raise ValueError("Questions file is empty.")
                raw_data = json.loads(content)

            # Handle both list of question dicts and {"questions": [...]} wrapper
            items = raw_data.get("questions", []) if isinstance(raw_data, dict) else raw_data
            if not isinstance(items, list):
                raise ValueError("Expected list of questions in JSON.")

            for item in items:
                try:
                    q = Question.from_dict(item)
                    questions.append(q)
                except Exception:
                    # Skip individually malformed questions
                    continue

        except (json.JSONDecodeError, ValueError, OSError):
            # Corrupted or unreadable JSON: use fallback questions
            questions = [Question.from_dict(item) for item in FALLBACK_QUESTIONS]

        # Final sanity check: if list is somehow still empty, load fallbacks
        if not questions:
            questions = [Question.from_dict(item) for item in FALLBACK_QUESTIONS]

        return questions

    def _write_fallback_questions(self, target: str) -> None:
        """Write embedded emergency questions to file."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
            payload = {
                "categories": ["Technology", "Academics", "General Knowledge", "Competitive Exams", "Sports", "Entertainment"],
                "difficulties": ["easy", "medium", "hard"],
                "questions": FALLBACK_QUESTIONS
            }
            with open(target, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def load_progress(self, filepath: Optional[str] = None) -> PlayerProgress:
        """
        Load player progress from JSON. Recovers gracefully if corrupted.
        """
        target = filepath or self.progress_path
        if not os.path.exists(target):
            default_progress = PlayerProgress()
            self.save_progress(default_progress, target)
            return default_progress

        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return PlayerProgress()
                data = json.loads(content)

            return PlayerProgress.from_dict(data)

        except (json.JSONDecodeError, ValueError, OSError):
            # Backup corrupted file so learner's history is not silently overwritten without trace
            backup_path = target + ".corrupted_bak"
            try:
                shutil.copyfile(target, backup_path)
            except OSError:
                pass

            # Return a fresh progress instance and save it cleanly
            fresh_progress = PlayerProgress()
            self.save_progress(fresh_progress, target)
            return fresh_progress

    def save_progress(self, progress: PlayerProgress, filepath: Optional[str] = None) -> bool:
        """
        Save player progress atomically using a temporary file and replace.
        """
        target = filepath or self.progress_path
        temp_target = target + ".tmp"
        try:
            os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
            with open(temp_target, "w", encoding="utf-8") as f:
                json.dump(progress.to_dict(), f, indent=2, ensure_ascii=False)

            # Atomic rename / replace
            os.replace(temp_target, target)
            return True
        except OSError:
            # Clean up temp file if failed
            if os.path.exists(temp_target):
                try:
                    os.remove(temp_target)
                except OSError:
                    pass
            return False

    def save_questions(self, questions: List[Question], filepath: Optional[str] = None) -> bool:
        """
        Persist a list of Question instances into JSON.
        """
        target = filepath or self.questions_path
        temp_target = target + ".tmp"
        try:
            os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
            payload = {
                "categories": list({q.category for q in questions}),
                "difficulties": list({q.difficulty for q in questions}),
                "questions": [q.to_dict() for q in questions]
            }
            with open(temp_target, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            os.replace(temp_target, target)
            return True
        except OSError:
            if os.path.exists(temp_target):
                try:
                    os.remove(temp_target)
                except OSError:
                    pass
            return False
