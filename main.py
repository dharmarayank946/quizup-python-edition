"""
QuizUp Python Edition - Main Entry Point
========================================
Week 4 Python Internship Project

Launches the Tkinter graphical desktop application by default.
Supports command-line flags:
  --gui   : Launch the modern pastel Tkinter desktop application (default).
  --test  : Execute the automated unit test suite.
  --cli   : Run in interactive terminal mode.
"""

import sys
import os
import unittest

# Reconfigure stdout for UTF-8 compatibility on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from models import Question, QuizSession, PlayerProgress
from storage import StorageManager
from quiz_engine import QuizEngine


def run_tests() -> bool:
    """Run automated unit tests and return True if all passed."""
    print("=" * 60)
    print("QuizUp Python Edition -- Running Automated Unit Tests")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(os.path.dirname(__file__), "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_cli_quiz() -> None:
    """Run an interactive console quiz session using the same core OOP engine."""
    print("=" * 60)
    print("QuizUp Python Edition -- Terminal Mode")
    print("=" * 60)

    storage = StorageManager()
    engine = QuizEngine(storage)
    progress = storage.load_progress()

    print("\nAvailable Categories:")
    categories = engine.get_categories()
    for idx, cat in enumerate(categories, 1):
        print(f"  {idx}. {cat}")

    cat_choice = input(f"\nSelect category [1-{len(categories)}] (default 1): ").strip()
    try:
        cat_idx = int(cat_choice) - 1
        selected_cat = categories[cat_idx] if 0 <= cat_idx < len(categories) else "Technology"
    except ValueError:
        selected_cat = "Technology"

    diff_choice = input("Select difficulty [easy, medium, hard] (default easy): ").strip().lower()
    if diff_choice not in ["easy", "medium", "hard"]:
        diff_choice = "easy"

    print(f"\nStarting {selected_cat} ({diff_choice}) quiz...\n")
    session = engine.create_session(selected_cat, diff_choice, question_count=5)

    while not session.is_finished():
        q = session.get_current_question()
        if not q:
            break

        print(f"\n--- Question {session.current_index + 1} of {session.total_questions} ---")
        print(q.question_text)
        for i, opt in enumerate(q.options):
            print(f"  [{chr(65 + i)}] {opt}")

        user_input = input("Your answer (A, B, C, D): ").strip().upper()
        if user_input in ["A", "B", "C", "D"]:
            opt_idx = ord(user_input) - ord("A")
            is_right = session.answer_current(opt_idx)
            if is_right:
                print("[+] Correct!")
            else:
                print(f"[-] Incorrect. The correct answer was: [{chr(65 + q.correct_index)}] {q.get_correct_answer()}")
            print(f"[*] Explanation: {q.explanation}")
        else:
            print("Invalid input, marking as skipped.")
            session.answer_current(-1)

        session.next_question()

    results = session.calculate_results()
    progress.record_session(results)
    storage.save_progress(progress)

    print("\n" + "=" * 60)
    print(f"[+] Final Score: {results['score']} / {results['total']} ({results['percentage']}%)")
    print(f"[+] Duration: {results['duration_seconds']}s")
    print("=" * 60)


def run_gui() -> None:
    """Launch the Tkinter desktop GUI."""
    print("=" * 60)
    print("QuizUp Python Edition -- Launching Desktop Game GUI...")
    print("(Window will center and pop up directly in front)")
    print("=" * 60)
    try:
        import tkinter as tk
        from gui import QuizUpGUI

        root = tk.Tk()
        app = QuizUpGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Notice: Failed to launch Tkinter GUI: {e}")
        print("Falling back to CLI mode...")
        run_cli_quiz()


def main() -> None:
    """Entry point dispatcher."""
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()
        if arg in ["--test", "-t", "test"]:
            success = run_tests()
            sys.exit(0 if success else 1)
        elif arg in ["--cli", "-c", "cli"]:
            run_cli_quiz()
            sys.exit(0)

    # Default: launch GUI
    run_gui()


if __name__ == "__main__":
    main()
