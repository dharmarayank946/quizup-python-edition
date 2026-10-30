import React, { useState, useEffect, useRef } from 'react';

// Render production backend URL or fallback to env/localhost
const API_BASE = (import.meta.env.VITE_API_URL || 'https://quizup-python-edition.onrender.com').replace(/\/+$/, '');

// Rich offline question bank for zero-downtime during backend hibernation
const OFFLINE_QUESTIONS = {
  Technology: [
    {
      id: "tech-1",
      category: "Technology",
      difficulty: "easy",
      question: "Which keyword is used to define a function in Python?",
      options: ["func", "def", "function", "lambda"],
      correct_index: 1,
      explanation: "'def' (short for define) is the standard Python keyword used to declare functions."
    },
    {
      id: "tech-2",
      category: "Technology",
      difficulty: "easy",
      question: "What is the time complexity of looking up a key in a Python dictionary on average?",
      options: ["O(n)", "O(log n)", "O(1)", "O(n^2)"],
      correct_index: 2,
      explanation: "Python dictionaries use hash tables under the hood, yielding O(1) average lookup time."
    },
    {
      id: "tech-3",
      category: "Technology",
      difficulty: "medium",
      question: "Which of the following data structures is immutable in Python?",
      options: ["list", "dict", "set", "tuple"],
      correct_index: 3,
      explanation: "Tuples cannot be altered after creation, making them immutable and hashable."
    },
    {
      id: "tech-4",
      category: "Technology",
      difficulty: "medium",
      question: "In React, what hook is primarily used for managing component side-effects?",
      options: ["useState", "useEffect", "useMemo", "useContext"],
      correct_index: 1,
      explanation: "useEffect handles lifecycles, subscriptions, DOM mutations, and API fetches."
    },
    {
      id: "tech-5",
      category: "Technology",
      difficulty: "hard",
      question: "What Python feature allows iterating over data without storing all elements in memory?",
      options: ["List comprehension", "Generators (yield)", "Decorators", "Metaclasses"],
      correct_index: 1,
      explanation: "Generators use 'yield' to produce values on-demand using lazy evaluation."
    }
  ],
  "General Knowledge": [
    {
      id: "gk-1",
      category: "General Knowledge",
      difficulty: "easy",
      question: "Which planet is known as the Red Planet?",
      options: ["Venus", "Mars", "Jupiter", "Saturn"],
      correct_index: 1,
      explanation: "Mars appears reddish due to iron oxide (rust) widespread across its surface."
    },
    {
      id: "gk-2",
      category: "General Knowledge",
      difficulty: "medium",
      question: "Which ocean is the deepest in the world?",
      options: ["Atlantic Ocean", "Indian Ocean", "Pacific Ocean", "Arctic Ocean"],
      correct_index: 2,
      explanation: "The Pacific Ocean contains the Mariana Trench, the deepest trench on Earth (~11,000m)."
    },
    {
      id: "gk-3",
      category: "General Knowledge",
      difficulty: "easy",
      question: "What is the capital city of Australia?",
      options: ["Sydney", "Melbourne", "Canberra", "Brisbane"],
      correct_index: 2,
      explanation: "Canberra was chosen as the capital in 1908 as a compromise between Sydney and Melbourne."
    }
  ],
  Academics: [
    {
      id: "acad-1",
      category: "Academics",
      difficulty: "easy",
      question: "What is the chemical symbol for Gold?",
      options: ["Ag", "Au", "Fe", "Pb"],
      correct_index: 1,
      explanation: "Au comes from the Latin word 'Aurum', meaning shining dawn."
    },
    {
      id: "acad-2",
      category: "Academics",
      difficulty: "medium",
      question: "What is the powerhouse organelle of a eukaryotic cell?",
      options: ["Ribosome", "Nucleus", "Mitochondria", "Golgi body"],
      correct_index: 2,
      explanation: "Mitochondria generate most of the chemical energy needed by cellular biochemical reactions (ATP)."
    }
  ]
};

const DEFAULT_CATEGORIES = [
  { name: "Technology", icon: "💻", color: "from-violet-500 to-indigo-600", questions: 28 },
  { name: "General Knowledge", icon: "🌐", color: "from-blue-500 to-cyan-600", questions: 24 },
  { name: "Academics", icon: "📚", color: "from-emerald-500 to-teal-600", questions: 22 },
  { name: "Competitive Exams", icon: "🏆", color: "from-amber-500 to-orange-600", questions: 20 },
  { name: "Sports", icon: "⚽", color: "from-rose-500 to-red-600", questions: 18 },
  { name: "Entertainment", icon: "🎬", color: "from-purple-500 to-pink-600", questions: 20 }
];

