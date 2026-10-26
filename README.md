# QuizUp ✦ — Python Edition
> **"Master something new, one question at a time."**

An Object-Oriented desktop quiz gaming application built with Python and Tkinter, featuring full design and functional parity with the modern soft-candy web edition of **[QuizUp](https://github.com/dharmarayank946/quizup-quiz-game)**. Developed for **Week 4 of the Python Development Internship**.

---

## 🌟 Overview & Feature Parity Highlights

QuizUp Python Edition delivers a complete graphical desktop gaming experience:

- **Complete User Journey & Global Navigation**:
  `Dashboard` ➔ `Practice & Setup` ➔ `Active Quiz` ➔ `Results & Review` ➔ `Leaderboard` ➔ `Profile & Rewards`.
- **Soft Pastel Candy Design System**:
  Harmonious palette featuring soft lavender (`#F7F4FF`), pure white cards (`#FFFFFF`), royal candy purple (`#9A83E8`), pastel pink (`#F5A5C8`), mint green (`#92D9D0`), and warm amber (`#FFDFA0`).
- **Dual Game Modes**:
  - **📖 Learning Mode**: Instant feedback on option selection, option locking, green/rose visual cues, and detailed conceptual explanations.
  - **⏱️ Exam Mode**: Strict countdown timer, free multi-directional navigation (`Previous`, `Next`, and `Question Jump Bar`), provisional answer selection/editing, unanswered questions audit, and comprehensive post-exam review.
- **⚡ Daily Spark Challenge**:
  One-click daily 5-question challenge drawn across 5 distinct categories, deterministically seeded by calendar date (`YYYY-MM-DD`) with bonus daily XP and coin rewards.
- **🏆 Dedicated Leaderboard & Local Hall of Fame**:
  - Podium presentation for Top 3 performances (🥇 1st, 🥈 2nd, 🥉 3rd) with trophies and player details.
  - Interactive multi-criteria sorting: by **Score**, **Accuracy %**, or **Most Recent**.
  - Honest local player tracking with complete transparency.
- **👤 Player Profile & Rewards**:
  - Customizable local display name.
  - Selectable avatar roster (🦊 Fox, 🦉 Owl, 🚀 Rocket, 🧠 Brain, ⚡ Spark, 👑 Crown, 🐼 Panda, 🐯 Tiger).
  - Dynamic level progression system (Levels 1–5+: Trivia Novice, Quiz Explorer, Brainiac, Trivia Master, Grandmaster) with visual XP progress bar.
  - Coin earnings and tracking.
  - Milestone Achievements & Badges showcase (First Spark, Sharpshooter, Daily Explorer, Exam Ace, Trivia Scholar, Century Club, Category Specialist).
- **Interactive Results & Filterable Answer Review**:
  Score breakdown (correct, incorrect, unanswered, accuracy %, time elapsed, XP and coins earned), with an interactive **All** vs. **Mistakes Only** review filter.
- **6 Full Categories (180 Questions)**:
  Technology, Academics, General Knowledge, Competitive Exams, Sports, and Entertainment across Easy, Medium, and Hard difficulty tiers.
- **Resilient JSON Persistence**:
  Atomic writes via temporary swap files, automatic corruption recovery (`.corrupted_bak`), and embedded emergency fallback questions.

---

## 🎨 Design System & Color Tokens

| Token | Hex Code | Visual Application |
|---|---|---|
| **Page Canvas** | `#F7F4FF` | Main background (soft lavender) |
| **Card Surface** | `#FFFFFF` | Crisp elevated container cards |
| **Primary Purple** | `#9A83E8` | Primary action buttons, active tabs, header branding |
| **Purple Hover** | `#8870DC` | Button hover and pressed states |
| **Secondary Lavender** | `#E9DFFF` | Inactive buttons, subtle frames, tag pills |
| **Pastel Pink** | `#F5A5C8` | Daily Spark highlights, badges, sparkles |
| **Mint Green (Success)**| `#92D9D0` | Correct answers, success banners, high accuracy |
| **Mint Green Tint** | `#E6F9F6` | Correct answer background container |
| **Soft Rose (Alert)** | `#F87171` | Incorrect answer borders, reset buttons |
| **Rose Tint** | `#FEE2E2` | Incorrect answer background container |
| **Butter Yellow** | `#FFDFA0` | High score trophies, coins, achievement stars |
| **Text Main** | `#302B40` | High-contrast readable dark slate |
| **Text Muted** | `#6F687D` | Secondary labels, descriptions, and metadata |
| **Subtle Border** | `#E7E1F0` | Dividers and card outlines |

---

## 📂 Project Architecture

```
QuizUp Python Edition/
├── data/
│   ├── questions.json       # 180 questions across 6 categories & 3 difficulty tiers
│   └── progress.json        # Saved player history, best scores, level/XP, coins, and badges
├── tests/
│   ├── __init__.py          # Test package marker
│   └── test_quiz.py         # 19 automated unit tests
├── models.py                # OOP Classes: Question, QuizSession, PlayerProgress, Achievements
├── quiz_engine.py           # Question loading, alias normalization, shuffling, Daily Spark
├── storage.py               # Resilient JSON loading/saving & corruption recovery
├── gui.py                   # Modern Tkinter desktop graphical interface
├── main.py                  # Application entry point (GUI / CLI / Tests)
├── requirements.txt         # Standard library specification
├── .gitignore               # Excludes bytecode, temp files, and caches
└── README.md                # Comprehensive documentation
```

---

## 🧩 Object-Oriented Design (OOP)

The application adheres strictly to OOP best practices:

### 1. `Question` Class (`models.py`)
- Encapsulates question text, category, difficulty, 4 multiple-choice options, correct option index, and conceptual explanation.
- Provides answer validation (`is_correct()`), correct answer string lookup, and dictionary serialization (`to_dict()` / `from_dict()`).

### 2. `QuizSession` Class (`models.py`)
- Manages an active quiz attempt with support for **Learning Mode** and **Exam Mode**.
- Tracks progression, active index, provisional vs confirmed answers, countdown timers, and duration.
- Supports multi-directional navigation (`next_question()`, `previous_question()`, `go_to_question()`).
- Calculates non-duplicating scores, unanswered question counts, and reward bonuses in `calculate_results()`.

### 3. `PlayerProgress` Class (`models.py`)
- Encapsulates player identity (`player_name`, `avatar`), total XP, coin balance, and lifetime statistics.
- Implements dynamic Level calculations (`level`, `level_title`, `level_progress`) based on earned XP.
- Evaluates achievement criteria upon quiz completion and awards unlocked milestone badges.
- Provides `get_leaderboard_records(sort_by)` with sorting by score, accuracy percentage, or date.

### 4. `QuizEngine` Class (`quiz_engine.py`)
- Coordinates category filtering, difficulty selection, and alias mapping.
- Implements `create_daily_spark_session(seed_date_str)` using deterministic date-based seeding.
- Uses `random.sample` to pick questions without modifying the master question bank.
- Dynamically shuffles option order while keeping the correct answer index synchronized.

### 5. `StorageManager` Class (`storage.py`)
- Manages JSON persistence for `questions.json` and `progress.json`.
- Implements atomic writes (`os.replace` via temporary `.tmp` file) preventing corrupt half-written files.
- Automatically backs up damaged files (`.corrupted_bak`) and initializes safe defaults.
- Embeds emergency fallback questions so the application never fails to launch.

---

## 📚 Question Bank Matrix (180 Questions)

Verified in `data/questions.json`:

| Category | Easy | Medium | Hard | Total Questions |
|---|:---:|:---:|:---:|:---:|
| 💻 **Technology** | 10 | 10 | 10 | **30** |
| 🔬 **Academics** | 10 | 10 | 10 | **30** |
| 🌍 **General Knowledge** | 10 | 10 | 10 | **30** |
| 📐 **Competitive Exams** | 10 | 10 | 10 | **30** |
| ⚽ **Sports** | 10 | 10 | 10 | **30** |
| 🎬 **Entertainment** | 10 | 10 | 10 | **30** |
| **Total** | **60** | **60** | **60** | **180** |

---

## 🚀 How to Run

### 1. Requirements
The application uses Python's built-in standard library (`tkinter`, `json`, `os`, `random`, `datetime`, `unittest`). No external `pip` packages are required.

- **Python Version**: Python 3.8+ (Python 3.13 tested).
- **Tkinter**: Standard GUI library included with official Python distributions.

### 2. Launch the Desktop GUI
Run from the `QuizUp Python Edition` folder:
```bash
python main.py
```
*(Or `python gui.py`)*

### 3. Run the Automated Unit Tests
Execute the 19 automated unit tests:
```bash
python main.py --test
```
*(Or `python -m unittest tests/test_quiz.py`)*

### 4. Run Interactive Console / CLI Mode (Optional)
```bash
python main.py --cli
```

---

## 🧪 Quality Assurance & Test Verification

All 19 unit tests pass with 100% success rate:

```
test_daily_spark_deterministic_selection ......... ok
test_exam_mode_navigation_and_scoring ............ ok
test_progress_recording .......................... ok
test_achievement_evaluation ...................... ok
test_leaderboard_sorting .......................... ok
test_profile_customization_and_serialization ..... ok
test_xp_and_level_progression .................... ok
test_correct_answer_evaluation ................... ok
test_invalid_construction ........................ ok
test_serialization ............................... ok
test_category_normalization ...................... ok
test_engine_has_questions ......................... ok
test_filtering_and_sampling ...................... ok
test_option_shuffling_preserves_correct_answer ... ok
test_answering_and_progression ................... ok
test_initial_state ............................... ok
test_corrupted_json_recovery ..................... ok
test_missing_files_recovery ...................... ok
test_save_and_load_progress ...................... ok
----------------------------------------------------------------------
Ran 19 tests in 0.077s

OK
```

---

## 🔒 Project Isolation Guarantee

This project is strictly self-contained within `D:\Projects\Python Internship\QuizUp Python Edition`.
- **Week 1 (Basic Calculator)**: Preserved and unmodified in `Basic Calculator/`.
- **Week 2 (Student Management System)**: Preserved and unmodified in `Student Management System/`.
- **Week 3 (WeatherWise App)**: Preserved and unmodified in `Weather App/`.
- **Original Web QuizUp Project**: Unmodified and preserved. No remote pushes or publishes are performed until explicitly requested.
