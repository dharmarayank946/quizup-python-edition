"""
QuizUp Python Edition - Automated Test Suite
============================================
Tests question models, quiz session state, scoring accuracy,
question filtering, randomization, and resilient JSON storage.
"""

import json
import os
import shutil
import tempfile
import unittest

from models import Question, QuizSession, PlayerProgress
from quiz_engine import QuizEngine
from storage import StorageManager


class TestQuestionModel(unittest.TestCase):
    """Test Question encapsulation, answer validation, and serialization."""

    def setUp(self):
        self.q = Question(
            id="test_01",
            category="Technology",
            difficulty="easy",
            question_text="What is Python?",
            options=["A snake", "A programming language", "A car", "A planet"],
            correct_index=1,
            explanation="Python is a high-level programming language."
        )

    def test_correct_answer_evaluation(self):
        self.assertTrue(self.q.is_correct(1))
        self.assertFalse(self.q.is_correct(0))
        self.assertFalse(self.q.is_correct(2))
        self.assertFalse(self.q.is_correct(3))
        self.assertEqual(self.q.get_correct_answer(), "A programming language")

    def test_serialization(self):
        d = self.q.to_dict()
        self.assertEqual(d["id"], "test_01")
        self.assertEqual(d["correct_index"], 1)

        restored = Question.from_dict(d)
        self.assertEqual(restored.id, self.q.id)
        self.assertEqual(restored.question_text, self.q.question_text)
        self.assertEqual(restored.correct_index, 1)
        self.assertTrue(restored.is_correct(1))

    def test_invalid_construction(self):
        # Must have at least 2 options
        with self.assertRaises(ValueError):
            Question("bad_1", "Tech", "easy", "Q?", ["OnlyOne"], 0)

        # Correct index out of bounds
        with self.assertRaises(ValueError):
            Question("bad_2", "Tech", "easy", "Q?", ["A", "B"], 5)


class TestQuizSessionScoring(unittest.TestCase):
    """Test quiz scoring, question navigation, and results compilation."""

    def setUp(self):
        self.questions = [
            Question("q1", "Technology", "easy", "Q1?", ["A", "B", "C", "D"], 0, "Exp 1"),
            Question("q2", "Technology", "easy", "Q2?", ["A", "B", "C", "D"], 1, "Exp 2"),
            Question("q3", "Technology", "easy", "Q3?", ["A", "B", "C", "D"], 2, "Exp 3"),
            Question("q4", "Technology", "easy", "Q4?", ["A", "B", "C", "D"], 3, "Exp 4"),
        ]
        self.session = QuizSession("Technology", "easy", self.questions)

    def test_initial_state(self):
        self.assertEqual(self.session.total_questions, 4)
        self.assertEqual(self.session.score, 0)
        self.assertFalse(self.session.is_finished())
        self.assertEqual(self.session.get_current_question().id, "q1")

    def test_answering_and_progression(self):
        # Question 1: Answer correct (0)
        res1 = self.session.answer_current(0)
        self.assertTrue(res1)
        self.assertEqual(self.session.score, 1)

        # Advance to Q2
        q2 = self.session.next_question()
        self.assertEqual(q2.id, "q2")

        # Question 2: Answer incorrect (3 instead of 1)
        res2 = self.session.answer_current(3)
        self.assertFalse(res2)
        self.assertEqual(self.session.score, 1)

        # Advance to Q3
        self.session.next_question()
        # Question 3: Answer correct (2)
        res3 = self.session.answer_current(2)
        self.assertTrue(res3)
        self.assertEqual(self.session.score, 2)

        # Advance to Q4
        self.session.next_question()
        # Question 4: Answer correct (3)
        res4 = self.session.answer_current(3)
        self.assertTrue(res4)
        self.assertEqual(self.session.score, 3)

        # Finish quiz
        self.session.next_question()
        self.assertTrue(self.session.is_finished())
        self.assertIsNone(self.session.get_current_question())

        # Check calculated results
        results = self.session.calculate_results()
        self.assertEqual(results["score"], 3)
        self.assertEqual(results["total"], 4)
        self.assertEqual(results["incorrect"], 1)
        self.assertEqual(results["percentage"], 75.0)
        self.assertEqual(len(results["review"]), 4)


