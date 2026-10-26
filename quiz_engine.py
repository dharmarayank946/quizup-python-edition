"""
QuizUp Python Edition - Quiz Engine (Enhanced Feature Parity Edition)
=====================================================================
Manages quiz generation, category filtering, difficulty selection,
randomized sampling, option shuffling, and special game modes:
- Learning Mode (Instant feedback & explanations)
- Exam Mode (Timed countdown assessment)
- Daily Spark ⚡ (Daily 5-question mixed challenge seeded by date)
"""

import copy
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

from models import Question, QuizSession
from storage import StorageManager


# Standardized category names
CATEGORIES = [
    "Technology",
    "Academics",
    "General Knowledge",
    "Competitive Exams",
    "Sports",
    "Entertainment"
]

DIFFICULTIES = ["easy", "medium", "hard"]

# Category alias mapping for flexible inputs
CATEGORY_ALIASES: Dict[str, str] = {
    "technology": "Technology",
    "tech": "Technology",
    "programming": "Technology",
    "coding": "Technology",
    "academics": "Academics",
    "science": "Academics",
    "general knowledge": "General Knowledge",
    "general": "General Knowledge",
    "gk": "General Knowledge",
    "trivia": "General Knowledge",
    "competitive exams": "Competitive Exams",
    "competitive": "Competitive Exams",
    "exams": "Competitive Exams",
    "math": "Competitive Exams",
    "aptitude": "Competitive Exams",
    "sports": "Sports",
    "sport": "Sports",
    "athletics": "Sports",
    "entertainment": "Entertainment",
    "movies": "Entertainment",
    "pop culture": "Entertainment",
    "cinema": "Entertainment",
    "daily spark": "Daily Spark ⚡",
    "daily spark ⚡": "Daily Spark ⚡",
    "daily": "Daily Spark ⚡",
}


