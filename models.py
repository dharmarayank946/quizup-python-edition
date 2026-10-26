"""
QuizUp Python Edition - Data Models (Enhanced Feature Parity Edition)
=====================================================================
Defines Object-Oriented Programming (OOP) classes:
- Question: Encapsulates individual quiz questions, options, and explanations.
- QuizSession: Manages active quiz sessions (Learning Mode and Exam Mode),
               navigation, time tracking, and result compilation.
- Achievement: Represents unlockable player badges and milestone rewards.
- PlayerProgress: Manages player profile (name, avatar), level, XP, coins,
                 unlocked achievements, category best scores, and attempt history.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


# Predefined Avatar Roster
AVAILABLE_AVATARS = [
    {"icon": "🦊", "name": "Curious Fox"},
    {"icon": "🦉", "name": "Wise Owl"},
    {"icon": "🚀", "name": "Cosmic Rocket"},
    {"icon": "🧠", "name": "Mastermind"},
    {"icon": "⚡", "name": "Electric Spark"},
    {"icon": "👑", "name": "Trivia King"},
    {"icon": "🐼", "name": "Zen Panda"},
    {"icon": "🐯", "name": "Bold Tiger"}
]

# Predefined Achievements / Badges
PREDEFINED_ACHIEVEMENTS = [
    {
        "id": "first_quiz",
        "title": "First Spark",
        "icon": "⚡",
        "description": "Complete your very first quiz session in any category.",
        "reward_xp": 50,
        "reward_coins": 25
    },
    {
        "id": "perfect_score",
        "title": "Sharpshooter",
        "icon": "🎯",
        "description": "Achieve a flawless 100% accuracy score on any quiz.",
        "reward_xp": 100,
        "reward_coins": 50
    },
    {
        "id": "daily_spark",
        "title": "Daily Explorer",
        "icon": "📅",
        "description": "Successfully complete a Daily Spark ⚡ mixed challenge.",
        "reward_xp": 75,
        "reward_coins": 35
    },
    {
        "id": "exam_ace",
        "title": "Exam Ace",
        "icon": "⏱️",
        "description": "Complete an Exam Mode timed quiz with at least 80% accuracy.",
        "reward_xp": 100,
        "reward_coins": 50
    },
    {
        "id": "scholar",
        "title": "Trivia Scholar",
        "icon": "📚",
        "description": "Complete 5 or more quiz sessions across any category.",
        "reward_xp": 150,
        "reward_coins": 75
    },
    {
        "id": "century_club",
        "title": "Century Club",
        "icon": "💯",
        "description": "Answer 50 or more total questions throughout your quiz career.",
        "reward_xp": 200,
        "reward_coins": 100
    },
    {
        "id": "category_specialist",
        "title": "Category Specialist",
        "icon": "👑",
        "description": "Score 10 out of 10 in a Full Challenge quiz.",
        "reward_xp": 250,
        "reward_coins": 150
    }
]


class Question:
    """
    Represents an individual multiple-choice question.

    Attributes:
        id (str): Unique question identifier.
        category (str): Subject category (e.g., Technology, Academics).
        difficulty (str): Difficulty level ('easy', 'medium', 'hard').
        question_text (str): The question prompt displayed to the user.
        options (List[str]): List of 4 multiple-choice options.
        correct_index (int): 0-indexed position of the correct option.
        explanation (str): Conceptual rationale explaining the correct answer.
    """

    def __init__(
        self,
        id: str,
        category: str,
        difficulty: str,
        question_text: str,
        options: List[str],
        correct_index: int,
        explanation: str = ""
    ) -> None:
        self.id = str(id).strip()
        self.category = str(category).strip()
        self.difficulty = str(difficulty).strip().lower()
        self.question_text = str(question_text).strip()
        self.options = [str(opt).strip() for opt in options]
        self.correct_index = int(correct_index)
        self.explanation = str(explanation).strip()

        # Validation
        if len(self.options) < 2:
            raise ValueError(f"Question '{self.id}' must have at least 2 options.")
        if not (0 <= self.correct_index < len(self.options)):
            raise ValueError(
                f"Question '{self.id}': correct_index {self.correct_index} "
                f"out of range for {len(self.options)} options."
            )

    def is_correct(self, chosen_index: Optional[int]) -> bool:
        """Return True if chosen_index matches correct_index."""
        if chosen_index is None or chosen_index < 0:
            return False
        return chosen_index == self.correct_index

    def get_correct_answer(self) -> str:
        """Return the text of the correct option."""
        return self.options[self.correct_index]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the Question instance to a dictionary."""
        return {
            "id": self.id,
            "category": self.category,
            "difficulty": self.difficulty,
            "question": self.question_text,
            "options": self.options,
            "correct_index": self.correct_index,
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Question":
        """Factory method to construct a Question instance from a dictionary."""
        q_text = data.get("question") or data.get("question_text", "")
        c_index = data.get("correct_index")
        if c_index is None:
            c_index = data.get("correctIndex", 0)

        return cls(
            id=data.get("id", "q_unknown"),
            category=data.get("category", "General Knowledge"),
            difficulty=data.get("difficulty", "easy"),
            question_text=q_text,
            options=data.get("options", []),
            correct_index=int(c_index),
            explanation=data.get("explanation", ""),
        )

    def __repr__(self) -> str:
        return f"<Question id={self.id} cat={self.category} diff={self.difficulty}>"


class QuizSession:
    """
    Encapsulates a single active or completed quiz attempt.

    Supports:
    - Mode: 'learning' (instant feedback, answer locking) vs 'exam' (timed countdown, free navigation, provisional answers).
    - Sequential and free-index question navigation.
    - Non-duplicating score calculations and detailed review output.
    """

    def __init__(
        self,
        category: str,
        difficulty: str,
        questions: List[Question],
        mode: str = "learning",
        time_limit: Optional[int] = None
    ) -> None:
        self.category = category
        self.difficulty = difficulty.lower()
        self.questions = questions
        self.mode = mode.lower()  # 'learning' or 'exam'
        self.current_index = 0
        self.user_answers: Dict[int, Optional[int]] = {}  # question_idx -> chosen_option_idx
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

        # Exam mode timer support (in seconds)
        # Default: 20 seconds per question for Exam Mode if not specified
        if self.mode == "exam" and time_limit is None:
            self.time_limit = len(questions) * 20
        else:
            self.time_limit = time_limit

        self.remaining_seconds = self.time_limit if self.time_limit is not None else 0

    @property
    def is_exam_mode(self) -> bool:
        return self.mode == "exam"

    @property
    def total_questions(self) -> int:
        return len(self.questions)

    @property
    def score(self) -> int:
        """Calculate total number of correct answers."""
        correct_count = 0
        for q_idx, chosen_opt in self.user_answers.items():
            if 0 <= q_idx < len(self.questions) and chosen_opt is not None:
                if self.questions[q_idx].is_correct(chosen_opt):
                    correct_count += 1
        return correct_count

    @property
    def answered_count(self) -> int:
        """Count how many questions have a selected answer."""
        return sum(1 for opt in self.user_answers.values() if opt is not None and opt >= 0)

    @property
    def unanswered_count(self) -> int:
        """Count how many questions remain unanswered."""
        return self.total_questions - self.answered_count

    def get_current_question(self) -> Optional[Question]:
        """Return the current Question or None if quiz is finished."""
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def get_user_answer_for_current(self) -> Optional[int]:
        """Return chosen index for current question or None."""
        return self.user_answers.get(self.current_index)

    def answer_current(self, option_index: int) -> bool:
        """
        Record the user's answer for the current question.
        Returns True if the answer was correct, False otherwise.
        """
        if self.is_finished():
            return False

        q = self.get_current_question()
        if not q:
            return False

        # Store answer
        self.user_answers[self.current_index] = option_index
        return q.is_correct(option_index)

    def go_to_question(self, index: int) -> Optional[Question]:
        """Jump directly to a specific question index (useful in Exam Mode)."""
        if 0 <= index < len(self.questions):
            self.current_index = index
            return self.questions[self.current_index]
        return None

    def next_question(self) -> Optional[Question]:
        """Advance to the next question index."""
        self.current_index += 1
        if self.is_finished() and self.end_time is None:
            self.end_time = datetime.now()
        return self.get_current_question()

    def previous_question(self) -> Optional[Question]:
        """Move back to the previous question index (useful in Exam Mode)."""
        if self.current_index > 0:
            self.current_index -= 1
        return self.get_current_question()

    def is_finished(self) -> bool:
        """Check whether all questions have been answered or reached."""
        return self.current_index >= len(self.questions)

    def finish_session(self) -> None:
        """Explicitly conclude session (e.g., when exam timer expires or user submits)."""
        if self.end_time is None:
            self.end_time = datetime.now()
        self.current_index = len(self.questions)

    def calculate_results(self) -> Dict[str, Any]:
        """Compute comprehensive performance metrics for the session."""
        total = len(self.questions)
        correct = self.score
        unanswered = 0
        for idx in range(total):
            ans = self.user_answers.get(idx)
            if ans is None or ans < 0:
                unanswered += 1
        incorrect = total - correct - unanswered
        percentage = round((correct / total * 100), 1) if total > 0 else 0.0

        if self.end_time is None:
            self.end_time = datetime.now()

        duration_sec = int((self.end_time - self.start_time).total_seconds())

        # Base rewards calculation
        base_xp = correct * 20 + 25  # +20 XP per correct + 25 XP completion bonus
        base_coins = correct * 10 + 10  # +10 coins per correct + 10 completion
        if percentage == 100.0:
            base_xp += 100
            base_coins += 50
        elif percentage >= 80.0:
            base_xp += 50
            base_coins += 25

        if self.mode == "exam":
            base_xp += 30
            base_coins += 20

        # Build detailed review of each question
        review = []
        for idx, q in enumerate(self.questions):
            user_opt = self.user_answers.get(idx)
            is_right = q.is_correct(user_opt)
            is_unanswered = (user_opt is None or user_opt < 0)

            chosen_text = "Unanswered"
            if not is_unanswered and user_opt is not None and 0 <= user_opt < len(q.options):
                chosen_text = q.options[user_opt]

            review.append({
                "question_index": idx + 1,
                "question_id": q.id,
                "question_text": q.question_text,
                "options": q.options,
                "chosen_index": user_opt,
                "chosen_text": chosen_text,
                "correct_index": q.correct_index,
                "correct_text": q.get_correct_answer(),
                "is_correct": is_right,
                "is_unanswered": is_unanswered,
                "explanation": q.explanation,
            })

        return {
            "category": self.category,
            "difficulty": self.difficulty,
            "mode": self.mode,
            "score": correct,
            "total": total,
            "incorrect": incorrect,
            "unanswered": unanswered,
            "percentage": percentage,
            "duration_seconds": duration_sec,
            "xp_earned": base_xp,
            "coins_earned": base_coins,
            "timestamp": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "review": review,
        }


class PlayerProgress:
    """
    Manages cumulative player statistics, profile settings, level, XP, coins,
    unlocked achievements, category high scores, and attempt history.
    """

    def __init__(
        self,
        player_name: str = "Player",
        avatar: str = "🦊",
        xp: int = 0,
        coins: int = 50,
        quizzes_played: int = 0,
        total_correct: int = 0,
        total_questions: int = 0,
        best_scores: Optional[Dict[str, int]] = None,
        achievements: Optional[List[str]] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        self.player_name = str(player_name).strip() or "Player"
        self.avatar = str(avatar).strip() or "🦊"
        self.xp = max(0, int(xp))
        self.coins = max(0, int(coins))
        self.quizzes_played = max(0, int(quizzes_played))
        self.total_correct = max(0, int(total_correct))
        self.total_questions = max(0, int(total_questions))
        self.best_scores: Dict[str, int] = best_scores if isinstance(best_scores, dict) else {}
        self.achievements: List[str] = achievements if isinstance(achievements, list) else []
        self.history: List[Dict[str, Any]] = history if isinstance(history, list) else []

    # Level & Progression System
    @property
    def level(self) -> int:
        """
        Calculate current level based on total XP.
        Level 1: 0 - 200 XP
        Level 2: 201 - 500 XP
        Level 3: 501 - 1000 XP
        Level 4: 1001 - 2000 XP
        Level 5: 2001 - 3500 XP
        Level 6+: +1500 XP per level
        """
        if self.xp < 200:
            return 1
        elif self.xp < 500:
            return 2
        elif self.xp < 1000:
            return 3
        elif self.xp < 2000:
            return 4
        elif self.xp < 3500:
            return 5
        else:
            return 5 + (self.xp - 3500) // 1500 + 1

    @property
    def level_title(self) -> str:
        """Return title associated with current player level."""
        lvl = self.level
        titles = {
            1: "Trivia Novice",
            2: "Quiz Explorer",
            3: "Brainiac",
            4: "Trivia Master",
            5: "Grandmaster"
        }
        return titles.get(lvl, "Legendary Champion")

    @property
    def level_progress(self) -> Tuple[int, int, float]:
        """
        Returns (current_level_xp, xp_needed_for_next, progress_pct 0.0-100.0)
        """
        lvl = self.level
        thresholds = [0, 200, 500, 1000, 2000, 3500]
        if lvl < len(thresholds):
            prev_thresh = thresholds[lvl - 1]
            next_thresh = thresholds[lvl]
        else:
            prev_thresh = 3500 + (lvl - 5) * 1500
            next_thresh = prev_thresh + 1500

        span = next_thresh - prev_thresh
        curr = max(0, self.xp - prev_thresh)
        pct = round(min(1.0, curr / span) * 100, 1) if span > 0 else 100.0
        return curr, span, pct

    @property
    def overall_accuracy(self) -> float:
        """Compute lifetime overall accuracy percentage."""
        if self.total_questions == 0:
            return 0.0
        return round((self.total_correct / self.total_questions) * 100, 1)

    def record_session(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Update cumulative stats, best scores, award XP/coins, evaluate achievements,
        and append to history. Returns any newly unlocked achievements.
        """
        score = results.get("score", 0)
        total = results.get("total", 0)
        category = results.get("category", "General")
        xp_earned = results.get("xp_earned", score * 20)
        coins_earned = results.get("coins_earned", score * 10)

        self.quizzes_played += 1
        self.total_correct += score
        self.total_questions += total
        self.xp += xp_earned
        self.coins += coins_earned

        # Update category best score
        current_best = self.best_scores.get(category, 0)
        if score > current_best:
            self.best_scores[category] = score

        # Check achievements
        newly_unlocked = self._evaluate_achievements(results)

        # Record attempt history item (limit history to last 50 items)
        history_entry = {
            "player_name": self.player_name,
            "avatar": self.avatar,
            "timestamp": results.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "category": category,
            "difficulty": results.get("difficulty", "easy"),
            "mode": results.get("mode", "learning"),
            "score": score,
            "total": total,
            "percentage": results.get("percentage", 0.0),
            "duration_seconds": results.get("duration_seconds", 0),
            "xp_earned": xp_earned,
            "coins_earned": coins_earned
        }
        self.history.insert(0, history_entry)
        if len(self.history) > 50:
            self.history = self.history[:50]

        return newly_unlocked

    def _evaluate_achievements(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate criteria for all locked achievements and unlock qualifying ones."""
        newly_unlocked = []
        score = results.get("score", 0)
        total = results.get("total", 0)
        pct = results.get("percentage", 0.0)
        category = results.get("category", "")
        mode = results.get("mode", "learning")

        for ach in PREDEFINED_ACHIEVEMENTS:
            aid = ach["id"]
            if aid in self.achievements:
                continue

            unlocked = False
            if aid == "first_quiz" and self.quizzes_played >= 1:
                unlocked = True
            elif aid == "perfect_score" and pct == 100.0 and total >= 5:
                unlocked = True
            elif aid == "daily_spark" and "Daily Spark" in category:
                unlocked = True
            elif aid == "exam_ace" and mode == "exam" and pct >= 80.0:
                unlocked = True
            elif aid == "scholar" and self.quizzes_played >= 5:
                unlocked = True
            elif aid == "century_club" and self.total_questions >= 50:
                unlocked = True
            elif aid == "category_specialist" and score == 10 and total == 10:
                unlocked = True

            if unlocked:
                self.achievements.append(aid)
                self.xp += ach.get("reward_xp", 0)
                self.coins += ach.get("reward_coins", 0)
                newly_unlocked.append(ach)

        return newly_unlocked

    def get_category_best(self, category: str) -> int:
        """Retrieve best score achieved in a given category."""
        return self.best_scores.get(category, 0)

    def is_achievement_unlocked(self, achievement_id: str) -> bool:
        """Check if an achievement ID is already earned."""
        return achievement_id in self.achievements

    def get_leaderboard_records(self, sort_by: str = "score") -> List[Dict[str, Any]]:
        """
        Return personal high score records formatted for the Leaderboard view.
        Supports sorting by 'score', 'percentage', or 'recent'.
        """
        records = list(self.history)
        if sort_by == "percentage":
            records.sort(key=lambda r: (r.get("percentage", 0), r.get("score", 0)), reverse=True)
        elif sort_by == "recent":
            records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        else:  # 'score' default
            records.sort(key=lambda r: (r.get("score", 0), r.get("percentage", 0)), reverse=True)
        return records

    def clear_history(self) -> None:
        """Reset player attempt history and lifetime statistics (preserves player name & avatar)."""
        self.quizzes_played = 0
        self.total_correct = 0
        self.total_questions = 0
        self.xp = 0
        self.coins = 50
        self.best_scores.clear()
        self.achievements.clear()
        self.history.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize PlayerProgress to a JSON-compatible dictionary."""
        return {
            "player_name": self.player_name,
            "avatar": self.avatar,
            "xp": self.xp,
            "coins": self.coins,
            "quizzes_played": self.quizzes_played,
            "total_correct": self.total_correct,
            "total_questions": self.total_questions,
            "overall_accuracy": self.overall_accuracy,
            "level": self.level,
            "level_title": self.level_title,
            "best_scores": self.best_scores,
            "achievements": self.achievements,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerProgress":
        """Instantiate PlayerProgress safely from parsed JSON data with backward compatibility."""
        if not isinstance(data, dict):
            return cls()
        return cls(
            player_name=data.get("player_name", "Player"),
            avatar=data.get("avatar", "🦊"),
            xp=data.get("xp", 0),
            coins=data.get("coins", 50),
            quizzes_played=data.get("quizzes_played", 0),
            total_correct=data.get("total_correct", 0),
            total_questions=data.get("total_questions", 0),
            best_scores=data.get("best_scores", {}),
            achievements=data.get("achievements", []),
            history=data.get("history", [])
        )