class TestPlayerProgress(unittest.TestCase):
    """Test cumulative stats, best score tracking, and history management."""

    def test_progress_recording(self):
        progress = PlayerProgress()
        self.assertEqual(progress.quizzes_played, 0)
        self.assertEqual(progress.overall_accuracy, 0.0)

        # Record attempt 1
        results1 = {
            "category": "Technology",
            "difficulty": "easy",
            "score": 4,
            "total": 5,
            "percentage": 80.0,
            "timestamp": "2026-10-26 12:00:00"
        }
        progress.record_session(results1)
        self.assertEqual(progress.quizzes_played, 1)
        self.assertEqual(progress.total_correct, 4)
        self.assertEqual(progress.total_questions, 5)
        self.assertEqual(progress.overall_accuracy, 80.0)
        self.assertEqual(progress.get_category_best("Technology"), 4)

        # Record attempt 2 in same category with higher score
        results2 = {
            "category": "Technology",
            "difficulty": "medium",
            "score": 5,
            "total": 5,
            "percentage": 100.0,
            "timestamp": "2026-10-26 12:10:00"
        }
        progress.record_session(results2)
        self.assertEqual(progress.quizzes_played, 2)
        self.assertEqual(progress.total_correct, 9)
        self.assertEqual(progress.total_questions, 10)
        self.assertEqual(progress.overall_accuracy, 90.0)
        self.assertEqual(progress.get_category_best("Technology"), 5)

        # Serialization round-trip
        data = progress.to_dict()
        restored = PlayerProgress.from_dict(data)
        self.assertEqual(restored.quizzes_played, 2)
        self.assertEqual(restored.total_correct, 9)
        self.assertEqual(restored.best_scores["Technology"], 5)


class TestQuizEngine(unittest.TestCase):
    """Test question filtering, randomization, and option shuffling."""

    def setUp(self):
        self.engine = QuizEngine()

    def test_engine_has_questions(self):
        self.assertGreaterEqual(len(self.engine.questions), 180)

    def test_category_normalization(self):
        self.assertEqual(self.engine.normalize_category("programming"), "Technology")
        self.assertEqual(self.engine.normalize_category("science"), "Academics")
        self.assertEqual(self.engine.normalize_category("gk"), "General Knowledge")
        self.assertEqual(self.engine.normalize_category("math"), "Competitive Exams")
        self.assertEqual(self.engine.normalize_category("sports"), "Sports")
        self.assertEqual(self.engine.normalize_category("movies"), "Entertainment")

    def test_filtering_and_sampling(self):
        # Sprint of 5 questions in Academics Medium
        session = self.engine.create_session("Academics", "medium", question_count=5)
        self.assertEqual(session.category, "Academics")
        self.assertEqual(session.difficulty, "medium")
        self.assertEqual(len(session.questions), 5)
        for q in session.questions:
            self.assertEqual(q.category, "Academics")
            self.assertEqual(q.difficulty, "medium")

    def test_option_shuffling_preserves_correct_answer(self):
        # Verify that option shuffling never breaks the correct answer text
        for _ in range(10):
            session = self.engine.create_session("Technology", "easy", question_count=5, shuffle_options=True)
            for q in session.questions:
                correct_text = q.get_correct_answer()
                self.assertEqual(q.options[q.correct_index], correct_text)
                self.assertTrue(q.is_correct(q.correct_index))