const AVATARS = ["🚀", "👑", "🧠", "🦉", "⚡", "🦊", "🎮", "💎"];

export default function App() {
  // Navigation
  const [activeTab, setActiveTab] = useState('play'); // 'play', 'leaderboard', 'achievements'
  
  // Player state
  const [playerName, setPlayerName] = useState(() => localStorage.getItem('quizup_name') || 'QuizChampion');
  const [avatar, setAvatar] = useState(() => localStorage.getItem('quizup_avatar') || '🚀');
  const [xp, setXp] = useState(() => parseInt(localStorage.getItem('quizup_xp') || '420', 10));
  const [coins, setCoins] = useState(() => parseInt(localStorage.getItem('quizup_coins') || '150', 10));
  const [streak, setStreak] = useState(() => parseInt(localStorage.getItem('quizup_streak') || '3', 10));
  const [level, setLevel] = useState(() => Math.floor(xp / 200) + 1);

  // Backend Health
  const [backendStatus, setBackendStatus] = useState('checking'); // 'live', 'offline', 'checking'

  // Quiz Setup state
  const [mode, setMode] = useState('learning'); // 'learning', 'exam'
  const [difficulty, setDifficulty] = useState('easy'); // 'easy', 'medium', 'hard'
  const [numQuestions, setNumQuestions] = useState(5);

  // Active Quiz Game state
  const [inGame, setInGame] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [selectedOption, setSelectedOption] = useState(null);
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false);
  const [timeLeft, setTimeLeft] = useState(15);
  const [timerActive, setTimerActive] = useState(false);

  // Results state
  const [quizFinished, setQuizFinished] = useState(false);
  const [resultsData, setResultsData] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Leaderboard data
  const [leaderboard, setLeaderboard] = useState([]);

  // Check Backend Liveness on mount
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(r => r.json())
      .then(d => {
        if (d.status === 'healthy') setBackendStatus('live');
        else setBackendStatus('offline');
      })
      .catch(() => setBackendStatus('offline'));

    // Fetch initial leaderboard
    fetch(`${API_BASE}/api/v1/quiz/leaderboard`)
      .then(r => r.json())
      .then(d => {
        if (d.leaderboard) setLeaderboard(d.leaderboard);
      })
      .catch(() => {
        setLeaderboard([
          { rank: 1, name: "Elena Rostova", avatar: "👑", level: 14, xp: 4820, coins: 1250, accuracy: 94.2 },
          { rank: 2, name: "Aarav Sharma", avatar: "🚀", level: 12, xp: 3950, coins: 980, accuracy: 91.5 },
          { rank: 3, name: "Kenji Sato", avatar: "🧠", level: 11, xp: 3410, coins: 820, accuracy: 88.0 },
          { rank: 4, name: "Sophia Miller", avatar: "🦉", level: 9, xp: 2740, coins: 640, accuracy: 85.4 },
          { rank: 5, name: "Lucas Silva", avatar: "⚡", level: 8, xp: 2180, coins: 510, accuracy: 82.1 }
        ]);
      });
  }, []);

  // Save profile changes to local storage
  useEffect(() => {
    localStorage.setItem('quizup_name', playerName);
    localStorage.setItem('quizup_avatar', avatar);
    localStorage.setItem('quizup_xp', xp.toString());
    localStorage.setItem('quizup_coins', coins.toString());
    localStorage.setItem('quizup_streak', streak.toString());
    setLevel(Math.floor(xp / 200) + 1);
  }, [playerName, avatar, xp, coins, streak]);

  // Exam mode countdown timer
  useEffect(() => {
    let interval = null;
    if (inGame && mode === 'exam' && timerActive && timeLeft > 0 && !isAnswerSubmitted) {
      interval = setInterval(() => {
        setTimeLeft(t => t - 1);
      }, 1000);
    } else if (inGame && mode === 'exam' && timeLeft === 0 && !isAnswerSubmitted) {
      // Time expired: auto-advance with no selection
      handleSelectOption(-1);
      handleSubmitQuestionAnswer();
    }
    return () => clearInterval(interval);
  }, [inGame, mode, timerActive, timeLeft, isAnswerSubmitted]);

  // Start a Quiz Session
  const startQuiz = async (categoryName, isDaily = false) => {
    setIsSubmitting(true);
    let loadedQuestions = [];
    let newSessionId = `local-${Date.now()}`;

    try {
      if (isDaily) {
        const res = await fetch(`${API_BASE}/api/v1/quiz/daily-spark`);
        if (res.ok) {
          const data = await res.json();
          newSessionId = data.session_id;
          loadedQuestions = data.questions;
        }
      } else {
        const res = await fetch(`${API_BASE}/api/v1/quiz/session/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            category: categoryName,
            difficulty: difficulty,
            mode: mode,
            num_questions: numQuestions
          })
        });
        if (res.ok) {
          const data = await res.json();
          newSessionId = data.session_id;
          loadedQuestions = data.questions;
        }
      }
    } catch (err) {
      console.warn("Backend unavailable, using offline fallback:", err);
    }

    // Fallback if backend returned empty or network failed
    if (!loadedQuestions || loadedQuestions.length === 0) {
      const fallbackPool = OFFLINE_QUESTIONS[categoryName] || OFFLINE_QUESTIONS["Technology"];
      loadedQuestions = [...fallbackPool].sort(() => 0.5 - Math.random()).slice(0, numQuestions);
    }

    setSessionId(newSessionId);
    setQuestions(loadedQuestions);
    setCurrentIdx(0);
    setAnswers([]);
    setSelectedOption(null);
    setIsAnswerSubmitted(false);
    setTimeLeft(15);
    setTimerActive(true);
    setQuizFinished(false);
    setResultsData(null);
    setInGame(true);
    setIsSubmitting(false);
  };

  const handleSelectOption = (index) => {
    if (isAnswerSubmitted && mode === 'learning') return;
    setSelectedOption(index);

    if (mode === 'learning') {
      setIsAnswerSubmitted(true);
    }
  };

  const handleSubmitQuestionAnswer = () => {
    const curQ = questions[currentIdx];
    const newAnswers = [
      ...answers,
      {
        question_id: curQ.id,
        selected_index: selectedOption !== null ? selectedOption : -1,
        time_spent_sec: 15 - timeLeft
      }
    ];
    setAnswers(newAnswers);

    if (currentIdx + 1 < questions.length) {
      // Advance to next question
      setCurrentIdx(i => i + 1);
      setSelectedOption(null);
      setIsAnswerSubmitted(false);
      setTimeLeft(15);
      setTimerActive(true);
    } else {
      // Quiz complete: calculate score & submit
      finalizeQuiz(newAnswers);
    }
  };

  const finalizeQuiz = async (finalAnswers) => {
    setIsSubmitting(true);
    setTimerActive(false);

    let result = null;
    try {
      const res = await fetch(`${API_BASE}/api/v1/quiz/session/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          answers: finalAnswers,
          player_name: playerName
        })
      });
      if (res.ok) {
        result = await res.json();
      }
    } catch (e) {
      console.warn("Submit failed, computing locally:", e);
    }

    // If server result failed, compute locally
    if (!result) {
      let correct = 0;
      const details = [];
      finalAnswers.forEach((ans, idx) => {
        const q = questions[idx];
        const isCorrect = (q.correct_index !== undefined) ? (ans.selected_index === q.correct_index) : false;
        if (isCorrect) correct++;
        details.push({
          question: q.question,
          options: q.options,
          selected_index: ans.selected_index,
          correct_index: q.correct_index,
          is_correct: isCorrect,
          explanation: q.explanation || "Review fundamental concepts."
        });
      });

      const acc = Math.round((correct / finalAnswers.length) * 100);
      const earnedXp = (correct * 20) + (acc >= 80 ? 25 : 0) + (acc === 100 ? 50 : 0);
      const earnedCoins = (correct * 10) + (acc >= 80 ? 20 : 0);

      result = {
        total_questions: finalAnswers.length,
        correct_answers: correct,
        accuracy_percentage: acc,
        xp_earned: earnedXp,
        coins_earned: earnedCoins,
        review_details: details
      };
    }

    // Update player stats
    setXp(x => x + (result.xp_earned || 50));
    setCoins(c => c + (result.coins_earned || 25));
    if (result.accuracy_percentage >= 60) {
      setStreak(s => s + 1);
    }

    setResultsData(result);
    setInGame(false);
    setQuizFinished(true);
    setIsSubmitting(false);
  };

  const currentQ = questions[currentIdx];

  return (
    <div style={{ minHeight: '100vh', padding: '24px 16px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      
      {/* Top Navbar & HUD */}
      <header className="glass-panel" style={{ width: '100%', maxWidth: '1080px', padding: '16px 24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
          
          {/* Logo & Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '44px',
              height: '44px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '24px',
              boxShadow: '0 0 16px rgba(139, 92, 246, 0.4)'
            }}>
              ⚡
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h1 style={{ fontSize: '20px', fontWeight: '800', letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #fff, #c4b5fd)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  QuizUp
                </h1>
                <span style={{ fontSize: '11px', fontWeight: '700', padding: '2px 8px', borderRadius: '6px', background: 'rgba(139, 92, 246, 0.2)', color: '#c4b5fd', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
                  PYTHON EDITION
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Battle of Wits & Daily Sparks</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav style={{ display: 'flex', gap: '6px', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            {[
              { id: 'play', label: '🎮 Play' },
              { id: 'leaderboard', label: '🏆 Leaderboard' },
              { id: 'achievements', label: '🎖️ Badges' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id); setInGame(false); setQuizFinished(false); }}
                style={{
                  padding: '8px 16px',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: activeTab === tab.id ? '#fff' : 'var(--text-muted)',
                  background: activeTab === tab.id ? 'var(--primary)' : 'transparent',
                  boxShadow: activeTab === tab.id ? '0 4px 12px rgba(139, 92, 246, 0.4)' : 'none'
                }}
              >
                {tab.label}
              </button>
            ))}
          </nav>

          {/* Player Stats HUD */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* Streak */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '6px 12px', borderRadius: '10px' }}>
              <span style={{ fontSize: '16px' }}>🔥</span>
              <span style={{ fontSize: '13px', fontWeight: '700', color: '#fbbf24' }}>{streak}</span>
            </div>

            {/* Coins */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '6px 12px', borderRadius: '10px' }}>
              <span style={{ fontSize: '16px' }}>🪙</span>
              <span style={{ fontSize: '13px', fontWeight: '700', color: '#34d399' }}>{coins}</span>
            </div>

            {/* Level & XP */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255, 255, 255, 0.04)', padding: '4px 12px 4px 6px', borderRadius: '24px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#8b5cf6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px' }}>
                {avatar}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '12px', fontWeight: '700', color: '#fff' }}>Lvl {level}</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{xp} XP</span>
                </div>
                <div style={{ width: '60px', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden', marginTop: '2px' }}>
                  <div style={{ width: `${(xp % 200) / 2}%`, height: '100%', background: 'linear-gradient(90deg, #8b5cf6, #ec4899)' }} />
                </div>
              </div>
            </div>

            {/* Backend status dot */}
            <div title={backendStatus === 'live' ? 'Render Backend Live' : 'Backend Cold-Starting (Offline Mode Ready)'} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: backendStatus === 'live' ? '#10b981' : '#f59e0b',
                boxShadow: backendStatus === 'live' ? '0 0 8px #10b981' : '0 0 8px #f59e0b'
              }} />
            </div>

          </div>

        </div>
      </header>

      {/* Main Container */}
      <main style={{ width: '100%', maxWidth: '1080px' }}>

        {/* ============================================================== */}
        {/* VIEW 1: PLAY MODE SELECTION & CATEGORIES GRID */}
        {/* ============================================================== */}
        {activeTab === 'play' && !inGame && !quizFinished && (
          <div className="animate-pop">
            
            {/* Daily Spark Banner */}
            <div className="glass-panel-glow" style={{
              background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(236, 72, 153, 0.15))',
              padding: '24px 28px',
              borderRadius: '20px',
              marginBottom: '28px',
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '20px'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', fontWeight: '800', letterSpacing: '0.08em', textTransform: 'uppercase', color: '#f43f5e', background: 'rgba(244, 63, 94, 0.15)', padding: '3px 8px', borderRadius: '6px' }}>
                    DAILY SPECIAL
                  </span>
                  <span style={{ fontSize: '12px', color: '#c4b5fd' }}>⚡ Double XP + 50 Coins</span>
                </div>
                <h2 style={{ fontSize: '24px', fontWeight: '800', color: '#fff', marginBottom: '4px' }}>
                  Daily Spark Trivia Challenge
                </h2>
                <p style={{ fontSize: '14px', color: 'var(--text-muted)', maxWidth: '540px' }}>
                  5 curated questions spanning tech, science, and world trivia. Test your speed and keep your daily streak alive!
                </p>
              </div>

              <button
                onClick={() => startQuiz("Daily Spark", true)}
                disabled={isSubmitting}
                style={{
                  padding: '14px 28px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, #ec4899, #8b5cf6)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '15px',
                  boxShadow: '0 8px 24px rgba(236, 72, 153, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}
              >
                <span>⚡ Play Daily Spark</span>
                <span style={{ fontSize: '18px' }}>→</span>
              </button>
            </div>

            {/* Game Options Bar: Mode, Difficulty, Question Count */}
            <div className="glass-panel" style={{ padding: '16px 24px', marginBottom: '24px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
              
              {/* Mode Toggle */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-muted)' }}>Mode:</span>
                <div style={{ display: 'flex', background: 'rgba(0,0,0,0.3)', padding: '3px', borderRadius: '10px' }}>
                  <button
                    onClick={() => setMode('learning')}
                    style={{
                      padding: '6px 14px',
                      borderRadius: '8px',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: mode === 'learning' ? '#fff' : 'var(--text-muted)',
                      background: mode === 'learning' ? '#8b5cf6' : 'transparent'
                    }}
                  >
                    📖 Learning (Instant Feedback)
                  </button>
                  <button
                    onClick={() => setMode('exam')}
                    style={{
                      padding: '6px 14px',
                      borderRadius: '8px',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: mode === 'exam' ? '#fff' : 'var(--text-muted)',
                      background: mode === 'exam' ? '#ec4899' : 'transparent'
                    }}
                  >
                    ⏱️ Exam (15s Timer)
                  </button>
                </div>
              </div>

              {/* Difficulty & Count */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Difficulty:</span>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    style={{
                      background: 'rgba(255,255,255,0.06)',
                      border: '1px solid var(--border-subtle)',
                      color: '#fff',
                      padding: '6px 12px',
                      borderRadius: '8px',
                      fontSize: '13px'
                    }}
                  >
                    <option value="easy">🟢 Easy</option>
                    <option value="medium">🟡 Medium</option>
                    <option value="hard">🔴 Hard</option>
                  </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Count:</span>
                  <select
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(parseInt(e.target.value, 10))}
                    style={{
                      background: 'rgba(255,255,255,0.06)',
                      border: '1px solid var(--border-subtle)',
                      color: '#fff',
                      padding: '6px 12px',
                      borderRadius: '8px',
                      fontSize: '13px'
                    }}
                  >
                    <option value={3}>3 Questions</option>
                    <option value={5}>5 Questions</option>
                    <option value={10}>10 Questions</option>
                  </select>
                </div>
              </div>

            </div>

            {/* Category Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(310px, 1fr))', gap: '20px' }}>
              {DEFAULT_CATEGORIES.map((cat) => (
                <div
                  key={cat.name}
                  className="glass-panel"
                  style={{
                    padding: '24px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                      <div style={{
                        width: '50px',
                        height: '50px',
                        borderRadius: '14px',
                        background: 'rgba(255,255,255,0.06)',
                        border: '1px solid var(--border-subtle)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '26px'
                      }}>
                        {cat.icon}
                      </div>
                      <span style={{ fontSize: '11px', fontWeight: '700', padding: '4px 10px', borderRadius: '12px', background: 'rgba(255,255,255,0.06)', color: 'var(--text-muted)' }}>
                        {cat.questions} Questions
                      </span>
                    </div>

                    <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#fff', marginBottom: '6px' }}>
                      {cat.name}
                    </h3>
                    <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5', marginBottom: '20px' }}>
                      Master fundamental and advanced questions, earn badges, and test your knowledge.
                    </p>
                  </div>

                  <button
                    onClick={() => startQuiz(cat.name)}
                    disabled={isSubmitting}
                    style={{
                      width: '100%',
                      padding: '12px',
                      borderRadius: '10px',
                      background: 'rgba(139, 92, 246, 0.15)',
                      border: '1px solid rgba(139, 92, 246, 0.35)',
                      color: '#c4b5fd',
                      fontWeight: '700',
                      fontSize: '13px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px'
                    }}
                  >
                    <span>Start Battle</span>
                    <span>→</span>
                  </button>
                </div>
              ))}
            </div>

          </div>
        )}

        {/* ============================================================== */}
        {/* VIEW 2: ACTIVE QUESTION SCREEN */}
        {/* ============================================================== */}
        {inGame && currentQ && (
          <div className="animate-pop" style={{ maxWidth: '780px', margin: '0 auto' }}>
            
            {/* Header info: Progress & Timer */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#a78bfa' }}>
                  {currentQ.category}
                </span>
                <span style={{ color: 'var(--text-faint)' }}>•</span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Question {currentIdx + 1} of {questions.length}
                </span>
              </div>

              {/* Timer for Exam Mode */}
              {mode === 'exam' && (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: timeLeft <= 5 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(139, 92, 246, 0.2)',
                  border: `1px solid ${timeLeft <= 5 ? '#ef4444' : '#8b5cf6'}`,
                  padding: '4px 12px',
                  borderRadius: '20px',
                  color: timeLeft <= 5 ? '#f87171' : '#c4b5fd',
                  fontWeight: '700',
                  fontSize: '13px'
                }}>
                  <span>⏱️</span>
                  <span>{timeLeft}s</span>
                </div>
              )}
            </div>

            {/* Progress Bar */}
            <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden', marginBottom: '24px' }}>
              <div style={{ width: `${((currentIdx + 1) / questions.length) * 100}%`, height: '100%', background: 'linear-gradient(90deg, #8b5cf6, #ec4899)', transition: 'width 0.3s ease' }} />
            </div>

            {/* Question Card */}
            <div className="glass-panel" style={{ padding: '32px 28px', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '700', lineHeight: '1.5', color: '#fff' }}>
                {currentQ.question}
              </h2>
            </div>

            {/* 4 Options Grid */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '24px' }}>
              {currentQ.options.map((option, idx) => {
                const isSelected = selectedOption === idx;
                const isCorrect = currentQ.correct_index === idx;

                let btnBg = 'rgba(26, 29, 49, 0.6)';
                let btnBorder = 'var(--border-subtle)';
                let textColor = '#f8fafc';

                if (mode === 'learning' && isAnswerSubmitted) {
                  if (isCorrect) {
                    btnBg = 'rgba(16, 185, 129, 0.25)';
                    btnBorder = '#10b981';
                    textColor = '#34d399';
                  } else if (isSelected && !isCorrect) {
                    btnBg = 'rgba(239, 68, 68, 0.25)';
                    btnBorder = '#ef4444';
                    textColor = '#f87171';
                  }
                } else if (isSelected) {
                  btnBg = 'rgba(139, 92, 246, 0.25)';
                  btnBorder = '#8b5cf6';
                  textColor = '#c4b5fd';
                }

                return (
                  <button
                    key={idx}
                    onClick={() => handleSelectOption(idx)}
                    disabled={mode === 'learning' && isAnswerSubmitted}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '14px',
                      padding: '16px 20px',
                      borderRadius: '14px',
                      background: btnBg,
                      border: `1.5px solid ${btnBorder}`,
                      color: textColor,
                      textAlign: 'left',
                      fontSize: '15px',
                      fontWeight: '500',
                      transition: 'all 0.2s ease',
                      boxShadow: isSelected ? '0 4px 16px rgba(139, 92, 246, 0.2)' : 'none'
                    }}
                  >
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '8px',
                      background: isSelected ? '#8b5cf6' : 'rgba(255,255,255,0.06)',
                      color: isSelected ? '#fff' : 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '13px',
                      fontWeight: '700'
                    }}>
                      {String.fromCharCode(65 + idx)}
                    </div>
                    <span style={{ flex: 1 }}>{option}</span>
                  </button>
                );
              })}
            </div>

            {/* Explanation card for Learning Mode */}
            {mode === 'learning' && isAnswerSubmitted && (
              <div className="glass-panel animate-pop" style={{
                padding: '20px',
                borderRadius: '14px',
                marginBottom: '24px',
                background: selectedOption === currentQ.correct_index ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                border: `1px solid ${selectedOption === currentQ.correct_index ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span>{selectedOption === currentQ.correct_index ? '✅ Brilliant!' : '💡 Explanation:'}</span>
                </div>
                <p style={{ fontSize: '14px', color: 'var(--text-main)', lineHeight: '1.5' }}>
                  {currentQ.explanation}
                </p>
              </div>
            )}

            {/* Action Bar */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                onClick={() => setInGame(false)}
                style={{
                  padding: '12px 20px',
                  borderRadius: '10px',
                  background: 'rgba(255,255,255,0.05)',
                  color: 'var(--text-muted)',
                  fontSize: '14px',
                  fontWeight: '600'
                }}
              >
                Exit Game
              </button>

              <button
                onClick={handleSubmitQuestionAnswer}
                disabled={selectedOption === null && mode === 'exam'}
                style={{
                  padding: '12px 28px',
                  borderRadius: '10px',
                  background: (mode === 'learning' && !isAnswerSubmitted) ? 'rgba(255,255,255,0.1)' : 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                  color: '#fff',
                  fontSize: '14px',
                  fontWeight: '700',
                  boxShadow: '0 6px 20px rgba(139, 92, 246, 0.35)',
                  cursor: (selectedOption === null && mode === 'exam') ? 'not-allowed' : 'pointer'
                }}
              >
                {currentIdx + 1 === questions.length ? 'Finish Quiz 🏁' : 'Next Question →'}
              </button>
            </div>

          </div>
        )}

        {/* ============================================================== */}
        {/* VIEW 3: QUIZ RESULTS & REWARDS SUMMARY */}
        {/* ============================================================== */}
        {quizFinished && resultsData && (
          <div className="animate-pop" style={{ maxWidth: '780px', margin: '0 auto' }}>
            
            <div className="glass-panel-glow" style={{ padding: '36px 32px', textAlign: 'center', borderRadius: '24px', marginBottom: '28px' }}>
              <div style={{ fontSize: '54px', marginBottom: '12px' }}>
                {resultsData.accuracy_percentage >= 80 ? '🏆' : resultsData.accuracy_percentage >= 50 ? '🌟' : '🎯'}
              </div>

              <h2 style={{ fontSize: '28px', fontWeight: '800', color: '#fff', marginBottom: '6px' }}>
                {resultsData.accuracy_percentage >= 80 ? 'Mastery Achieved!' : resultsData.accuracy_percentage >= 50 ? 'Well Played!' : 'Good Effort!'}
              </h2>
              <p style={{ fontSize: '15px', color: 'var(--text-muted)', marginBottom: '28px' }}>
                You answered {resultsData.correct_answers} out of {resultsData.total_questions} questions correctly ({resultsData.accuracy_percentage}%)
              </p>

              {/* Reward stats cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '16px', marginBottom: '32px' }}>
                <div style={{ background: 'rgba(139, 92, 246, 0.15)', border: '1px solid rgba(139, 92, 246, 0.3)', padding: '16px', borderRadius: '16px' }}>
                  <div style={{ fontSize: '20px', marginBottom: '4px' }}>⚡</div>
                  <div style={{ fontSize: '22px', fontWeight: '800', color: '#c4b5fd' }}>+{resultsData.xp_earned}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>XP Earned</div>
                </div>

                <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '16px', borderRadius: '16px' }}>
                  <div style={{ fontSize: '20px', marginBottom: '4px' }}>🪙</div>
                  <div style={{ fontSize: '22px', fontWeight: '800', color: '#34d399' }}>+{resultsData.coins_earned}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>Coins Won</div>
                </div>

                <div style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '16px', borderRadius: '16px' }}>
                  <div style={{ fontSize: '20px', marginBottom: '4px' }}>🔥</div>
                  <div style={{ fontSize: '22px', fontWeight: '800', color: '#fbbf24' }}>{streak}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>Day Streak</div>
                </div>
              </div>

              {/* CTA Buttons */}
              <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '14px' }}>
                <button
                  onClick={() => { setQuizFinished(false); setInGame(false); setActiveTab('play'); }}
                  style={{
                    padding: '14px 28px',
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                    color: '#fff',
                    fontWeight: '700',
                    fontSize: '14px',
                    boxShadow: '0 8px 24px rgba(139, 92, 246, 0.4)'
                  }}
                >
                  🎮 Play Another Quiz
                </button>

                <button
                  onClick={() => { setQuizFinished(false); setActiveTab('leaderboard'); }}
                  style={{
                    padding: '14px 24px',
                    borderRadius: '12px',
                    background: 'rgba(255,255,255,0.06)',
                    border: '1px solid var(--border-subtle)',
                    color: '#fff',
                    fontWeight: '600',
                    fontSize: '14px'
                  }}
                >
                  🏆 View Leaderboard
                </button>
              </div>

            </div>

          </div>
        )}

        {/* ============================================================== */}
        {/* VIEW 4: LEADERBOARD / HALL OF FAME */}
        {/* ============================================================== */}
        {activeTab === 'leaderboard' && (
          <div className="animate-pop" style={{ maxWidth: '820px', margin: '0 auto' }}>
            <div className="glass-panel" style={{ padding: '28px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                <div>
                  <h2 style={{ fontSize: '22px', fontWeight: '800', color: '#fff' }}>Hall of Fame</h2>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Top trivia champions and high scorers</p>
                </div>
                <div style={{ fontSize: '32px' }}>👑</div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {leaderboard.map((player) => (
                  <div
                    key={player.rank}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '14px 18px',
                      borderRadius: '12px',
                      background: player.rank === 1 ? 'rgba(245, 158, 11, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                      border: `1px solid ${player.rank === 1 ? 'rgba(245, 158, 11, 0.3)' : 'var(--border-subtle)'}`
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <div style={{
                        width: '28px',
                        fontSize: '14px',
                        fontWeight: '800',
                        color: player.rank === 1 ? '#fbbf24' : player.rank === 2 ? '#94a3b8' : player.rank === 3 ? '#b45309' : 'var(--text-faint)'
                      }}>
                        #{player.rank}
                      </div>

                      <div style={{ fontSize: '24px' }}>{player.avatar}</div>

                      <div>
                        <div style={{ fontSize: '15px', fontWeight: '700', color: '#fff' }}>{player.name}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Level {player.level} • {player.accuracy}% accuracy</div>
                      </div>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '15px', fontWeight: '800', color: '#c4b5fd' }}>{player.xp} XP</div>
                      <div style={{ fontSize: '12px', color: '#34d399' }}>🪙 {player.coins}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* VIEW 5: BADGES & ACHIEVEMENTS */}
        {/* ============================================================== */}
        {activeTab === 'achievements' && (
          <div className="animate-pop" style={{ maxWidth: '820px', margin: '0 auto' }}>
            <div className="glass-panel" style={{ padding: '28px' }}>
              <h2 style={{ fontSize: '22px', fontWeight: '800', color: '#fff', marginBottom: '6px' }}>
                Badges & Achievements
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '24px' }}>
                Complete games, build streaks, and unlock prestigious gamer honors.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
                {[
                  { icon: '🚀', title: 'First Flight', desc: 'Complete your very first quiz session', unlocked: true },
                  { icon: '⚡', title: 'Daily Spark Hero', desc: 'Finish 3 Daily Spark challenges', unlocked: true },
                  { icon: '🔥', title: 'On Fire', desc: 'Maintain a 3-day quiz streak', unlocked: streak >= 3 },
                  { icon: '🧠', title: 'Code Wizard', desc: 'Achieve 100% on Technology Hard quiz', unlocked: false },
                  { icon: '👑', title: 'Grandmaster', desc: 'Reach Level 10 and amass 2000 XP', unlocked: level >= 10 },
                  { icon: '💎', title: 'Coin Tycoon', desc: 'Accumulate 500 Quiz Coins', unlocked: coins >= 500 }
                ].map((badge, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '18px',
                      borderRadius: '14px',
                      background: badge.unlocked ? 'rgba(139, 92, 246, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                      border: `1px solid ${badge.unlocked ? 'rgba(139, 92, 246, 0.3)' : 'var(--border-subtle)'}`,
                      opacity: badge.unlocked ? 1 : 0.5
                    }}
                  >
                    <div style={{ fontSize: '32px', marginBottom: '8px' }}>{badge.icon}</div>
                    <div style={{ fontSize: '15px', fontWeight: '700', color: '#fff', marginBottom: '4px' }}>{badge.title}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>{badge.desc}</div>
                    <div style={{ marginTop: '10px', fontSize: '11px', fontWeight: '700', color: badge.unlocked ? '#34d399' : 'var(--text-faint)' }}>
                      {badge.unlocked ? '✅ UNLOCKED' : '🔒 LOCKED'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer style={{ marginTop: 'auto', paddingTop: '40px', paddingBottom: '16px', textAlign: 'center', color: 'var(--text-faint)', fontSize: '12px' }}>
        <p>QuizUp Python Edition • Microservice API on Render • Frontend on Vercel</p>
      </footer>

    </div>
  );
}