class QuizEngine:
    """
    Coordinates question filtering, randomization, game mode configuration,
    and quiz session generation.
    """

    def __init__(self, storage_manager: Optional[StorageManager] = None) -> None:
        self.storage = storage_manager or StorageManager()
        self.questions: List[Question] = []
        self.reload_questions()

    def reload_questions(self) -> int:
        """Load or reload questions from storage."""
        self.questions = self.storage.load_questions()
        return len(self.questions)

    def normalize_category(self, category: str) -> str:
        """
        Map a category name or alias to its official canonical display name.
        """
        clean = str(category).strip().lower()
        if clean in CATEGORY_ALIASES:
            return CATEGORY_ALIASES[clean]

        for cat in CATEGORIES:
            if cat.lower() == clean:
                return cat

        if "daily" in clean:
            return "Daily Spark ⚡"

        return "Technology"

    def normalize_difficulty(self, difficulty: str) -> str:
        """
        Normalize difficulty string to 'easy', 'medium', 'hard', or 'mixed'.
        """
        clean = str(difficulty).strip().lower()
        if clean in DIFFICULTIES or clean == "mixed":
            return clean
        return "easy"

    def get_questions_pool(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Question]:
        """
        Filter questions matching the given category and difficulty.
        """
        norm_cat = self.normalize_category(category) if category else None
        norm_diff = self.normalize_difficulty(difficulty) if difficulty and difficulty != "mixed" else None

        filtered = []
        for q in self.questions:
            if norm_cat and norm_cat != "Daily Spark ⚡":
                if q.category.lower() != norm_cat.lower():
                    continue
            if norm_diff:
                if q.difficulty.lower() != norm_diff.lower():
                    continue
            filtered.append(q)

        return filtered

    def create_session(
        self,
        category: str = "Technology",
        difficulty: str = "easy",
        question_count: int = 5,
        shuffle_options: bool = True,
        mode: str = "learning",
        time_limit: Optional[int] = None
    ) -> QuizSession:
        """
        Build a randomized, self-contained QuizSession.

        Args:
            category (str): Selected category.
            difficulty (str): 'easy', 'medium', 'hard', or 'mixed'.
            question_count (int): Number of questions to include (e.g. 5 or 10).
            shuffle_options (bool): Whether to randomly shuffle option order.
            mode (str): 'learning' or 'exam'.
            time_limit (Optional[int]): Optional time limit in seconds for Exam Mode.

        Returns:
            QuizSession: Configured active quiz session.
        """
        norm_cat = self.normalize_category(category)
        norm_diff = self.normalize_difficulty(difficulty)

        # Handle Daily Spark separately if selected
        if norm_cat == "Daily Spark ⚡":
            return self.create_daily_spark_session(mode=mode)

        # 1. Fetch matching pool
        pool = self.get_questions_pool(norm_cat, norm_diff)

        # 2. Fallbacks if pool is small
        if not pool:
            pool = self.get_questions_pool(norm_cat, None)
        if not pool:
            pool = list(self.questions)

        # 3. Randomly sample requested question count
        sample_size = min(max(1, question_count), len(pool))
        chosen_raw = random.sample(pool, sample_size)

        # 4. Deep copy questions so option shuffling does not mutate original bank
        session_questions: List[Question] = []
        for q in chosen_raw:
            q_copy = copy.deepcopy(q)
            if shuffle_options and len(q_copy.options) > 1:
                correct_text = q_copy.get_correct_answer()
                random.shuffle(q_copy.options)
                q_copy.correct_index = q_copy.options.index(correct_text)
            session_questions.append(q_copy)

        return QuizSession(
            category=norm_cat,
            difficulty=norm_diff,
            questions=session_questions,
            mode=mode,
            time_limit=time_limit
        )

    def create_daily_spark_session(
        self,
        seed_date_str: Optional[str] = None,
        mode: str = "learning"
    ) -> QuizSession:
        """
        Generate a 5-question mixed challenge seeded deterministically by date.
        Picks questions across 5 distinct categories so every user gets the same
        daily challenge for a given calendar day!
        """
        date_str = seed_date_str or datetime.now().strftime("%Y-%m-%d")
        # Use date string to seed random generator for deterministic daily selection
        rng = random.Random(date_str)

        shuffled_categories = list(CATEGORIES)
        rng.shuffle(shuffled_categories)
        selected_categories = shuffled_categories[:5]

        chosen_questions: List[Question] = []
        for cat in selected_categories:
            pool = [q for q in self.questions if q.category.lower() == cat.lower()]
            if pool:
                picked = rng.choice(pool)
                q_copy = copy.deepcopy(picked)
                if len(q_copy.options) > 1:
                    correct_text = q_copy.get_correct_answer()
                    rng.shuffle(q_copy.options)
                    q_copy.correct_index = q_copy.options.index(correct_text)
                chosen_questions.append(q_copy)

        # Fallback if less than 5 questions
        if len(chosen_questions) < 5 and self.questions:
            remaining = [q for q in self.questions if q.id not in [c.id for c in chosen_questions]]
            if remaining:
                extra = rng.sample(remaining, min(5 - len(chosen_questions), len(remaining)))
                chosen_questions.extend([copy.deepcopy(x) for x in extra])

        return QuizSession(
            category=f"Daily Spark ⚡ ({date_str})",
            difficulty="mixed",
            questions=chosen_questions,
            mode=mode,
            time_limit=100 if mode == "exam" else None
        )

    @classmethod
    def get_categories(cls) -> List[str]:
        """Return list of canonical categories."""
        return list(CATEGORIES)

    @classmethod
    def get_difficulties(cls) -> List[str]:
        """Return list of canonical difficulties."""
        return list(DIFFICULTIES)

    def get_stats(self) -> Dict[str, Any]:
        """Return counts of questions per category and difficulty."""
        stats: Dict[str, Dict[str, int]] = {cat: {d: 0 for d in DIFFICULTIES} for cat in CATEGORIES}
        for q in self.questions:
            c = self.normalize_category(q.category)
            d = self.normalize_difficulty(q.difficulty)
            if c in stats and d in stats[c]:
                stats[c][d] += 1
        return {
            "total_questions": len(self.questions),
            "breakdown": stats
        }
