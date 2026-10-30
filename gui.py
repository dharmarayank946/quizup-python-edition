"""
QuizUp Python Edition - Professional Desktop GUI (Tkinter)
==========================================================
Delivers full feature parity with the modern soft-candy web edition:
- Global Navigation Header (Dashboard, Practice Setup, Leaderboard, Profile & Rewards).
- Dashboard with personalized time-of-day greeting, Level & XP progress bar,
  Daily Spark ⚡ mixed challenge, mode showcase, and featured categories.
- Dual Game Modes:
  * Learning Mode: Instant feedback, option locking, and educational explanations.
  * Exam Mode: Timed countdown assessment, free navigation, provisional answers,
    and post-exam review.
- Local Leaderboard & Hall of Fame with podium presentation and multi-attribute sorting.
- Profile & Rewards with editable display name, selectable avatar roster,
  coin balance, and achievement badges showcase.
- Comprehensive Results & Review with 'All' vs 'Mistakes Only' filters.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Optional, List, Dict, Any

from models import (
    Question,
    QuizSession,
    PlayerProgress,
    AVAILABLE_AVATARS,
    PREDEFINED_ACHIEVEMENTS
)
from quiz_engine import QuizEngine
from storage import StorageManager


# =============================================================================
# Color Constants — Soft Candy UI Palette
# =============================================================================
BG_COLOR = "#F7F4FF"               # Soft lavender canvas background
CARD_BG = "#FFFFFF"                # Pure white elevated card surfaces
PRIMARY_PURPLE = "#9A83E8"         # Royal candy purple (primary accent)
PRIMARY_PURPLE_HOVER = "#8870DC"   # Deeper purple on hover/active
SECONDARY_LAVENDER = "#E9DFFF"     # Light lavender tag/button background
PASTEL_PINK = "#F5A5C8"            # Accent pink for highlights and badges
MINT_GREEN = "#92D9D0"             # Mint green for correct answers & success
MINT_GREEN_DARK = "#168274"        # High-contrast text on mint
MINT_GREEN_BG = "#E6F9F6"          # Soft mint container background
SOFT_ROSE = "#F87171"              # Soft rose red for incorrect answers
ROSE_DARK = "#B91C1C"              # High-contrast text on rose
ROSE_BG = "#FEE2E2"                # Soft rose container background
BUTTER_YELLOW = "#FFDFA0"          # Warm amber for trophies, coins, & stars
TEXT_MAIN = "#302B40"              # High-contrast dark text
TEXT_MUTED = "#6F687D"             # Secondary / muted labels
BORDER_SUBTLE = "#E7E1F0"          # Card outlines and dividers

CATEGORY_ICONS = {
    "Technology": "💻",
    "Academics": "🔬",
    "General Knowledge": "🌍",
    "Competitive Exams": "📐",
    "Sports": "⚽",
    "Entertainment": "🎬",
    "Daily Spark ⚡": "⚡"
}

DIFFICULTY_LABELS = {
    "easy": "🌱 Easy",
    "medium": "⚡ Medium",
    "hard": "🔥 Hard",
    "mixed": "🎲 Mixed"
}


class QuizUpGUI:
    """
    Main Tkinter graphical interface for QuizUp Python Edition.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("QuizUp ✦ Python Edition")
        self.root.geometry("1000x780")
        self.root.minsize(860, 680)
        self.root.configure(bg=BG_COLOR)

        # Center and elevate window in front of VS Code / terminal on startup
        self._center_and_elevate_window(980, 720)

        # Engine and Storage instances
        self.storage = StorageManager()
        self.engine = QuizEngine(self.storage)
        self.progress: PlayerProgress = self.storage.load_progress()

        # Active Session & Setup State
        self.current_session: Optional[QuizSession] = None
        self.selected_category: str = "Technology"
        self.selected_difficulty: str = "easy"
        self.selected_mode: str = "learning"  # 'learning' or 'exam'
        self.selected_question_count: int = 5
        self.has_answered_current: bool = False

        # Exam mode countdown timer handle
        self.exam_timer_id: Optional[str] = None

        # Answer Review filter state ('all' or 'mistakes')
        self.review_filter: str = "all"
        self.latest_unlocked_achievements: List[Dict[str, Any]] = []

        # Build persistent navigation header
        self._build_top_header()

        # Content container where views are dynamically rendered
        self.content_area = tk.Frame(self.root, bg=BG_COLOR)
        self.content_area.pack(fill=tk.BOTH, expand=True)

        # Start on Dashboard
        self.show_dashboard_screen()

    def _center_and_elevate_window(self, width: int, height: int) -> None:
        """Center window on screen and elevate smoothly in front of all applications."""
        try:
            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            w = min(width, sw - 40)
            h = min(height, sh - 80)
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            self.root.geometry(f"{w}x{h}+{x}+{y}")
            self.root.minsize(860, 600)
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(800, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
        except Exception:
            pass

    def _cancel_timer(self) -> None:
        """Cancel active countdown timer if running."""
        if self.exam_timer_id is not None:
            try:
                self.root.after_cancel(self.exam_timer_id)
            except Exception:
                pass
            self.exam_timer_id = None

    def _clear_content(self, cancel_timer: bool = True) -> None:
        """Clear dynamic content view and conditionally stop active timers."""
        if cancel_timer:
            self._cancel_timer()
        for widget in self.content_area.winfo_children():
            widget.destroy()

    # =========================================================================
    # GLOBAL PERSISTENT HEADER & NAVIGATION BAR
    # =========================================================================

    def _build_top_header(self) -> None:
        """Construct the persistent app navigation header."""
        self.header_frame = tk.Frame(self.root, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        self.header_frame.pack(fill=tk.X, side=tk.TOP, ipady=6, ipadx=15)

        # Left: App Logo / Title
        brand_frame = tk.Frame(self.header_frame, bg=CARD_BG)
        brand_frame.pack(side=tk.LEFT, padx=(10, 20))

        logo_lbl = tk.Label(brand_frame, text="QuizUp ✦", font=("Segoe UI", 16, "bold"), bg=CARD_BG, fg=PRIMARY_PURPLE)
        logo_lbl.pack(side=tk.LEFT)

        sub_lbl = tk.Label(brand_frame, text="Desktop Edition", font=("Segoe UI", 9, "bold"), bg=SECONDARY_LAVENDER, fg=PRIMARY_PURPLE, padx=6, pady=2)
        sub_lbl.pack(side=tk.LEFT, padx=(8, 0))

        # Center: Navigation Tabs
        nav_tabs = tk.Frame(self.header_frame, bg=CARD_BG)
        nav_tabs.pack(side=tk.LEFT, padx=10)

        self.nav_buttons: Dict[str, tk.Button] = {}
        tabs = [
            ("dashboard", "🏠 Dashboard", self.show_dashboard_screen),
            ("setup", "🎯 Practice & Setup", self.show_setup_screen),
            ("leaderboard", "🏆 Leaderboard", self.show_leaderboard_screen),
            ("profile", "👤 Profile & Rewards", self.show_profile_screen)
        ]

        for tab_id, label, cmd in tabs:
            btn = tk.Button(
                nav_tabs,
                text=label,
                font=("Segoe UI", 10),
                bg=CARD_BG,
                fg=TEXT_MAIN,
                activebackground=SECONDARY_LAVENDER,
                activeforeground=PRIMARY_PURPLE,
                bd=0,
                cursor="hand2",
                padx=12,
                pady=6,
                command=cmd
            )
            btn.pack(side=tk.LEFT, padx=3)
            self.nav_buttons[tab_id] = btn

        # Right: Quick Player Status Chip (Avatar, Name, Level, Coins)
        self.player_chip = tk.Frame(self.header_frame, bg=BG_COLOR, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        self.player_chip.pack(side=tk.RIGHT, padx=10, ipady=3, ipadx=10)

        self.chip_avatar_lbl = tk.Label(self.player_chip, text=self.progress.avatar, font=("Segoe UI", 14), bg=BG_COLOR)
        self.chip_avatar_lbl.pack(side=tk.LEFT, padx=(0, 6))

        self.chip_info_lbl = tk.Label(
            self.player_chip,
            text=f"{self.progress.player_name}  •  Lv.{self.progress.level}  •  {self.progress.coins} 🪙",
            font=("Segoe UI", 9, "bold"),
            bg=BG_COLOR,
            fg=TEXT_MAIN
        )
        self.chip_info_lbl.pack(side=tk.LEFT)

    def _update_header_chip(self) -> None:
        """Refresh player chip status in global header."""
        self.chip_avatar_lbl.configure(text=self.progress.avatar)
        self.chip_info_lbl.configure(
            text=f"{self.progress.player_name}  •  Lv.{self.progress.level}  •  {self.progress.coins} 🪙"
        )

    def _highlight_nav_tab(self, active_tab: str) -> None:
        """Visual highlight for active navigation tab."""
        self._update_header_chip()
        for tab_id, btn in self.nav_buttons.items():
            if tab_id == active_tab:
                btn.configure(bg=SECONDARY_LAVENDER, fg=PRIMARY_PURPLE, font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=CARD_BG, fg=TEXT_MAIN, font=("Segoe UI", 10, "normal"))

    # =========================================================================
    # 1. DASHBOARD SCREEN
    # =========================================================================

    def show_dashboard_screen(self) -> None:
        """Render the complete main player dashboard view."""
        self._clear_content()
        self._highlight_nav_tab("dashboard")
        self.progress = self.storage.load_progress()

        # Canvas for scrollable dashboard
        canvas = tk.Canvas(self.content_area, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_area, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_COLOR)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=970)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=15)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 1. Personalized Greeting & Level Card
        greeting_card = tk.Frame(scroll_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        greeting_card.pack(fill=tk.X, pady=(0, 15), ipady=12, ipadx=18)

        # Time of day greeting
        hour = datetime.now().hour
        greeting_word = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 17 else "Good Evening")

        top_row = tk.Frame(greeting_card, bg=CARD_BG)
        top_row.pack(fill=tk.X)

        greet_lbl = tk.Label(
            top_row,
            text=f"{greeting_word}, {self.progress.player_name}! {self.progress.avatar}",
            font=("Segoe UI", 18, "bold"),
            bg=CARD_BG,
            fg=TEXT_MAIN
        )
        greet_lbl.pack(side=tk.LEFT)

        level_pill = tk.Label(
            top_row,
            text=f"Level {self.progress.level} — {self.progress.level_title}",
            font=("Segoe UI", 10, "bold"),
            bg=SECONDARY_LAVENDER,
            fg=PRIMARY_PURPLE,
            padx=10,
            pady=4
        )
        level_pill.pack(side=tk.RIGHT)

        # XP Progress Bar
        curr_xp, span_xp, pct = self.progress.level_progress
        xp_frame = tk.Frame(greeting_card, bg=CARD_BG)
        xp_frame.pack(fill=tk.X, pady=(10, 0))

        xp_text = tk.Label(
            xp_frame,
            text=f"Experience: {self.progress.xp} Total XP  ({curr_xp} / {span_xp} XP to Level {self.progress.level + 1})",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_MUTED
        )
        xp_text.pack(anchor=tk.W, pady=(0, 4))

        # Progress bar widget
        prog_bar = ttk.Progressbar(xp_frame, orient=tk.HORIZONTAL, length=900, mode="determinate")
        prog_bar["value"] = pct
        prog_bar.pack(fill=tk.X)

        # 2. Daily Spark ⚡ Challenge Banner (Signature Feature)
        spark_card = tk.Frame(scroll_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=PASTEL_PINK, highlightthickness=2)
        spark_card.pack(fill=tk.X, pady=(0, 15), ipady=10, ipadx=18)

        spark_inner = tk.Frame(spark_card, bg=CARD_BG)
        spark_inner.pack(fill=tk.X)

        spark_left = tk.Frame(spark_inner, bg=CARD_BG)
        spark_left.pack(side=tk.LEFT)

        today_date = datetime.now().strftime("%B %d, %Y")
        spark_badge = tk.Label(
            spark_left,
            text="⚡ DAILY SPARK CHALLENGE",
            font=("Segoe UI", 9, "bold"),
            bg=PASTEL_PINK,
            fg="#FFFFFF",
            padx=8,
            pady=2
        )
        spark_badge.pack(anchor=tk.W)

        spark_title = tk.Label(
            spark_left,
            text="Today's 5-Question Mixed Sprint",
            font=("Segoe UI", 14, "bold"),
            bg=CARD_BG,
            fg=TEXT_MAIN
        )
        spark_title.pack(anchor=tk.W, pady=(2, 0))

        spark_sub = tk.Label(
            spark_left,
            text=f"5 questions across different categories for {today_date}. Earn +75 bonus XP!",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_MUTED
        )
        spark_sub.pack(anchor=tk.W)

        spark_btn = tk.Button(
            spark_inner,
            text="Play Daily Spark ⚡",
            font=("Segoe UI", 11, "bold"),
            bg=PRIMARY_PURPLE,
            fg="#FFFFFF",
            activebackground=PRIMARY_PURPLE_HOVER,
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8,
            command=self.start_daily_spark
        )
        spark_btn.pack(side=tk.RIGHT, padx=10)

        # 3. Game Mode Showcase Banners (Learning vs Exam)
        modes_row = tk.Frame(scroll_frame, bg=BG_COLOR)
        modes_row.pack(fill=tk.X, pady=(0, 15))

        # Learning Mode Showcase Card
        learn_card = tk.Frame(modes_row, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        learn_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), ipady=10, ipadx=15)

        learn_tag = tk.Label(learn_card, text="📖 LEARNING MODE", font=("Segoe UI", 9, "bold"), bg=MINT_GREEN_BG, fg=MINT_GREEN_DARK, padx=8, pady=2)
        learn_tag.pack(anchor=tk.W, padx=10, pady=(5, 3))

        learn_title = tk.Label(learn_card, text="Instant Feedback & Concept Mastery", font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        learn_title.pack(anchor=tk.W, padx=10)

        learn_desc = tk.Label(
            learn_card,
            text="Answer questions one by one with immediate correctness indicators, locked choices, and educational rationale.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_MUTED,
            wraplength=400,
            justify=tk.LEFT
        )
        learn_desc.pack(anchor=tk.W, padx=10, pady=(3, 8))

        learn_btn = tk.Button(
            learn_card,
            text="Launch Learning Quiz ➔",
            font=("Segoe UI", 9, "bold"),
            bg=SECONDARY_LAVENDER,
            fg=PRIMARY_PURPLE,
            activebackground=BORDER_SUBTLE,
            bd=0,
            cursor="hand2",
            padx=12,
            pady=5,
            command=lambda: self._quick_start_mode("learning")
        )
        learn_btn.pack(anchor=tk.W, padx=10)

        # Exam Mode Showcase Card
        exam_card = tk.Frame(modes_row, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        exam_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0), ipady=10, ipadx=15)

        exam_tag = tk.Label(exam_card, text="⏱️ EXAM MODE", font=("Segoe UI", 9, "bold"), bg=ROSE_BG, fg=ROSE_DARK, padx=8, pady=2)
        exam_tag.pack(anchor=tk.W, padx=10, pady=(5, 3))

        exam_title = tk.Label(exam_card, text="Timed Challenge & Free Navigation", font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        exam_title.pack(anchor=tk.W, padx=10)

        exam_desc = tk.Label(
            exam_card,
            text="Strict countdown timer, free multi-directional question navigation, provisional answers, and full post-exam review.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_MUTED,
            wraplength=400,
            justify=tk.LEFT
        )
        exam_desc.pack(anchor=tk.W, padx=10, pady=(3, 8))

        exam_btn = tk.Button(
            exam_card,
            text="Launch Exam Challenge ➔",
            font=("Segoe UI", 9, "bold"),
            bg=SECONDARY_LAVENDER,
            fg=PRIMARY_PURPLE,
            activebackground=BORDER_SUBTLE,
            bd=0,
            cursor="hand2",
            padx=12,
            pady=5,
            command=lambda: self._quick_start_mode("exam")
        )
        exam_btn.pack(anchor=tk.W, padx=10)

        # 4. Quick Stats Ribbon (4 Mini-Cards)
        stats_row = tk.Frame(scroll_frame, bg=BG_COLOR)
        stats_row.pack(fill=tk.X, pady=(0, 15))

        self._create_stat_mini_card(stats_row, "🎮 Quizzes Played", str(self.progress.quizzes_played), PASTEL_PINK)
        self._create_stat_mini_card(stats_row, "🎯 Accuracy", f"{self.progress.overall_accuracy}%", MINT_GREEN)
        best_val = max(self.progress.best_scores.values()) if self.progress.best_scores else 0
        self._create_stat_mini_card(stats_row, "🏆 Best Score", str(best_val), BUTTER_YELLOW)
        self._create_stat_mini_card(stats_row, "🪙 Coins", str(self.progress.coins), BUTTER_YELLOW)

        # 5. Featured Subject Categories Grid (6 Cards)
        cat_section = tk.Frame(scroll_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        cat_section.pack(fill=tk.X, pady=(0, 10), ipady=10, ipadx=15)

        cat_header_row = tk.Frame(cat_section, bg=CARD_BG)
        cat_header_row.pack(fill=tk.X, padx=15, pady=(5, 10))

        cat_lbl = tk.Label(cat_header_row, text="Featured Categories", font=("Segoe UI", 13, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        cat_lbl.pack(side=tk.LEFT)

        custom_btn = tk.Button(
            cat_header_row,
            text="Customize Settings in Quiz Setup ⚙️",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=PRIMARY_PURPLE,
            bd=0,
            cursor="hand2",
            command=self.show_setup_screen
        )
        custom_btn.pack(side=tk.RIGHT)

        cat_grid = tk.Frame(cat_section, bg=CARD_BG)
        cat_grid.pack(fill=tk.X, padx=15, pady=(0, 5))

        for idx, cat_name in enumerate(self.engine.get_categories()):
            row = idx // 3
            col = idx % 3
            icon = CATEGORY_ICONS.get(cat_name, "✦")
            best_cat = self.progress.get_category_best(cat_name)

            card_f = tk.Frame(cat_grid, bg=BG_COLOR, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
            card_f.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            cat_grid.grid_columnconfigure(col, weight=1)

            t_box = tk.Label(card_f, text=f"{icon}  {cat_name}", font=("Segoe UI", 10, "bold"), bg=BG_COLOR, fg=TEXT_MAIN)
            t_box.pack(anchor=tk.W, padx=10, pady=(8, 2))

            b_box = tk.Label(card_f, text=f"Best: {best_cat} pts", font=("Segoe UI", 8), bg=BG_COLOR, fg=TEXT_MUTED)
            b_box.pack(anchor=tk.W, padx=10, pady=(0, 8))

            play_b = tk.Button(
                card_f,
                text="Start Practice ➔",
                font=("Segoe UI", 9, "bold"),
                bg=PRIMARY_PURPLE,
                fg="#FFFFFF",
                bd=0,
                cursor="hand2",
                padx=10,
                pady=4,
                command=lambda c=cat_name: self._start_category_direct(c)
            )
            play_b.pack(anchor=tk.E, padx=10, pady=(0, 8))

    def _create_stat_mini_card(self, parent: tk.Widget, label: str, value: str, accent: str) -> None:
        """Create a summary stat box."""
        card = tk.Frame(parent, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, ipady=8, ipadx=10)

        stripe = tk.Frame(card, bg=accent, height=3)
        stripe.pack(fill=tk.X, side=tk.TOP)

        v_lbl = tk.Label(card, text=value, font=("Segoe UI", 15, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        v_lbl.pack(pady=(5, 1))

        l_lbl = tk.Label(card, text=label, font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_MUTED)
        l_lbl.pack()

    def _quick_start_mode(self, mode: str) -> None:
        """Configure mode and navigate to quiz setup."""
        self.selected_mode = mode
        self.show_setup_screen()

    def _start_category_direct(self, category: str) -> None:
        """Direct launch of a selected category with default 5 questions."""
        self.selected_category = category
        self.start_quiz()

    def start_daily_spark(self) -> None:
        """Directly initialize and launch today's Daily Spark challenge."""
        self.selected_category = "Daily Spark ⚡"
        self._cancel_timer()
        self.current_session = self.engine.create_daily_spark_session(mode=self.selected_mode)
        self.show_quiz_screen()

    # =========================================================================
    # 2. QUIZ SETUP SCREEN
    # =========================================================================

    def show_setup_screen(self) -> None:
        """Render comprehensive quiz configuration and setup screen."""
        self._clear_content()
        self._highlight_nav_tab("setup")

        setup_frame = tk.Frame(self.content_area, bg=BG_COLOR)
        setup_frame.pack(fill=tk.BOTH, expand=True, padx=35, pady=20)

        # Header Title
        title_card = tk.Frame(setup_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        title_card.pack(fill=tk.X, pady=(0, 15), ipady=8, ipadx=15)

        t_lbl = tk.Label(title_card, text="🎯 Quiz Setup & Customization", font=("Segoe UI", 16, "bold"), bg=CARD_BG, fg=PRIMARY_PURPLE)
        t_lbl.pack(anchor=tk.W, padx=10)
        s_lbl = tk.Label(title_card, text="Choose your subject, difficulty tier, game mode, and challenge length.", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_MUTED)
        s_lbl.pack(anchor=tk.W, padx=10)

        # 1. Category Selection Card
        cat_card = tk.Frame(setup_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        cat_card.pack(fill=tk.X, pady=(0, 12), ipady=8, ipadx=15)

        c_title = tk.Label(cat_card, text="1. Select Category", font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        c_title.pack(anchor=tk.W, padx=15, pady=(4, 8))

        grid_f = tk.Frame(cat_card, bg=CARD_BG)
        grid_f.pack(fill=tk.X, padx=15, pady=(0, 5))

        self.setup_cat_buttons = {}
        for idx, cat in enumerate(self.engine.get_categories()):
            r = idx // 3
            c = idx % 3
            icon = CATEGORY_ICONS.get(cat, "✦")
            is_sel = (cat == self.selected_category)

            btn = tk.Button(
                grid_f,
                text=f"{icon}  {cat}",
                font=("Segoe UI", 10, "bold" if is_sel else "normal"),
                bg=PRIMARY_PURPLE if is_sel else SECONDARY_LAVENDER,
                fg="#FFFFFF" if is_sel else TEXT_MAIN,
                activebackground=PRIMARY_PURPLE_HOVER,
                activeforeground="#FFFFFF",
                bd=0,
                cursor="hand2",
                padx=10,
                pady=7,
                command=lambda ct=cat: self._setup_select_cat(ct)
            )
            btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            grid_f.grid_columnconfigure(c, weight=1)
            self.setup_cat_buttons[cat] = btn

        # 2. Difficulty & Mode Row
        mid_row = tk.Frame(setup_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        mid_row.pack(fill=tk.X, pady=(0, 12), ipady=8, ipadx=15)

        mid_inner = tk.Frame(mid_row, bg=CARD_BG)
        mid_inner.pack(fill=tk.X, padx=15, pady=4)

        # Difficulty Selector
        diff_col = tk.Frame(mid_inner, bg=CARD_BG)
        diff_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        d_title = tk.Label(diff_col, text="2. Difficulty Level", font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        d_title.pack(anchor=tk.W, pady=(0, 6))

        diff_b_frame = tk.Frame(diff_col, bg=CARD_BG)
        diff_b_frame.pack(anchor=tk.W)

        self.setup_diff_buttons = {}
        for d_key in ["easy", "medium", "hard"]:
            lbl = DIFFICULTY_LABELS[d_key]
            is_sel = (d_key == self.selected_difficulty)
            btn = tk.Button(
                diff_b_frame,
                text=lbl,
                font=("Segoe UI", 10, "bold" if is_sel else "normal"),
                bg=PRIMARY_PURPLE if is_sel else SECONDARY_LAVENDER,
                fg="#FFFFFF" if is_sel else TEXT_MAIN,
                bd=0,
                cursor="hand2",
                padx=12,
                pady=6,
                command=lambda d=d_key: self._setup_select_diff(d)
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))
            self.setup_diff_buttons[d_key] = btn

        # Mode Selector
        mode_col = tk.Frame(mid_inner, bg=CARD_BG)
        mode_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        m_title = tk.Label(mode_col, text="3. Game Mode", font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        m_title.pack(anchor=tk.W, pady=(0, 6))

        mode_b_frame = tk.Frame(mode_col, bg=CARD_BG)
        mode_b_frame.pack(anchor=tk.W)

        self.setup_mode_buttons = {}
        for m_key, m_label in [("learning", "📖 Learning Mode"), ("exam", "⏱️ Exam Mode")]:
            is_sel = (m_key == self.selected_mode)
            btn = tk.Button(
                mode_b_frame,
                text=m_label,
                font=("Segoe UI", 10, "bold" if is_sel else "normal"),
                bg=PRIMARY_PURPLE if is_sel else SECONDARY_LAVENDER,
                fg="#FFFFFF" if is_sel else TEXT_MAIN,
                bd=0,
                cursor="hand2",
                padx=12,
                pady=6,
                command=lambda m=m_key: self._setup_select_mode(m)
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))
            self.setup_mode_buttons[m_key] = btn

        # 3. Question Count Card
        len_card = tk.Frame(setup_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        len_card.pack(fill=tk.X, pady=(0, 15), ipady=8, ipadx=15)

        len_title = tk.Label(len_card, text="4. Question Count", font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        len_title.pack(anchor=tk.W, padx=15, pady=(4, 6))

        len_b_frame = tk.Frame(len_card, bg=CARD_BG)
        len_b_frame.pack(anchor=tk.W, padx=15, pady=(0, 5))

        self.setup_count_buttons = {}
        for c_val, c_lbl in [(5, "⚡ 5 Questions (Quick Sprint)"), (10, "🏆 10 Questions (Full Challenge)")]:
            is_sel = (c_val == self.selected_question_count)
            btn = tk.Button(
                len_b_frame,
                text=c_lbl,
                font=("Segoe UI", 10, "bold" if is_sel else "normal"),
                bg=PRIMARY_PURPLE if is_sel else SECONDARY_LAVENDER,
                fg="#FFFFFF" if is_sel else TEXT_MAIN,
                bd=0,
                cursor="hand2",
                padx=14,
                pady=6,
                command=lambda c=c_val: self._setup_select_count(c)
            )
            btn.pack(side=tk.LEFT, padx=(0, 8))
            self.setup_count_buttons[c_val] = btn

        # Action Buttons
        action_f = tk.Frame(setup_frame, bg=BG_COLOR)
        action_f.pack(fill=tk.X, pady=5)

        start_btn = tk.Button(
            action_f,
            text="Start Quiz ✦",
            font=("Segoe UI", 13, "bold"),
            bg=PRIMARY_PURPLE,
            fg="#FFFFFF",
            activebackground=PRIMARY_PURPLE_HOVER,
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=28,
            pady=10,
            command=self.start_quiz
        )
        start_btn.pack(side=tk.LEFT, padx=(0, 12))

        cancel_btn = tk.Button(
            action_f,
            text="← Return to Dashboard",
            font=("Segoe UI", 10),
            bg=CARD_BG,
            fg=TEXT_MAIN,
            bd=0,
            highlightbackground=BORDER_SUBTLE,
            highlightthickness=1,
            cursor="hand2",
            padx=16,
            pady=10,
            command=self.show_dashboard_screen
        )
        cancel_btn.pack(side=tk.LEFT)

    def _setup_select_cat(self, cat: str) -> None:
        self.selected_category = cat
        for c, btn in self.setup_cat_buttons.items():
            is_sel = (c == cat)
            btn.configure(bg=PRIMARY_PURPLE if is_sel else SECONDARY_LAVENDER, fg="#FFFFFF" if is_sel else TEXT_MAIN, font=("Segoe UI", 10, "bold" if is_sel else "normal"))

    def _setup_select_diff(self, diff: str) -> None:
        self.selected_difficulty = diff
        for d, btn in self.setup_diff_buttons.items():
            is_sel = (d == diff)
            btn.configure(bg=PRIMARY_PURPLE if is_sel else SECONDARY_LAVENDER, fg="#FFFFFF" if is_sel else TEXT_MAIN, font=("Segoe UI", 10, "bold" if is_sel else "normal"))

    def _setup_select_mode(self, mode: str) -> None:
        self.selected_mode = mode
        for m, btn in self.setup_mode_buttons.items():
            is_sel = (m == mode)
            btn.configure(bg=PRIMARY_PURPLE if is_sel else SECONDARY_LAVENDER, fg="#FFFFFF" if is_sel else TEXT_MAIN, font=("Segoe UI", 10, "bold" if is_sel else "normal"))

    def _setup_select_count(self, count: int) -> None:
        self.selected_question_count = count
        for c, btn in self.setup_count_buttons.items():
            is_sel = (c == count)
            btn.configure(bg=PRIMARY_PURPLE if is_sel else SECONDARY_LAVENDER, fg="#FFFFFF" if is_sel else TEXT_MAIN, font=("Segoe UI", 10, "bold" if is_sel else "normal"))

    # =========================================================================
    # 3. ACTIVE QUIZ SCREEN (LEARNING & EXAM MODES)
    # =========================================================================

    def start_quiz(self) -> None:
        """Create session and launch active quiz view."""
        self._cancel_timer()
        self.current_session = self.engine.create_session(
            category=self.selected_category,
            difficulty=self.selected_difficulty,
            question_count=self.selected_question_count,
            shuffle_options=True,
            mode=self.selected_mode
        )
        self.show_quiz_screen()

    def show_quiz_screen(self) -> None:
        """Render active question with mode-specific layout."""
        self._clear_content(cancel_timer=False)
        self.has_answered_current = False

        if not self.current_session or self.current_session.is_finished():
            self.show_results_screen()
            return

        q = self.current_session.get_current_question()
        if not q:
            self.show_results_screen()
            return

        quiz_frame = tk.Frame(self.content_area, bg=BG_COLOR)
        quiz_frame.pack(fill=tk.BOTH, expand=True, padx=35, pady=20)

        # 1. Status Bar Header
        status_bar = tk.Frame(quiz_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        status_bar.pack(fill=tk.X, pady=(0, 12), ipady=8, ipadx=15)

        # Mode Tag
        is_exam = self.current_session.is_exam_mode
        mode_text = "⏱️ EXAM MODE" if is_exam else "📖 LEARNING MODE"
        mode_color = ROSE_DARK if is_exam else MINT_GREEN_DARK
        mode_bg = ROSE_BG if is_exam else MINT_GREEN_BG

        m_badge = tk.Label(status_bar, text=mode_text, font=("Segoe UI", 9, "bold"), bg=mode_bg, fg=mode_color, padx=8, pady=3)
        m_badge.pack(side=tk.LEFT, padx=(0, 10))

        # Category & Difficulty Tag
        cat_icon = CATEGORY_ICONS.get(self.current_session.category, "✦")
        cat_badge = tk.Label(status_bar, text=f"{cat_icon} {self.current_session.category}", font=("Segoe UI", 10, "bold"), bg=SECONDARY_LAVENDER, fg=PRIMARY_PURPLE, padx=8, pady=3)
        cat_badge.pack(side=tk.LEFT, padx=(0, 8))

        diff_badge = tk.Label(status_bar, text=self.current_session.difficulty.capitalize(), font=("Segoe UI", 9), bg=BG_COLOR, fg=TEXT_MUTED, padx=6, pady=3)
        diff_badge.pack(side=tk.LEFT)

        # Right Side: Exam Timer or Live Score
        if is_exam:
            mins = self.current_session.remaining_seconds // 60
            secs = self.current_session.remaining_seconds % 60
            self.timer_label = tk.Label(
                status_bar,
                text=f"⏳ {mins:02d}:{secs:02d}",
                font=("Segoe UI", 11, "bold"),
                bg=ROSE_BG,
                fg=ROSE_DARK,
                padx=10,
                pady=3
            )
            self.timer_label.pack(side=tk.RIGHT)
            # Start timer loop if not already running
            if self.exam_timer_id is None:
                self.exam_timer_id = self.root.after(1000, self._tick_exam_timer)
        else:
            score_lbl = tk.Label(
                status_bar,
                text=f"Score: {self.current_session.score}",
                font=("Segoe UI", 10, "bold"),
                bg=MINT_GREEN_BG,
                fg=MINT_GREEN_DARK,
                padx=10,
                pady=3
            )
            score_lbl.pack(side=tk.RIGHT)

        # Question Index Count
        count_lbl = tk.Label(
            status_bar,
            text=f"Question {self.current_session.current_index + 1} of {self.current_session.total_questions}",
            font=("Segoe UI", 11, "bold"),
            bg=CARD_BG,
            fg=TEXT_MAIN
        )
        count_lbl.pack(side=tk.RIGHT, padx=12)

        # 2. Question Card
        q_card = tk.Frame(quiz_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        q_card.pack(fill=tk.BOTH, expand=True, ipady=12, ipadx=18)

        # Question text
        q_text_lbl = tk.Label(
            q_card,
            text=q.question_text,
            font=("Segoe UI", 13, "bold"),
            bg=CARD_BG,
            fg=TEXT_MAIN,
            wraplength=800,
            justify=tk.LEFT
        )
        q_text_lbl.pack(anchor=tk.W, padx=20, pady=(15, 18))

        # Options Container
        opt_container = tk.Frame(q_card, bg=CARD_BG)
        opt_container.pack(fill=tk.X, padx=20, pady=(0, 5))

        self.quiz_option_buttons = []
        user_choice = self.current_session.get_user_answer_for_current()
        opt_letters = ["A", "B", "C", "D"]

        for opt_idx, opt_text in enumerate(q.options):
            letter = opt_letters[opt_idx] if opt_idx < len(opt_letters) else str(opt_idx + 1)
            btn_label = f"   {letter}.  {opt_text}"

            # Initial styling based on mode and prior answer
            is_chosen = (user_choice == opt_idx)
            btn_bg = SECONDARY_LAVENDER if (is_exam and is_chosen) else BG_COLOR
            btn_fg = PRIMARY_PURPLE if (is_exam and is_chosen) else TEXT_MAIN
            btn_font = ("Segoe UI", 11, "bold" if (is_exam and is_chosen) else "normal")

            btn = tk.Button(
                opt_container,
                text=btn_label,
                font=btn_font,
                bg=btn_bg,
                fg=btn_fg,
                activebackground=SECONDARY_LAVENDER,
                bd=0,
                highlightbackground=BORDER_SUBTLE,
                highlightthickness=1,
                anchor=tk.W,
                justify=tk.LEFT,
                cursor="hand2",
                padx=15,
                pady=9,
                command=lambda idx=opt_idx: self._handle_quiz_answer(idx)
            )
            btn.pack(fill=tk.X, pady=4)
            self.quiz_option_buttons.append(btn)

        # Learning Mode Explanation Drawer
        self.explanation_frame = tk.Frame(q_card, bg=BG_COLOR, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        self.explanation_label = tk.Label(
            self.explanation_frame,
            text="",
            font=("Segoe UI", 10),
            bg=BG_COLOR,
            fg=TEXT_MAIN,
            wraplength=780,
            justify=tk.LEFT
        )
        self.explanation_label.pack(anchor=tk.W, padx=12, pady=10)

        # 3. Bottom Navigation Bar
        nav_bottom = tk.Frame(q_card, bg=CARD_BG)
        nav_bottom.pack(fill=tk.X, padx=20, pady=(15, 10))

        if is_exam:
            # Exam Mode Multi-Directional Navigation
            prev_btn = tk.Button(
                nav_bottom,
                text="← Previous",
                font=("Segoe UI", 10),
                bg=SECONDARY_LAVENDER,
                fg=TEXT_MAIN,
                bd=0,
                cursor="hand2",
                state=tk.NORMAL if self.current_session.current_index > 0 else tk.DISABLED,
                command=self._exam_prev_question
            )
            prev_btn.pack(side=tk.LEFT)

            # Jump bar (pills 1..N)
            jump_f = tk.Frame(nav_bottom, bg=CARD_BG)
            jump_f.pack(side=tk.LEFT, padx=15)

            for j_idx in range(self.current_session.total_questions):
                ans = self.current_session.user_answers.get(j_idx)
                is_curr = (j_idx == self.current_session.current_index)
                is_done = (ans is not None and ans >= 0)

                j_bg = PRIMARY_PURPLE if is_curr else (MINT_GREEN_BG if is_done else BG_COLOR)
                j_fg = "#FFFFFF" if is_curr else (MINT_GREEN_DARK if is_done else TEXT_MUTED)

                j_btn = tk.Button(
                    jump_f,
                    text=str(j_idx + 1),
                    font=("Segoe UI", 8, "bold" if is_curr else "normal"),
                    bg=j_bg,
                    fg=j_fg,
                    bd=0,
                    width=2,
                    cursor="hand2",
                    command=lambda idx=j_idx: self._exam_jump_question(idx)
                )
                j_btn.pack(side=tk.LEFT, padx=2)

            # Submit Exam or Next Question
            is_last = (self.current_session.current_index + 1 >= self.current_session.total_questions)
            if is_last:
                submit_btn = tk.Button(
                    nav_bottom,
                    text="Submit Exam 🏆",
                    font=("Segoe UI", 10, "bold"),
                    bg=PRIMARY_PURPLE,
                    fg="#FFFFFF",
                    activebackground=PRIMARY_PURPLE_HOVER,
                    bd=0,
                    cursor="hand2",
                    padx=15,
                    pady=6,
                    command=self._confirm_exam_submission
                )
                submit_btn.pack(side=tk.RIGHT)
            else:
                next_btn = tk.Button(
                    nav_bottom,
                    text="Next ➔",
                    font=("Segoe UI", 10, "bold"),
                    bg=PRIMARY_PURPLE,
                    fg="#FFFFFF",
                    activebackground=PRIMARY_PURPLE_HOVER,
                    bd=0,
                    cursor="hand2",
                    padx=14,
                    pady=6,
                    command=self._exam_next_question
                )
                next_btn.pack(side=tk.RIGHT)
        else:
            # Learning Mode Sequential Navigation
            is_last = (self.current_session.current_index + 1 >= self.current_session.total_questions)
            next_text = "See Final Results 🏆" if is_last else "Next Question ➔"

            self.learn_next_btn = tk.Button(
                nav_bottom,
                text=next_text,
                font=("Segoe UI", 11, "bold"),
                bg=PRIMARY_PURPLE,
                fg="#FFFFFF",
                activebackground=PRIMARY_PURPLE_HOVER,
                bd=0,
                cursor="hand2",
                padx=18,
                pady=7,
                state=tk.DISABLED,  # Unlocks after option click
                command=self._learning_advance
            )
            self.learn_next_btn.pack(side=tk.RIGHT)

        # Exit to Dashboard
        exit_btn = tk.Button(
            nav_bottom,
            text="⌂ Exit to Dashboard",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_MUTED,
            bd=0,
            cursor="hand2",
            command=self._confirm_exit_quiz
        )
        exit_btn.pack(side=tk.LEFT if not is_exam else tk.LEFT, padx=(0, 10))

    def _tick_exam_timer(self) -> None:
        """Countdown timer for Exam Mode assessment."""
        if not self.current_session or not self.current_session.is_exam_mode or self.current_session.is_finished():
            self._cancel_timer()
            return

        if self.current_session.remaining_seconds > 0:
            self.current_session.remaining_seconds -= 1
            mins = self.current_session.remaining_seconds // 60
            secs = self.current_session.remaining_seconds % 60
            if hasattr(self, "timer_label") and self.timer_label.winfo_exists():
                self.timer_label.configure(text=f"⏳ {mins:02d}:{secs:02d}")
            self.exam_timer_id = self.root.after(1000, self._tick_exam_timer)
        else:
            # Time has expired!
            self._cancel_timer()
            messagebox.showinfo("Time's Up!", "Exam time limit reached! Submitting your responses now.")
            self._finish_and_show_results()

    def _handle_quiz_answer(self, chosen_index: int) -> None:
        """Process player's option click based on active mode."""
        if not self.current_session:
            return

        q = self.current_session.get_current_question()
        if not q:
            return

        if self.current_session.is_exam_mode:
            # Exam Mode: Record answer provisionally without leaks
            self.current_session.answer_current(chosen_index)
            # Update visual highlight on chosen option
            for idx, btn in enumerate(self.quiz_option_buttons):
                if idx == chosen_index:
                    btn.configure(bg=SECONDARY_LAVENDER, fg=PRIMARY_PURPLE, font=("Segoe UI", 11, "bold"))
                else:
                    btn.configure(bg=BG_COLOR, fg=TEXT_MAIN, font=("Segoe UI", 11, "normal"))
        else:
            # Learning Mode: Immediate feedback, lock buttons, reveal explanation
            if self.has_answered_current:
                return
            self.has_answered_current = True

            is_correct = self.current_session.answer_current(chosen_index)

            # Lock option buttons
            for btn in self.quiz_option_buttons:
                btn.configure(state=tk.DISABLED, cursor="arrow")

            # Style chosen button
            chosen_btn = self.quiz_option_buttons[chosen_index]
            if is_correct:
                chosen_btn.configure(bg=MINT_GREEN_BG, fg=MINT_GREEN_DARK, font=("Segoe UI", 11, "bold"), highlightbackground=MINT_GREEN, highlightthickness=2)
            else:
                chosen_btn.configure(bg=ROSE_BG, fg=ROSE_DARK, font=("Segoe UI", 11, "bold"), highlightbackground=SOFT_ROSE, highlightthickness=2)
                # Reveal correct answer in green
                correct_btn = self.quiz_option_buttons[q.correct_index]
                correct_btn.configure(bg=MINT_GREEN_BG, fg=MINT_GREEN_DARK, font=("Segoe UI", 11, "bold"), highlightbackground=MINT_GREEN, highlightthickness=2)

            # Reveal explanation
            status = "✓ Correct!" if is_correct else f"✗ Incorrect. The correct answer was: {q.get_correct_answer()}"
            self.explanation_label.configure(text=f"{status}\n\n💡 Explanation: {q.explanation}")
            self.explanation_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

            # Enable next button
            self.learn_next_btn.configure(state=tk.NORMAL)

    def _learning_advance(self) -> None:
        """Advance to next question in Learning Mode."""
        if not self.current_session:
            return
        self.current_session.next_question()
        if self.current_session.is_finished():
            self._finish_and_show_results()
        else:
            self.show_quiz_screen()

    def _exam_next_question(self) -> None:
        if self.current_session:
            self.current_session.next_question()
            self.show_quiz_screen()

    def _exam_prev_question(self) -> None:
        if self.current_session:
            self.current_session.previous_question()
            self.show_quiz_screen()

    def _exam_jump_question(self, index: int) -> None:
        if self.current_session:
            self.current_session.go_to_question(index)
            self.show_quiz_screen()

    def _confirm_exam_submission(self) -> None:
        """Intercept unanswered questions before final submission in Exam Mode."""
        if not self.current_session:
            return

        unanswered = self.current_session.unanswered_count
        if unanswered > 0:
            msg = f"You have {unanswered} unanswered question(s).\n\nDo you want to submit anyway or review your answers?"
            if not messagebox.askyesno("Confirm Exam Submission", msg):
                return

        self._finish_and_show_results()

    def _finish_and_show_results(self) -> None:
        """Conclude session, save progress, award XP/coins/achievements, and display results."""
        self._cancel_timer()
        if not self.current_session:
            self.show_dashboard_screen()
            return

        self.current_session.finish_session()
        results = self.current_session.calculate_results()

        # Update progress and check for newly unlocked achievements
        self.latest_unlocked_achievements = self.progress.record_session(results)
        self.storage.save_progress(self.progress)
        self._update_header_chip()

        self.show_results_screen()

    def _confirm_exit_quiz(self) -> None:
        """Prompt confirmation before discarding active quiz progress."""
        if messagebox.askyesno("Exit Quiz", "Are you sure you want to exit? Your progress in this quiz will not be saved."):
            self._cancel_timer()
            self.show_dashboard_screen()

    # =========================================================================
    # 4. RESULTS & ANSWER REVIEW SCREEN
    # =========================================================================

    def show_results_screen(self) -> None:
        """Display comprehensive results, celebration banner, rewards, and answer review."""
        self._clear_content()
        if not self.current_session:
            self.show_dashboard_screen()
            return

        results = self.current_session.calculate_results()
        score = results["score"]
        total = results["total"]
        pct = results["percentage"]
        unanswered = results["unanswered"]
        incorrect = results["incorrect"]

        canvas = tk.Canvas(self.content_area, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_area, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_COLOR)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=970)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=15)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 1. Newly Unlocked Achievement Notification (if triggered)
        if self.latest_unlocked_achievements:
            ach_banner = tk.Frame(scroll_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BUTTER_YELLOW, highlightthickness=2)
            ach_banner.pack(fill=tk.X, pady=(0, 15), ipady=8, ipadx=15)

            for ach in self.latest_unlocked_achievements:
                a_row = tk.Frame(ach_banner, bg=CARD_BG)
                a_row.pack(fill=tk.X, pady=2)
                icon_lbl = tk.Label(a_row, text=f"🎉 BADGE UNLOCKED: {ach['icon']} {ach['title']}!", font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
                icon_lbl.pack(side=tk.LEFT)
                reward_lbl = tk.Label(a_row, text=f"+{ach['reward_xp']} XP & +{ach['reward_coins']} Coins 🪙", font=("Segoe UI", 10, "bold"), bg=CARD_BG, fg=PRIMARY_PURPLE)
                reward_lbl.pack(side=tk.RIGHT)

        # 2. Celebration Header Card
        celeb_card = tk.Frame(scroll_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        celeb_card.pack(fill=tk.X, pady=(0, 15), ipady=12, ipadx=18)

        if pct >= 80:
            headline = "🌟 Outstanding Mastery!"
            sub = "Exceptional performance! You demonstrated comprehensive subject understanding."
            badge_color = MINT_GREEN_DARK
        elif pct >= 50:
            headline = "👍 Great Effort!"
            sub = "Well done! Review the detailed explanations below to reach perfection."
            badge_color = PRIMARY_PURPLE
        else:
            headline = "💪 Keep Practicing!"
            sub = "Good learning attempt! Review the explanations below and try again."
            badge_color = SOFT_ROSE

        badge_lbl = tk.Label(celeb_card, text=headline, font=("Segoe UI", 18, "bold"), bg=CARD_BG, fg=badge_color)
        badge_lbl.pack(pady=(4, 2))

        sub_lbl = tk.Label(celeb_card, text=sub, font=("Segoe UI", 10), bg=CARD_BG, fg=TEXT_MUTED)
        sub_lbl.pack(pady=(0, 12))

        # Metrics Row
        metric_row = tk.Frame(celeb_card, bg=CARD_BG)
        metric_row.pack(fill=tk.X, padx=15, pady=(0, 10))

        self._create_metric_box(metric_row, "Score", f"{score} / {total}", PRIMARY_PURPLE)
        self._create_metric_box(metric_row, "Accuracy", f"{pct}%", MINT_GREEN_DARK)
        self._create_metric_box(metric_row, "Correct", str(score), MINT_GREEN_DARK)
        self._create_metric_box(metric_row, "Incorrect", str(incorrect), ROSE_DARK)
        self._create_metric_box(metric_row, "Unanswered", str(unanswered), TEXT_MUTED)
        self._create_metric_box(metric_row, "XP Earned", f"+{results['xp_earned']} XP", PRIMARY_PURPLE)
        self._create_metric_box(metric_row, "Coins Earned", f"+{results['coins_earned']} 🪙", BUTTER_YELLOW)

        # Action Buttons Row
        action_row = tk.Frame(celeb_card, bg=CARD_BG)
        action_row.pack(fill=tk.X, padx=15, pady=(10, 5))

        retake_btn = tk.Button(
            action_row,
            text="↺ Retake Quiz",
            font=("Segoe UI", 10, "bold"),
            bg=PRIMARY_PURPLE,
            fg="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=16,
            pady=7,
            command=self.start_quiz
        )
        retake_btn.pack(side=tk.LEFT, padx=(0, 8))

        home_btn = tk.Button(
            action_row,
            text="🏠 Return to Dashboard",
            font=("Segoe UI", 10),
            bg=SECONDARY_LAVENDER,
            fg=TEXT_MAIN,
            bd=0,
            cursor="hand2",
            padx=14,
            pady=7,
            command=self.show_dashboard_screen
        )
        home_btn.pack(side=tk.LEFT, padx=(0, 8))

        board_btn = tk.Button(
            action_row,
            text="🏆 View Leaderboard",
            font=("Segoe UI", 10),
            bg=CARD_BG,
            fg=TEXT_MAIN,
            bd=0,
            highlightbackground=BORDER_SUBTLE,
            highlightthickness=1,
            cursor="hand2",
            padx=14,
            pady=7,
            command=self.show_leaderboard_screen
        )
        board_btn.pack(side=tk.LEFT)

        # 3. Interactive Answer Review Section (with All vs Mistakes Filter)
        filter_bar = tk.Frame(scroll_frame, bg=BG_COLOR)
        filter_bar.pack(fill=tk.X, pady=(10, 6))

        r_title = tk.Label(filter_bar, text="Answer Review & Conceptual Explanations", font=("Segoe UI", 12, "bold"), bg=BG_COLOR, fg=TEXT_MAIN)
        r_title.pack(side=tk.LEFT)

        all_filter_btn = tk.Button(
            filter_bar,
            text="Show All",
            font=("Segoe UI", 9, "bold" if self.review_filter == "all" else "normal"),
            bg=PRIMARY_PURPLE if self.review_filter == "all" else CARD_BG,
            fg="#FFFFFF" if self.review_filter == "all" else TEXT_MAIN,
            bd=0,
            cursor="hand2",
            padx=10,
            pady=4,
            command=lambda: self._set_review_filter("all")
        )
        all_filter_btn.pack(side=tk.RIGHT, padx=2)

        mistakes_filter_btn = tk.Button(
            filter_bar,
            text="Mistakes Only",
            font=("Segoe UI", 9, "bold" if self.review_filter == "mistakes" else "normal"),
            bg=PRIMARY_PURPLE if self.review_filter == "mistakes" else CARD_BG,
            fg="#FFFFFF" if self.review_filter == "mistakes" else TEXT_MAIN,
            bd=0,
            cursor="hand2",
            padx=10,
            pady=4,
            command=lambda: self._set_review_filter("mistakes")
        )
        mistakes_filter_btn.pack(side=tk.RIGHT, padx=2)

        # Render review cards
        displayed_items = 0
        for item in results["review"]:
            is_right = item["is_correct"]
            if self.review_filter == "mistakes" and is_right:
                continue

            displayed_items += 1
            rev_card = tk.Frame(scroll_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
            rev_card.pack(fill=tk.X, pady=5, ipady=8, ipadx=15)

            icon_mark = "✓" if is_right else ("—" if item["is_unanswered"] else "✗")
            color_mark = MINT_GREEN_DARK if is_right else (TEXT_MUTED if item["is_unanswered"] else ROSE_DARK)

            head_text = f"{icon_mark} Question {item['question_index']}: {item['question_text']}"
            q_head = tk.Label(rev_card, text=head_text, font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=color_mark, wraplength=880, justify=tk.LEFT)
            q_head.pack(anchor=tk.W, padx=12, pady=(4, 4))

            chosen_display = item["chosen_text"]
            correct_display = item["correct_text"]
            ans_info = f"Your Answer: {chosen_display}   |   Correct Answer: {correct_display}"
            ans_lbl = tk.Label(rev_card, text=ans_info, font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_MAIN)
            ans_lbl.pack(anchor=tk.W, padx=12, pady=(0, 4))

            exp_lbl = tk.Label(rev_card, text=f"💡 {item['explanation']}", font=("Segoe UI", 9, "italic"), bg=CARD_BG, fg=TEXT_MUTED, wraplength=880, justify=tk.LEFT)
            exp_lbl.pack(anchor=tk.W, padx=12, pady=(0, 4))

        if displayed_items == 0:
            empty_rev = tk.Label(scroll_frame, text="🎉 No mistakes! You achieved 100% accuracy on every question.", font=("Segoe UI", 11, "bold"), bg=BG_COLOR, fg=MINT_GREEN_DARK)
            empty_rev.pack(pady=20)

    def _create_metric_box(self, parent: tk.Widget, label: str, value: str, color: str) -> None:
        """Create a compact metrics box inside results card."""
        f = tk.Frame(parent, bg=BG_COLOR, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3, ipady=5, ipadx=6)

        v = tk.Label(f, text=value, font=("Segoe UI", 12, "bold"), bg=BG_COLOR, fg=color)
        v.pack()
        l = tk.Label(f, text=label, font=("Segoe UI", 8), bg=BG_COLOR, fg=TEXT_MUTED)
        l.pack()

    def _set_review_filter(self, filter_name: str) -> None:
        """Toggle review filter between 'all' and 'mistakes'."""
        self.review_filter = filter_name
        self.show_results_screen()

    # =========================================================================
    # 5. PROFESSIONAL LEADERBOARD & LOCAL HALL OF FAME
    # =========================================================================

    def show_leaderboard_screen(self) -> None:
        """Render dedicated Leaderboard screen with podium presentation and rankings."""
        self._clear_content()
        self._highlight_nav_tab("leaderboard")
        self.progress = self.storage.load_progress()

        board_frame = tk.Frame(self.content_area, bg=BG_COLOR)
        board_frame.pack(fill=tk.BOTH, expand=True, padx=35, pady=20)

        # 1. Header Card with Honest Transparency
        header_card = tk.Frame(board_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        header_card.pack(fill=tk.X, pady=(0, 15), ipady=10, ipadx=18)

        t_lbl = tk.Label(header_card, text="🏆 Local Player Hall of Fame & Leaderboard", font=("Segoe UI", 16, "bold"), bg=CARD_BG, fg=PRIMARY_PURPLE)
        t_lbl.pack(anchor=tk.W, padx=10)

        sub_lbl = tk.Label(
            header_card,
            text="Tracks your personal best quiz performances, lifetime records, and high scores stored locally on this machine.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_MUTED
        )
        sub_lbl.pack(anchor=tk.W, padx=10)

        # 2. Podium Presentation (Top 3 Performances)
        podium_card = tk.Frame(board_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        podium_card.pack(fill=tk.X, pady=(0, 15), ipady=10, ipadx=15)

        podium_title = tk.Label(podium_card, text="🌟 Top Record Performances", font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        podium_title.pack(anchor=tk.W, padx=10, pady=(0, 8))

        top_records = self.progress.get_leaderboard_records(sort_by="score")[:3]
        podium_row = tk.Frame(podium_card, bg=CARD_BG)
        podium_row.pack(fill=tk.X, padx=10)

        # 3 podium stands
        podium_slots = [
            ("🥈 2nd Place", top_records[1] if len(top_records) > 1 else None, SECONDARY_LAVENDER),
            ("🥇 1st Place", top_records[0] if len(top_records) > 0 else None, BUTTER_YELLOW),
            ("🥉 3rd Place", top_records[2] if len(top_records) > 2 else None, SECONDARY_LAVENDER)
        ]

        for title, rec, bg_c in podium_slots:
            slot_f = tk.Frame(podium_row, bg=BG_COLOR, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
            slot_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, ipady=8)

            badge_l = tk.Label(slot_f, text=title, font=("Segoe UI", 11, "bold"), bg=bg_c, fg=TEXT_MAIN, padx=8, pady=3)
            badge_l.pack(fill=tk.X, padx=5, pady=(2, 6))

            if rec:
                avatar = rec.get("avatar", self.progress.avatar)
                pname = rec.get("player_name", self.progress.player_name)
                score_str = f"{rec.get('score', 0)} / {rec.get('total', 0)} ({rec.get('percentage', 0)}%)"
                cat_str = f"{rec.get('category', 'Quiz')} ({rec.get('difficulty', 'easy').capitalize()})"

                lbl_a = tk.Label(slot_f, text=f"{avatar} {pname}", font=("Segoe UI", 11, "bold"), bg=BG_COLOR, fg=TEXT_MAIN)
                lbl_a.pack()
                lbl_s = tk.Label(slot_f, text=score_str, font=("Segoe UI", 10, "bold"), bg=BG_COLOR, fg=PRIMARY_PURPLE)
                lbl_s.pack()
                lbl_c = tk.Label(slot_f, text=cat_str, font=("Segoe UI", 8), bg=BG_COLOR, fg=TEXT_MUTED)
                lbl_c.pack()
            else:
                lbl_empty = tk.Label(slot_f, text="No record yet", font=("Segoe UI", 9, "italic"), bg=BG_COLOR, fg=TEXT_MUTED)
                lbl_empty.pack(pady=10)

        # 3. All Records Table & Sorting Toolbar
        table_card = tk.Frame(board_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, ipady=8, ipadx=12)

        toolbar = tk.Frame(table_card, bg=CARD_BG)
        toolbar.pack(fill=tk.X, padx=10, pady=(4, 8))

        t_title = tk.Label(toolbar, text="Attempt History & Score Standings", font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        t_title.pack(side=tk.LEFT)

        # Sort Buttons
        sort_recent_btn = tk.Button(toolbar, text="Recent", font=("Segoe UI", 8), bg=SECONDARY_LAVENDER, bd=0, cursor="hand2", padx=8, pady=3, command=lambda: self._refresh_leaderboard_table("recent"))
        sort_recent_btn.pack(side=tk.RIGHT, padx=2)

        sort_pct_btn = tk.Button(toolbar, text="By Accuracy %", font=("Segoe UI", 8), bg=SECONDARY_LAVENDER, bd=0, cursor="hand2", padx=8, pady=3, command=lambda: self._refresh_leaderboard_table("percentage"))
        sort_pct_btn.pack(side=tk.RIGHT, padx=2)

        sort_score_btn = tk.Button(toolbar, text="By Score", font=("Segoe UI", 8, "bold"), bg=PRIMARY_PURPLE, fg="#FFFFFF", bd=0, cursor="hand2", padx=8, pady=3, command=lambda: self._refresh_leaderboard_table("score"))
        sort_score_btn.pack(side=tk.RIGHT, padx=2)

        sort_lbl = tk.Label(toolbar, text="Sort By: ", font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_MUTED)
        sort_lbl.pack(side=tk.RIGHT, padx=4)

        # Treeview
        self.board_table_frame = tk.Frame(table_card, bg=CARD_BG)
        self.board_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

        self._render_leaderboard_tree("score")

    def _refresh_leaderboard_table(self, sort_key: str) -> None:
        """Re-render treeview with new sorting criterion."""
        for widget in self.board_table_frame.winfo_children():
            widget.destroy()
        self._render_leaderboard_tree(sort_key)

    def _render_leaderboard_tree(self, sort_key: str) -> None:
        """Render Treeview populated with sorted quiz attempt records."""
        records = self.progress.get_leaderboard_records(sort_by=sort_key)
        if not records:
            empty_lbl = tk.Label(self.board_table_frame, text="No quiz attempts recorded yet. Play a quiz to enter the Hall of Fame!", font=("Segoe UI", 10, "italic"), bg=CARD_BG, fg=TEXT_MUTED)
            empty_lbl.pack(pady=30)
            return

        columns = ("rank", "player", "category", "difficulty", "mode", "score", "percentage", "date")
        tree = ttk.Treeview(self.board_table_frame, columns=columns, show="headings", height=7)

        tree.heading("rank", text="Rank")
        tree.heading("player", text="Player")
        tree.heading("category", text="Category")
        tree.heading("difficulty", text="Difficulty")
        tree.heading("mode", text="Mode")
        tree.heading("score", text="Score")
        tree.heading("percentage", text="Accuracy")
        tree.heading("date", text="Date & Time")

        tree.column("rank", width=50, anchor=tk.CENTER)
        tree.column("player", width=140, anchor=tk.CENTER)
        tree.column("category", width=150, anchor=tk.CENTER)
        tree.column("difficulty", width=80, anchor=tk.CENTER)
        tree.column("mode", width=80, anchor=tk.CENTER)
        tree.column("score", width=80, anchor=tk.CENTER)
        tree.column("percentage", width=80, anchor=tk.CENTER)
        tree.column("date", width=140, anchor=tk.CENTER)

        for idx, rec in enumerate(records, 1):
            rank_str = f"#{idx}"
            if idx == 1:
                rank_str = "🥇 #1"
            elif idx == 2:
                rank_str = "🥈 #2"
            elif idx == 3:
                rank_str = "🥉 #3"

            p_display = f"{rec.get('avatar', '🦊')} {rec.get('player_name', 'Player')}"
            tree.insert(
                "",
                tk.END,
                values=(
                    rank_str,
                    p_display,
                    rec.get("category", "-"),
                    rec.get("difficulty", "-").capitalize(),
                    rec.get("mode", "learning").capitalize(),
                    f"{rec.get('score', 0)} / {rec.get('total', 0)}",
                    f"{rec.get('percentage', 0.0)}%",
                    rec.get("timestamp", "-")
                )
            )

        scroll = ttk.Scrollbar(self.board_table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # =========================================================================
    # 6. PROFILE & REWARDS SCREEN
    # =========================================================================

    def show_profile_screen(self) -> None:
        """Render player profile, avatar picker, stats, and achievements showcase."""
        self._clear_content()
        self._highlight_nav_tab("profile")
        self.progress = self.storage.load_progress()

        canvas = tk.Canvas(self.content_area, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_area, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_COLOR)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=970)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=15)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 1. Player Card & Name/Avatar Editor
        profile_card = tk.Frame(scroll_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        profile_card.pack(fill=tk.X, pady=(0, 15), ipady=12, ipadx=18)

        left_avatar_frame = tk.Frame(profile_card, bg=CARD_BG)
        left_avatar_frame.pack(side=tk.LEFT, padx=(5, 15))

        big_avatar_lbl = tk.Label(left_avatar_frame, text=self.progress.avatar, font=("Segoe UI", 36), bg=BG_COLOR, padx=12, pady=6)
        big_avatar_lbl.pack()

        # Name and Level info
        info_col = tk.Frame(profile_card, bg=CARD_BG)
        info_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        name_row = tk.Frame(info_col, bg=CARD_BG)
        name_row.pack(fill=tk.X)

        self.name_display_lbl = tk.Label(name_row, text=self.progress.player_name, font=("Segoe UI", 16, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        self.name_display_lbl.pack(side=tk.LEFT)

        rename_btn = tk.Button(
            name_row,
            text="✏️ Change Name",
            font=("Segoe UI", 8),
            bg=SECONDARY_LAVENDER,
            fg=PRIMARY_PURPLE,
            bd=0,
            cursor="hand2",
            padx=8,
            pady=2,
            command=self._prompt_change_name
        )
        rename_btn.pack(side=tk.LEFT, padx=10)

        level_str = f"Level {self.progress.level}  •  {self.progress.level_title}  •  {self.progress.xp} Total XP  •  {self.progress.coins} Coins 🪙"
        sub_info = tk.Label(info_col, text=level_str, font=("Segoe UI", 10), bg=CARD_BG, fg=TEXT_MUTED)
        sub_info.pack(anchor=tk.W, pady=(2, 8))

        # Avatar Selection Palette
        avatar_prompt = tk.Label(info_col, text="Choose Your Player Avatar:", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        avatar_prompt.pack(anchor=tk.W, pady=(0, 4))

        avatar_btn_row = tk.Frame(info_col, bg=CARD_BG)
        avatar_btn_row.pack(anchor=tk.W)

        for av in AVAILABLE_AVATARS:
            is_active = (av["icon"] == self.progress.avatar)
            av_b = tk.Button(
                avatar_btn_row,
                text=av["icon"],
                font=("Segoe UI", 13),
                bg=PRIMARY_PURPLE if is_active else BG_COLOR,
                bd=0,
                cursor="hand2",
                padx=6,
                pady=2,
                command=lambda a=av["icon"]: self._select_new_avatar(a)
            )
            av_b.pack(side=tk.LEFT, padx=3)

        # 2. Achievement Badges Showcase
        badge_section = tk.Frame(scroll_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        badge_section.pack(fill=tk.X, pady=(0, 15), ipady=12, ipadx=18)

        unlocked_count = len(self.progress.achievements)
        total_ach = len(PREDEFINED_ACHIEVEMENTS)

        b_header = tk.Frame(badge_section, bg=CARD_BG)
        b_header.pack(fill=tk.X, padx=10, pady=(2, 10))

        b_title = tk.Label(b_header, text=f"Achievements & Milestone Badges ({unlocked_count}/{total_ach} Unlocked)", font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=TEXT_MAIN)
        b_title.pack(side=tk.LEFT)

        # Badge Grid
        badge_grid = tk.Frame(badge_section, bg=CARD_BG)
        badge_grid.pack(fill=tk.X, padx=10)

        for idx, ach in enumerate(PREDEFINED_ACHIEVEMENTS):
            is_unlocked = self.progress.is_achievement_unlocked(ach["id"])
            card_bg_col = CARD_BG if is_unlocked else BG_COLOR
            border_col = MINT_GREEN if is_unlocked else BORDER_SUBTLE

            b_card = tk.Frame(badge_grid, bg=card_bg_col, highlightbackground=border_col, highlightthickness=1 if not is_unlocked else 2)
            row = idx // 2
            col = idx % 2
            b_card.grid(row=row, column=col, padx=6, pady=5, sticky="nsew")
            badge_grid.grid_columnconfigure(col, weight=1)

            # Inside badge card
            top_b = tk.Frame(b_card, bg=card_bg_col)
            top_b.pack(fill=tk.X, padx=10, pady=(6, 2))

            icon_l = tk.Label(top_b, text=ach["icon"], font=("Segoe UI", 16), bg=card_bg_col)
            icon_l.pack(side=tk.LEFT, padx=(0, 6))

            name_l = tk.Label(top_b, text=ach["title"], font=("Segoe UI", 10, "bold"), bg=card_bg_col, fg=TEXT_MAIN if is_unlocked else TEXT_MUTED)
            name_l.pack(side=tk.LEFT)

            status_text = "✓ UNLOCKED" if is_unlocked else f"+{ach['reward_xp']} XP"
            status_fg = MINT_GREEN_DARK if is_unlocked else PRIMARY_PURPLE
            status_bg = MINT_GREEN_BG if is_unlocked else SECONDARY_LAVENDER

            status_l = tk.Label(top_b, text=status_text, font=("Segoe UI", 8, "bold"), bg=status_bg, fg=status_fg, padx=6, pady=1)
            status_l.pack(side=tk.RIGHT)

            desc_l = tk.Label(b_card, text=ach["description"], font=("Segoe UI", 8), bg=card_bg_col, fg=TEXT_MUTED, wraplength=420, justify=tk.LEFT)
            desc_l.pack(anchor=tk.W, padx=10, pady=(0, 6))

        # 3. Danger Zone / Reset History
        danger_card = tk.Frame(scroll_frame, bg=CARD_BG, relief=tk.FLAT, bd=0, highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        danger_card.pack(fill=tk.X, pady=(0, 10), ipady=8, ipadx=18)

        d_row = tk.Frame(danger_card, bg=CARD_BG)
        d_row.pack(fill=tk.X, padx=10)

        d_text = tk.Label(d_row, text="Clear Quiz History & Records (Preserves Player Name and Avatar)", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_MUTED)
        d_text.pack(side=tk.LEFT)

        clear_btn = tk.Button(
            d_row,
            text="🗑 Clear Records",
            font=("Segoe UI", 9),
            bg=ROSE_BG,
            fg=ROSE_DARK,
            bd=0,
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._confirm_clear_profile_history
        )
        clear_btn.pack(side=tk.RIGHT)

    def _prompt_change_name(self) -> None:
        """Prompt dialog to edit local player display name."""
        new_name = simpledialog.askstring("Edit Player Name", "Enter your preferred player name (max 20 chars):", initialvalue=self.progress.player_name)
        if new_name and new_name.strip():
            clean = new_name.strip()[:20]
            self.progress.player_name = clean
            self.storage.save_progress(self.progress)
            self._update_header_chip()
            self.show_profile_screen()

    def _select_new_avatar(self, avatar: str) -> None:
        """Update and persist selected player avatar."""
        self.progress.avatar = avatar
        self.storage.save_progress(self.progress)
        self._update_header_chip()
        self.show_profile_screen()

    def _confirm_clear_profile_history(self) -> None:
        """Confirm and clear player history."""
        if messagebox.askyesno("Clear Records", "Are you sure you want to reset your quiz history, XP, and high scores?"):
            self.progress.clear_history()
            self.storage.save_progress(self.progress)
            self._update_header_chip()
            self.show_profile_screen()


def launch_gui() -> None:
    """Standard bootstrap function to launch QuizUp desktop GUI."""
    root = tk.Tk()
    app = QuizUpGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