class TestStorageManager(unittest.TestCase):
    """Test resilient loading, saving, corruption recovery, and atomic writes."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.q_path = os.path.join(self.test_dir, "test_questions.json")
        self.p_path = os.path.join(self.test_dir, "test_progress.json")
        self.storage = StorageManager(self.q_path, self.p_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_missing_files_recovery(self):
        # Loading from non-existent questions file should create and load fallback questions
        questions = self.storage.load_questions()
        self.assertGreater(len(questions), 0)
        self.assertTrue(os.path.exists(self.q_path))

        # Loading from non-existent progress file should create fresh progress
        progress = self.storage.load_progress()
        self.assertEqual(progress.quizzes_played, 0)
        self.assertTrue(os.path.exists(self.p_path))

    def test_corrupted_json_recovery(self):
        # Write corrupted invalid JSON to progress file
        with open(self.p_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json text <<>>")

        # Loading should not crash, should create backup and return clean progress
        progress = self.storage.load_progress()
        self.assertIsInstance(progress, PlayerProgress)
        self.assertEqual(progress.quizzes_played, 0)
        self.assertTrue(os.path.exists(self.p_path + ".corrupted_bak"))

    def test_save_and_load_progress(self):
        progress = PlayerProgress(quizzes_played=3, total_correct=12, total_questions=15)
        saved = self.storage.save_progress(progress)
        self.assertTrue(saved)

        loaded = self.storage.load_progress()
        self.assertEqual(loaded.quizzes_played, 3)
        self.assertEqual(loaded.total_correct, 12)
        self.assertEqual(loaded.total_questions, 15)
        self.assertEqual(loaded.overall_accuracy, 80.0)


class TestExamModeAndDailySpark(unittest.TestCase):
    """Test Exam Mode free navigation, countdown limits, and Daily Spark mixed challenges."""

    def setUp(self):
        self.questions = [
            Question("ex1", "Technology", "easy", "Q1?", ["A", "B", "C", "D"], 0, "Exp 1"),
            Question("ex2", "Technology", "easy", "Q2?", ["A", "B", "C", "D"], 1, "Exp 2"),
            Question("ex3", "Technology", "easy", "Q3?", ["A", "B", "C", "D"], 2, "Exp 3"),
        ]

    def test_exam_mode_navigation_and_scoring(self):
        session = QuizSession("Technology", "easy", self.questions, mode="exam", time_limit=60)
        self.assertTrue(session.is_exam_mode)
        self.assertEqual(session.remaining_seconds, 60)

        # Free jump to question 2 (index 1)
        session.go_to_question(1)
        self.assertEqual(session.current_index, 1)

        # Answer question 2
        session.answer_current(1)
        self.assertEqual(session.answered_count, 1)
        self.assertEqual(session.unanswered_count, 2)

        # Change answer on question 2 (provisional change in Exam mode)
        session.answer_current(2)
        self.assertEqual(session.score, 0)
        session.answer_current(1)  # change back to correct
        self.assertEqual(session.score, 1)

        # Jump to question 3 (index 2)
        session.go_to_question(2)
        session.answer_current(2)  # correct

        # Question 1 (index 0) left unanswered
        results = session.calculate_results()
        self.assertEqual(results["mode"], "exam")
        self.assertEqual(results["score"], 2)
        self.assertEqual(results["total"], 3)
        self.assertEqual(results["unanswered"], 1)
        self.assertEqual(results["incorrect"], 0)
        self.assertGreater(results["xp_earned"], 0)
        self.assertGreater(results["coins_earned"], 0)

    def test_daily_spark_deterministic_selection(self):
        engine = QuizEngine()
        # Seeded by the same date string should produce the exact same 5 questions
        session1 = engine.create_daily_spark_session(seed_date_str="2026-10-26")
        session2 = engine.create_daily_spark_session(seed_date_str="2026-10-26")

        self.assertEqual(len(session1.questions), 5)
        self.assertEqual(len(session2.questions), 5)

        ids1 = [q.id for q in session1.questions]
        ids2 = [q.id for q in session2.questions]
        self.assertEqual(ids1, ids2)

        # Categories should be drawn across distinct categories
        cats = [q.category for q in session1.questions]
        self.assertEqual(len(set(cats)), 5)


class TestPlayerProgressionAndLeaderboard(unittest.TestCase):
    """Test XP thresholds, level titles, achievements, rewards, and leaderboard sorting."""

    def test_xp_and_level_progression(self):
        p = PlayerProgress()
        self.assertEqual(p.level, 1)
        self.assertEqual(p.level_title, "Trivia Novice")

        # Add XP to reach Level 2 (200 XP threshold)
        p.xp = 250
        self.assertEqual(p.level, 2)
        self.assertEqual(p.level_title, "Quiz Explorer")

        # Level 3 (500 XP threshold)
        p.xp = 600
        self.assertEqual(p.level, 3)
        self.assertEqual(p.level_title, "Brainiac")

        # Level progress calculation
        curr, span, pct = p.level_progress
        self.assertEqual(curr, 100)  # 600 - 500
        self.assertEqual(span, 500)  # 1000 - 500
        self.assertEqual(pct, 20.0)

    def test_achievement_evaluation(self):
        p = PlayerProgress()
        self.assertEqual(len(p.achievements), 0)

        # Complete first quiz with 100% accuracy
        results = {
            "category": "Technology",
            "difficulty": "easy",
            "mode": "learning",
            "score": 5,
            "total": 5,
            "percentage": 100.0,
            "xp_earned": 150,
            "coins_earned": 75,
            "timestamp": "2026-10-26 14:00:00"
        }
        unlocked = p.record_session(results)
        unlocked_ids = [a["id"] for a in unlocked]

        # Both 'first_quiz' and 'perfect_score' should trigger!
        self.assertIn("first_quiz", unlocked_ids)
        self.assertIn("perfect_score", unlocked_ids)
        self.assertTrue(p.is_achievement_unlocked("first_quiz"))
        self.assertTrue(p.is_achievement_unlocked("perfect_score"))

    def test_leaderboard_sorting(self):
        p = PlayerProgress(player_name="Champion", avatar="👑")
        # Add two attempts
        p.record_session({
            "category": "Academics",
            "difficulty": "easy",
            "mode": "learning",
            "score": 4,
            "total": 5,
            "percentage": 80.0,
            "timestamp": "2026-10-26 10:00:00"
        })
        p.record_session({
            "category": "Sports",
            "difficulty": "hard",
            "mode": "exam",
            "score": 5,
            "total": 5,
            "percentage": 100.0,
            "timestamp": "2026-10-26 11:00:00"
        })

        by_score = p.get_leaderboard_records(sort_by="score")
        self.assertEqual(by_score[0]["score"], 5)

        by_recent = p.get_leaderboard_records(sort_by="recent")
        self.assertEqual(by_recent[0]["category"], "Sports")

    def test_profile_customization_and_serialization(self):
        p = PlayerProgress(player_name="TriviaWhiz", avatar="🚀", coins=120)
        data = p.to_dict()
        self.assertEqual(data["player_name"], "TriviaWhiz")
        self.assertEqual(data["avatar"], "🚀")
        self.assertEqual(data["coins"], 120)

        restored = PlayerProgress.from_dict(data)
        self.assertEqual(restored.player_name, "TriviaWhiz")
        self.assertEqual(restored.avatar, "🚀")
        self.assertEqual(restored.coins, 120)


if __name__ == "__main__":
    unittest.main()

