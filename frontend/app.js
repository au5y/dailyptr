const API = "api";
let current = null; // currently loaded ChallengeOut
let appConfig = { ai_grading_enabled: false };
let tracks = []; // [{id, name}]
let currentTrack = localStorage.getItem("cdr-track") || "cpp_core";
let currentTab = "quiz";
let historyByDate = {}; // date string -> DayOut, for the current track (refreshed each time History opens)
let calYear, calMonth; // calendar's currently displayed month (0-based month)
let isGuest = false;

// ---------- guest mode ----------
const GUEST_STREAK_MSG = "Your streak is tracked locally only - sign in to save your stats!";
function showGuestReminder() {
  if (!isGuest) return;
  const banner = document.getElementById("guest-banner");
  document.getElementById("guest-banner-msg").textContent = GUEST_STREAK_MSG;
  const wasHidden = banner.hidden;
  banner.hidden = false;
  banner.classList.remove("guest-banner-pulse");
  if (!wasHidden) {
    void banner.offsetWidth; // restart the pulse animation on repeat triggers
    banner.classList.add("guest-banner-pulse");
  }
}

const DIFF_COLORS = {
  easy: "#859900",
  medium: "#b58900",
  hard: "#cb4b16",
  expert: "#dc322f",
};

// ---------- streak milestones ----------
// Mirrors config.STREAK_MILESTONES/STREAK_MILESTONE_BONUS on the backend -
// purely for display (icon/label/next-badge preview); the server is always
// the source of truth for which are actually earned (stats.badges).
const STREAK_MILESTONES = [
  { at: 3, icon: "🔥", label: "3-Day Streak" },
  { at: 7, icon: "🔥", label: "7-Day Streak" },
  { at: 14, icon: "⚡", label: "14-Day Streak" },
  { at: 30, icon: "🌟", label: "30-Day Streak" },
  { at: 60, icon: "🌟", label: "60-Day Streak" },
  { at: 100, icon: "🏆", label: "100-Day Streak" },
  { at: 200, icon: "🏆", label: "200-Day Streak" },
  { at: 365, icon: "👑", label: "365-Day Streak" },
];

function renderBadges(earnedMilestones) {
  const container = document.getElementById("badges-row");
  container.innerHTML = "";
  const earned = new Set(earnedMilestones);
  let nextLockedShown = false;
  STREAK_MILESTONES.forEach(({ at, icon, label }) => {
    const isEarned = earned.has(at);
    // show every earned badge, plus just the single next one up (locked, as
    // a preview of what's coming) - not every remaining locked tier, to
    // avoid a wall of 8 pills for a fresh user.
    if (!isEarned) {
      if (nextLockedShown) return;
      nextLockedShown = true;
    }
    const pill = document.createElement("span");
    pill.className = "milestone-badge" + (isEarned ? "" : " locked");
    pill.textContent = `${icon} ${label}`;
    container.appendChild(pill);
  });
}

let milestoneToastTimer = null;
function celebrateMilestones(milestones) {
  if (!milestones || milestones.length === 0) return;
  const highest = Math.max(...milestones);
  const meta = STREAK_MILESTONES.find((m) => m.at === highest) || { icon: "🔥", label: `${highest}-Day Streak` };

  const toast = document.getElementById("milestone-toast");
  document.getElementById("milestone-toast-icon").textContent = meta.icon;
  document.getElementById("milestone-toast-title").textContent = `New badge: ${meta.label}!`;
  document.getElementById("milestone-toast-sub").textContent = "Bonus points added - keep it going.";

  clearTimeout(milestoneToastTimer);
  toast.hidden = false;
  toast.classList.remove("milestone-toast-out");
  // restart the pop-in animation even if a toast is already showing
  void toast.offsetWidth;
  toast.style.animation = "none";
  void toast.offsetWidth;
  toast.style.animation = "";

  milestoneToastTimer = setTimeout(() => {
    toast.classList.add("milestone-toast-out");
    setTimeout(() => { toast.hidden = true; }, 300);
  }, 3200);
}

const MASCOT_MSG = {
  quiz: "Warm up with a quick quiz.",
  "code-review": "Spot what's wrong with this snippet.",
  "critical-reasoning": "Spot the flaw in this reasoning.",
  concept: "Explain it back in your own words.",
};

// ---------- fetch helpers ----------
async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
  return res.json();
}
async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error((await res.json()).detail || res.statusText);
  return res.json();
}

function setMascot(text) {
  document.getElementById("mascot-msg").textContent = text;
}

// pad2 is defined further down (function declarations are hoisted, so it's
// available here too) alongside dateKey(y, m, d) - dateKeyFromDate is the
// same idea but takes a Date object directly, which Progress needs more often.
function dateKeyFromDate(d) { return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`; }
// A guest's "today" is computed in the browser's own timezone, unlike a
// signed-in day which always trusts the server's date.today() uncritically -
// if the two disagree near midnight a guest could see a different day's
// content than a signed-in user would at that exact moment. Not new: this
// app has never reconciled timezones anywhere, this is just the first place
// the client makes its own "what day is it" call instead of the server.
function todayLocalISO() { return dateKeyFromDate(new Date()); }
function round1(x) { return Math.round(x * 10) / 10; }

// ---------- Progress: the guest-vs-signed-in seam ----------
// The single place isGuest gets branched on. Every render/handler function
// below calls only Progress.* and addresses days by (track, date) - never
// current.day.id, which doesn't exist for a guest's virtual (unpersisted)
// day. For signed-in accounts Progress is a thin pass-through to the real
// API (addressed internally via a small track|date -> Day id cache, since
// the real endpoints are id-addressed); for guests it hits the stateless
// /api/guest/* endpoints and keeps all progress in localStorage, submitting
// it via /api/claim once the guest signs in for real (see maybeClaim).
const Progress = (() => {
  const STORAGE_KEY = "dailyptr-guest-progress";
  const dayIds = {}; // "track|date" -> real Day id (signed-in accounts only)

  function dayKey(track, date) { return `${track}|${date}`; }

  function defaultState() {
    return { version: 1, onboarded: false, subscriptions: {}, days: {} };
  }
  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? { ...defaultState(), ...JSON.parse(raw) } : defaultState();
    } catch {
      return defaultState();
    }
  }
  function save(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function reviewKindFor(track) {
    const t = tracks.find((tt) => tt.id === track);
    return t ? t.review_kind : "code";
  }
  function multiplierFor(difficulty) {
    return appConfig.scoring.difficulty_multipliers[difficulty];
  }
  function isFullyCompleted(record, reviewKind) {
    const reviewDone = reviewKind === "code" ? record.code_review_completed : record.critical_reasoning_completed;
    return record.quiz_completed && reviewDone && record.concept_completed;
  }
  function isBonus(record, subscribedAt) {
    return !!subscribedAt && record.date < subscribedAt;
  }
  function isLate(record, fullyCompleted, subscribedAt) {
    if (isBonus(record, subscribedAt)) return false;
    if (!record.completed_at) return record.date < todayLocalISO() && !fullyCompleted;
    return record.completed_at.slice(0, 10) > record.date;
  }
  // Mirrors scoring.maybe_award_completion_bonus's on-time-bonus half only -
  // milestone/badge checking needs persisted streak history to check
  // against, which a guest doesn't have, so badges stay suppressed
  // client-side (getStats always returns badges: []) until a real sign-in
  // claims the history server-side.
  function maybeCompleteDay(record, track) {
    const fullyCompleted = isFullyCompleted(record, reviewKindFor(track));
    if (fullyCompleted && !record.completed_at) {
      record.completed_at = new Date().toISOString();
      if (record.date === todayLocalISO()) {
        record.points_earned += round1(appConfig.scoring.on_time_bonus * multiplierFor(record.difficulty));
      }
    }
  }
  function addDays(dateStr, n) {
    const d = new Date(dateStr + "T00:00:00");
    d.setDate(d.getDate() + n);
    return dateKeyFromDate(d);
  }
  // Port of scoring._streaks - same two-pass algorithm (walk back from
  // today for the current streak, scan sorted dates for the longest run).
  function streaks(completedDates) {
    const today = todayLocalISO();
    let current = 0;
    let cursor = completedDates.has(today) ? today : addDays(today, -1);
    while (completedDates.has(cursor)) {
      current++;
      cursor = addDays(cursor, -1);
    }
    const sorted = Array.from(completedDates).sort();
    let longest = 0, run = 0, prev = null;
    for (const d of sorted) {
      run = (prev !== null && d === addDays(prev, 1)) ? run + 1 : 1;
      longest = Math.max(longest, run);
      prev = d;
    }
    return { current, longest };
  }

  function ensureDayRecord(state, track, date, content) {
    const key = dayKey(track, date);
    if (!state.days[key]) {
      state.days[key] = {
        track, date,
        weekday: content.day.weekday, difficulty: content.day.difficulty,
        quiz_question_ids: content.quiz.map((q) => q.id),
        quiz_answers: {}, quiz_correct_indices: {},
        quiz_completed: false, quiz_correct: 0, quiz_total: 0,
        code_review_matches: null, code_review_completed: false, code_review_correct: 0, code_review_total: 0,
        critical_reasoning_matches: null, critical_reasoning_completed: false, critical_reasoning_correct: 0, critical_reasoning_total: 0,
        concept_self_rating: null, concept_completed: false,
        points_earned: 0, completed_at: null,
      };
    }
    return state.days[key];
  }

  function dayOutFromRecord(record, track) {
    const state = load();
    const subscribedAt = state.subscriptions[track] || null;
    const reviewKind = reviewKindFor(track);
    const fullyCompleted = isFullyCompleted(record, reviewKind);
    return {
      date: record.date, track, weekday: record.weekday, difficulty: record.difficulty,
      quiz_completed: record.quiz_completed, quiz_correct: record.quiz_correct, quiz_total: record.quiz_total,
      code_review_completed: record.code_review_completed, code_review_correct: record.code_review_correct, code_review_total: record.code_review_total,
      critical_reasoning_completed: record.critical_reasoning_completed, critical_reasoning_correct: record.critical_reasoning_correct, critical_reasoning_total: record.critical_reasoning_total,
      concept_completed: record.concept_completed, concept_self_rating: record.concept_self_rating,
      points_earned: round1(record.points_earned), completed_at: record.completed_at,
      fully_completed: fullyCompleted,
      is_late: isLate(record, fullyCompleted, subscribedAt),
      is_bonus: isBonus(record, subscribedAt),
    };
  }

  async function getChallenge(track, date) {
    if (!isGuest) {
      const challenge = await getJSON(`${API}/day/${date}?track=${encodeURIComponent(track)}`);
      dayIds[dayKey(track, date)] = challenge.day.id;
      return challenge;
    }
    const content = await getJSON(`${API}/guest/challenge?date=${date}&track=${encodeURIComponent(track)}`);
    const state = load();
    const record = ensureDayRecord(state, track, date, content);
    save(state);
    return {
      day: dayOutFromRecord(record, track),
      quiz: content.quiz,
      code_review: content.code_review,
      critical_reasoning: content.critical_reasoning,
      concept: content.concept,
    };
  }

  async function answerQuiz(track, date, questionId, choiceIndex) {
    if (!isGuest) {
      const dayId = dayIds[dayKey(track, date)];
      return postJSON(`${API}/quiz/${dayId}/question/${questionId}/answer`, { choice_index: choiceIndex });
    }
    const result = await postJSON(`${API}/guest/quiz/answer`, { date, track, question_id: questionId, choice_index: choiceIndex });
    const state = load();
    const record = state.days[dayKey(track, date)];
    record.quiz_answers[String(questionId)] = choiceIndex;
    record.quiz_correct_indices[String(questionId)] = result.correct_index;

    let pointsAwarded = 0;
    const allAnswered = record.quiz_question_ids.every((qid) => String(qid) in record.quiz_answers);
    if (allAnswered && !record.quiz_completed) {
      const correct = record.quiz_question_ids.filter(
        (qid) => record.quiz_answers[String(qid)] === record.quiz_correct_indices[String(qid)]
      ).length;
      record.quiz_completed = true;
      record.quiz_correct = correct;
      record.quiz_total = record.quiz_question_ids.length;
      pointsAwarded = round1(appConfig.scoring.base_quiz * correct * multiplierFor(record.difficulty));
      record.points_earned += pointsAwarded;
      maybeCompleteDay(record, track);
    }
    save(state);

    return {
      correct: result.correct,
      correct_index: result.correct_index,
      explanation: result.explanation,
      quiz_completed: record.quiz_completed,
      quiz_correct: record.quiz_correct,
      quiz_total: record.quiz_total,
      points_awarded: pointsAwarded,
      milestones_hit: [],
    };
  }

  async function submitReview(track, date, kind, matches) {
    const cfg = REVIEW_KIND_CONFIG[kind];
    if (!isGuest) {
      const dayId = dayIds[dayKey(track, date)];
      return postJSON(`${API}/${cfg.endpoint}/${dayId}/submit`, { matches });
    }
    const result = await postJSON(`${API}/guest/${cfg.endpoint}/check`, { date, track, matches });
    const state = load();
    const record = state.days[dayKey(track, date)];
    record[cfg.matchesField] = matches;
    record[cfg.completedField] = true;
    record[cfg.correctField] = result.correct_count;
    record[cfg.totalField] = result.total;
    record.points_earned += result.points_awarded;
    maybeCompleteDay(record, track);
    save(state);
    return { ...result, milestones_hit: [] };
  }

  async function submitConcept(track, date, selfRating) {
    if (!isGuest) {
      const dayId = dayIds[dayKey(track, date)];
      return postJSON(`${API}/concept/${dayId}/submit`, { self_rating_correct: selfRating });
    }
    const result = await postJSON(`${API}/guest/concept/score`, { date, track, self_rating_correct: selfRating });
    const state = load();
    const record = state.days[dayKey(track, date)];
    if (!record.concept_completed) {
      record.concept_self_rating = selfRating;
      record.concept_completed = true;
      record.points_earned += result.points_awarded;
      maybeCompleteDay(record, track);
    }
    save(state);
    return { model_answer: current.concept.model_answer, points_awarded: result.points_awarded, milestones_hit: [] };
  }

  async function resetDay(track, date) {
    if (!isGuest) {
      const dayId = dayIds[dayKey(track, date)];
      return postJSON(`${API}/day/${dayId}/reset`, {});
    }
    const state = load();
    delete state.days[dayKey(track, date)];
    save(state);
    return getChallenge(track, date);
  }

  async function getHistory(track) {
    if (!isGuest) return getJSON(`${API}/history?track=${encodeURIComponent(track)}`);
    const state = load();
    return Object.values(state.days)
      .filter((r) => r.track === track)
      .map((r) => dayOutFromRecord(r, track))
      .sort((a, b) => (a.date < b.date ? 1 : -1));
  }

  async function getStats(track) {
    if (!isGuest) return getJSON(`${API}/stats?track=${encodeURIComponent(track)}`);
    const state = load();
    const subscribedAt = state.subscriptions[track] || null;
    const records = Object.values(state.days).filter((r) => r.track === track);
    const reviewKind = reviewKindFor(track);
    const completedDates = new Set(records.filter((r) => isFullyCompleted(r, reviewKind)).map((r) => r.date));
    const today = todayLocalISO();
    const daysMissedOpen = records.filter(
      (r) => subscribedAt && r.date >= subscribedAt && r.date < today && !isFullyCompleted(r, reviewKind)
    ).length;
    const { current: currentStreak, longest: longestStreak } = streaks(completedDates);
    return {
      total_points: round1(records.reduce((sum, r) => sum + r.points_earned, 0)),
      current_streak: currentStreak,
      longest_streak: longestStreak,
      days_completed: completedDates.size,
      days_missed_open: daysMissedOpen,
      badges: [],
    };
  }

  function isOnboarded(meOnboarded) {
    return isGuest ? load().onboarded : meOnboarded;
  }

  async function onboard(trackIds) {
    if (!isGuest) return postJSON(`${API}/onboarding`, { tracks: trackIds });
    const state = load();
    const today = todayLocalISO();
    trackIds.forEach((t) => { if (!state.subscriptions[t]) state.subscriptions[t] = today; });
    state.onboarded = true;
    save(state);
    return getTracks(tracks);
  }

  async function subscribe(trackId) {
    if (!isGuest) return postJSON(`${API}/subscribe`, { track: trackId });
    const state = load();
    if (!state.subscriptions[trackId]) state.subscriptions[trackId] = todayLocalISO();
    save(state);
    return getTracks(tracks);
  }

  function getTracks(rawTracks) {
    if (!isGuest) return rawTracks;
    const state = load();
    return rawTracks.map((t) => ({ ...t, subscribed: t.id in state.subscriptions }));
  }

  // Called once at boot for a real (non-guest) session - replays whatever
  // this browser accumulated as a guest into the now-signed-in account (see
  // routers/claim.py). Idempotent and safe to retry: errors are left to
  // propagate to init()'s own try/catch rather than swallowed here, so a
  // failed claim just gets retried on next boot instead of silently losing
  // the local data (only cleared from localStorage after a confirmed 200).
  async function maybeClaim() {
    const state = load();
    const dayEntries = Object.values(state.days);
    const subEntries = Object.entries(state.subscriptions);
    if (dayEntries.length === 0 && subEntries.length === 0) return;

    await postJSON(`${API}/claim`, {
      subscriptions: subEntries.map(([track, subscribed_at]) => ({ track, subscribed_at })),
      days: dayEntries.map((r) => ({
        track: r.track,
        date: r.date,
        quiz_answers: r.quiz_answers,
        code_review_matches: r.code_review_matches,
        critical_reasoning_matches: r.critical_reasoning_matches,
        concept_self_rating: r.concept_self_rating,
      })),
    });
    localStorage.removeItem(STORAGE_KEY);
  }

  return {
    isOnboarded, onboard, subscribe, getTracks,
    getChallenge, answerQuiz, submitReview, submitConcept, resetDay,
    getHistory, getStats,
    maybeClaim,
  };
})();

// ---------- onboarding (first-login topic selection) ----------
let onboardingPicks = new Set();

function renderOnboardingTopics(allTracks) {
  onboardingPicks = new Set();
  const grid = document.getElementById("onboarding-topics");
  grid.innerHTML = "";
  allTracks.forEach((t) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "topic-card";
    btn.innerHTML = `
      <span class="topic-card-check">
        <svg width="14" height="14" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" fill="none" stroke="var(--bg)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </span>
      <span class="topic-card-name">${t.name}</span>
    `;
    btn.addEventListener("click", () => {
      if (onboardingPicks.has(t.id)) onboardingPicks.delete(t.id);
      else onboardingPicks.add(t.id);
      btn.classList.toggle("selected", onboardingPicks.has(t.id));
      document.getElementById("onboarding-start").disabled = onboardingPicks.size === 0;
    });
    grid.appendChild(btn);
  });
}

document.getElementById("onboarding-start").addEventListener("click", async () => {
  const btn = document.getElementById("onboarding-start");
  btn.disabled = true;
  btn.textContent = "Setting things up…";
  try {
    tracks = await Progress.onboard(Array.from(onboardingPicks));
    currentTrack = tracks.find((t) => t.subscribed)?.id || tracks[0]?.id;
    localStorage.setItem("cdr-track", currentTrack);
    document.getElementById("onboarding-view").hidden = true;
    document.getElementById("app-view").hidden = false;
    renderTrackSwitcher();
    await loadToday();
    showGuestReminder();
  } catch (e) {
    alert(`Couldn't save your topics: ${e.message}`);
    btn.disabled = false;
    btn.textContent = "Start";
  }
});

// ---------- track switcher ----------
function renderTrackSwitcher() {
  const nav = document.getElementById("track-switcher");
  nav.innerHTML = "";
  const subscribed = tracks.filter((t) => t.subscribed);
  subscribed.forEach((t) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "track-pill" + (t.id === currentTrack ? " active" : "");
    btn.textContent = t.name;
    btn.addEventListener("click", () => switchTrack(t.id));
    nav.appendChild(btn);
  });

  const unsubscribed = tracks.filter((t) => !t.subscribed);
  document.getElementById("add-topic-popover").hidden = true;
  if (unsubscribed.length === 0) return;
  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = "track-pill track-pill-add";
  addBtn.textContent = "+ Add topic";
  addBtn.addEventListener("click", () => renderAddTopicPopover(unsubscribed));
  nav.appendChild(addBtn);
}

function renderAddTopicPopover(unsubscribed) {
  const pop = document.getElementById("add-topic-popover");
  if (!pop.hidden) { pop.hidden = true; return; }
  pop.innerHTML = '<p class="hint">Add a topic to your rotation:</p>';
  unsubscribed.forEach((t) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "topic-chip";
    btn.textContent = t.name;
    btn.addEventListener("click", async () => {
      try {
        tracks = await Progress.subscribe(t.id);
        pop.hidden = true;
        await switchTrack(t.id);
      } catch (e) {
        alert(`Couldn't add topic: ${e.message}`);
      }
    });
    pop.appendChild(btn);
  });
  pop.hidden = false;
}

async function switchTrack(trackId) {
  if (trackId === currentTrack) return;
  currentTrack = trackId;
  localStorage.setItem("cdr-track", trackId);
  renderTrackSwitcher();
  showView("challenge-view");
  await loadToday();
}

async function loadToday() {
  await refreshStats();
  const today = await Progress.getChallenge(currentTrack, todayLocalISO());
  renderChallenge(today);
}

// ---------- stats ----------
async function refreshStats() {
  const stats = await Progress.getStats(currentTrack);
  document.getElementById("stat-points").textContent = stats.total_points;
  document.getElementById("stat-streak").textContent = stats.current_streak;
  const missedWrap = document.getElementById("stat-missed-wrap");
  if (stats.days_missed_open > 0) {
    missedWrap.hidden = false;
    document.getElementById("stat-missed").textContent = stats.days_missed_open;
  } else {
    missedWrap.hidden = true;
  }
  renderBadges(stats.badges);
}

// ---------- challenge rendering ----------
function difficultyBadgeClass(d) {
  return `badge badge-${d}`;
}

function renderChallenge(challenge) {
  current = challenge;
  const { day, quiz, code_review, critical_reasoning, concept } = challenge;
  // Exactly one of code_review/critical_reasoning is populated, per the
  // day's track's review_kind (see config.TRACKS on the backend).
  const reviewKind = code_review ? "code" : "reasoning";

  const badge = document.getElementById("challenge-badge");
  badge.textContent = `${day.difficulty} · ${day.date}`;
  badge.className = difficultyBadgeClass(day.difficulty);
  document.getElementById("blob-diff").style.background =
    `radial-gradient(circle, ${DIFF_COLORS[day.difficulty] || DIFF_COLORS.medium} 0%, transparent 70%)`;

  document.getElementById("challenge-late").hidden = !day.is_late;
  document.getElementById("challenge-bonus").hidden = !day.is_bonus;

  // Only the tab matching this track's review kind is shown - a track never
  // has both Code Review and Critical Reasoning content at once.
  document.querySelector('.node-btn[data-tab="code-review"]').hidden = reviewKind !== "code";
  document.querySelector('.node-btn[data-tab="critical-reasoning"]').hidden = reviewKind !== "reasoning";
  if (currentTab === "code-review" || currentTab === "critical-reasoning") {
    currentTab = reviewKind === "code" ? "code-review" : "critical-reasoning";
  }

  renderNodes(day, reviewKind);
  renderQuiz(quiz, day);
  renderReviewChallenge(reviewKind, reviewKind === "code" ? code_review : critical_reasoning, day);
  renderConcept(concept, day);

  showView("challenge-view");
  showTab(currentTab || "quiz");
}

document.getElementById("reset-day-btn").addEventListener("click", async () => {
  if (!confirm("Reset today's progress? You'll lose the points earned today and can try the same quiz/code review/concept check again.")) return;
  try {
    const fresh = await Progress.resetDay(currentTrack, current.day.date);
    renderChallenge(fresh);
    await refreshStats();
    setMascot("Fresh start - let's go again.");
  } catch (e) {
    alert(`Couldn't reset: ${e.message}`);
  }
});

function renderNodes(day, reviewKind) {
  const nodeState = (nodeId, done, isCurrent) => {
    const el = document.getElementById(nodeId);
    el.classList.toggle("done", done);
    el.classList.toggle("current", isCurrent && !done);
    if (isCurrent && !done) {
      el.style.background = DIFF_COLORS[day.difficulty] || DIFF_COLORS.medium;
    } else if (!done) {
      el.style.background = "";
    }
  };
  nodeState("node-quiz", day.quiz_completed, currentTab === "quiz");
  if (reviewKind === "code") {
    nodeState("node-code-review", day.code_review_completed, currentTab === "code-review");
  } else {
    nodeState("node-critical-reasoning", day.critical_reasoning_completed, currentTab === "critical-reasoning");
  }
  nodeState("node-concept", day.concept_completed, currentTab === "concept");
}

// ---------- quiz ----------
function renderQuiz(quiz, day) {
  const container = document.getElementById("quiz-questions");
  container.innerHTML = "";
  quiz.forEach((q, idx) => {
    const div = document.createElement("div");
    div.className = "question";
    const p = document.createElement("p");
    p.className = "q-text";
    p.textContent = `${idx + 1}. ${q.question}`;
    div.appendChild(p);
    q.choices.forEach((choice, ci) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "choice";
      btn.dataset.qid = q.id;
      btn.dataset.ci = ci;
      btn.textContent = choice;
      if (day.quiz_completed) btn.classList.add("locked");
      btn.addEventListener("click", () => submitQuizAnswer(q, ci, div));
      div.appendChild(btn);
    });
    const explain = document.createElement("p");
    explain.className = "q-explain";
    explain.hidden = true;
    div.appendChild(explain);
    container.appendChild(div);
  });

  const resultBox = document.getElementById("quiz-result");
  resultBox.hidden = true;
  if (day.quiz_completed) {
    resultBox.hidden = false;
    resultBox.textContent = `Already completed: ${day.quiz_correct}/${day.quiz_total} correct.`;
  }
}

async function submitQuizAnswer(q, ci, div) {
  const choiceBtns = div.querySelectorAll(".choice");
  if (current.day.quiz_completed || [...choiceBtns].some((b) => b.disabled)) return;
  choiceBtns.forEach((b) => (b.disabled = true));
  try {
    const result = await Progress.answerQuiz(currentTrack, current.day.date, q.id, ci);
    choiceBtns.forEach((b) => b.classList.remove("correct", "incorrect"));
    const chosenBtn = div.querySelector(`.choice[data-ci="${ci}"]`);
    chosenBtn.classList.add(result.correct ? "correct" : "incorrect");
    if (!result.correct) {
      const correctBtn = div.querySelector(`.choice[data-ci="${result.correct_index}"]`);
      if (correctBtn) correctBtn.classList.add("correct");
    }
    const explain = div.querySelector(".q-explain");
    explain.textContent = result.explanation;
    explain.hidden = false;

    current.day.quiz_completed = result.quiz_completed;
    current.day.quiz_correct = result.quiz_correct;
    current.day.quiz_total = result.quiz_total;

    if (result.quiz_completed) {
      document.querySelectorAll("#quiz-questions .choice").forEach((b) => b.classList.add("locked"));
      const resultBox = document.getElementById("quiz-result");
      resultBox.hidden = false;
      resultBox.textContent = `${result.quiz_correct}/${result.quiz_total} correct - +${result.points_awarded} pts`;
      setMascot(result.quiz_correct === result.quiz_total ? "Perfect score! Let's keep moving." : `${result.quiz_correct}/${result.quiz_total} - nice, on to the next one.`);
      celebrateMilestones(result.milestones_hit);
      await afterComponentComplete();
    }
  } catch (e) {
    alert(`Couldn't submit answer: ${e.message}`);
  } finally {
    if (!current.day.quiz_completed) choiceBtns.forEach((b) => (b.disabled = false));
  }
}

// ---------- code review ----------
// crState: interactive click-a-line / tap-a-reason matching state for the
// review challenge (Code Review or Critical Reasoning - only one is ever on
// screen for a given track, see REVIEW_KIND_CONFIG) currently on screen.
// kind: which of the two this state belongs to, so handlers re-render the
// right panel/re-derive the right text. flagged: ordered array of line
// numbers (max MAX_CR_FLAGS). reasons: {line -> reason text} for lines
// matched to a reason so far. active: the flagged line waiting for a reason
// tap (or null).
const MAX_CR_FLAGS = 3;
let crState = { kind: "code", flagged: [], reasons: {}, active: null, bank: [], locked: false };

// The two review kinds share identical interaction/grading logic, differing
// only in which DOM ids/endpoint/Day fields/text field they touch - see
// routers/code_review.py vs routers/critical_reasoning.py on the backend for
// the same shape mirrored server-side.
const REVIEW_KIND_CONFIG = {
  code: {
    elPrefix: "code-review",
    endpoint: "code-review",
    textField: "snippet",
    matchesField: "code_review_matches",
    completedField: "code_review_completed",
    correctField: "code_review_correct",
    totalField: "code_review_total",
    verb: "bug or smell",
  },
  reasoning: {
    elPrefix: "critical-reasoning",
    endpoint: "critical-reasoning",
    textField: "passage",
    matchesField: "critical_reasoning_matches",
    completedField: "critical_reasoning_completed",
    correctField: "critical_reasoning_correct",
    totalField: "critical_reasoning_total",
    verb: "flaw in the reasoning",
  },
};

function renderReviewChallenge(kind, challenge, day) {
  const cfg = REVIEW_KIND_CONFIG[kind];
  const completed = day[cfg.completedField];
  document.getElementById(`${cfg.elPrefix}-title`).textContent = challenge.title;
  crState = { kind, flagged: [], reasons: {}, active: null, bank: challenge.reason_bank.map((reason) => ({ reason, used: false })), locked: completed };

  const resultBox = document.getElementById(`${cfg.elPrefix}-result`);
  resultBox.hidden = true;
  document.getElementById(`${cfg.elPrefix}-submit`).hidden = completed;
  document.getElementById(`${cfg.elPrefix}-bank-hint`).hidden = completed;
  document.getElementById(`${cfg.elPrefix}-hint`).textContent = completed
    ? "Already completed."
    : `Click the line(s) with a ${cfg.verb} (up to ${MAX_CR_FLAGS}), then tap a reason below to match it.`;

  renderCrSnippet(kind, challenge[cfg.textField]);
  renderCrBank(kind);

  if (completed) {
    resultBox.hidden = false;
    resultBox.textContent = `Already completed: ${day[cfg.correctField]}/${day[cfg.totalField]} matched correctly.`;
  }
}

function renderCrSnippet(kind, text) {
  const cfg = REVIEW_KIND_CONFIG[kind];
  const container = document.getElementById(`${cfg.elPrefix}-snippet`);
  container.innerHTML = "";
  text.split("\n").forEach((textLine, idx) => {
    const lineNum = idx + 1;
    const row = document.createElement("div");
    row.className = "cr-line";
    row.dataset.line = lineNum;
    if (crState.locked) row.classList.add("locked");
    if (crState.flagged.includes(lineNum)) row.classList.add("flagged");
    if (crState.reasons[lineNum]) row.classList.add("matched");
    if (crState.active === lineNum) row.classList.add("active");

    const num = document.createElement("span");
    num.className = "cr-line-num";
    num.textContent = lineNum;
    row.appendChild(num);

    const code = document.createElement("span");
    code.className = "cr-line-code";
    code.textContent = textLine;
    row.appendChild(code);

    if (crState.reasons[lineNum]) {
      const chip = document.createElement("span");
      chip.className = "cr-line-chip";
      chip.textContent = crState.reasons[lineNum];
      row.appendChild(chip);
    }

    row.addEventListener("click", () => onCrLineClick(lineNum));
    container.appendChild(row);
  });
}

function currentReviewChallenge() {
  return crState.kind === "code" ? current.code_review : current.critical_reasoning;
}

function onCrLineClick(line) {
  if (crState.locked) return;
  const isFlagged = crState.flagged.includes(line);
  if (!isFlagged) {
    if (crState.flagged.length >= MAX_CR_FLAGS) return;
    crState.flagged.push(line);
    crState.active = line;
  } else if (crState.active !== line) {
    crState.active = line;
  } else {
    // clicking the active flagged line again removes it, returning its
    // reason chip (if any) to the bank
    crState.flagged = crState.flagged.filter((l) => l !== line);
    const freedReason = crState.reasons[line];
    delete crState.reasons[line];
    crState.active = null;
    if (freedReason) {
      const chip = crState.bank.find((b) => b.reason === freedReason && b.used);
      if (chip) chip.used = false;
    }
  }
  const cfg = REVIEW_KIND_CONFIG[crState.kind];
  renderCrSnippet(crState.kind, currentReviewChallenge()[cfg.textField]);
  renderCrBank(crState.kind);
}

function onCrChipClick(reason) {
  if (crState.locked || crState.active === null) return;
  const chip = crState.bank.find((b) => b.reason === reason && !b.used);
  if (!chip) return;

  const line = crState.active;
  const prevReason = crState.reasons[line];
  if (prevReason) {
    const prevChip = crState.bank.find((b) => b.reason === prevReason && b.used);
    if (prevChip) prevChip.used = false;
  }
  chip.used = true;
  crState.reasons[line] = reason;

  // auto-advance to the next flagged line still waiting on a reason
  crState.active = crState.flagged.find((l) => !crState.reasons[l]) ?? null;

  const cfg = REVIEW_KIND_CONFIG[crState.kind];
  renderCrSnippet(crState.kind, currentReviewChallenge()[cfg.textField]);
  renderCrBank(crState.kind);
}

function renderCrBank(kind) {
  const cfg = REVIEW_KIND_CONFIG[kind];
  const container = document.getElementById(`${cfg.elPrefix}-reason-bank`);
  container.innerHTML = "";
  crState.bank.forEach(({ reason, used }) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "reason-chip";
    btn.textContent = reason;
    btn.disabled = crState.locked || used || crState.active === null;
    btn.addEventListener("click", () => onCrChipClick(reason));
    container.appendChild(btn);
  });
  const bankHint = document.getElementById(`${cfg.elPrefix}-bank-hint`);
  bankHint.classList.toggle("dim", crState.active === null);
}

async function submitReview(kind) {
  const cfg = REVIEW_KIND_CONFIG[kind];
  if (crState.flagged.length === 0) {
    alert("Flag at least one line first.");
    return;
  }
  const matches = crState.flagged.filter((line) => crState.reasons[line]).map((line) => ({ line, reason: crState.reasons[line] }));
  try {
    const result = await Progress.submitReview(currentTrack, current.day.date, kind, matches);
    current.day[cfg.completedField] = true;
    current.day[cfg.correctField] = result.correct_count;
    current.day[cfg.totalField] = result.total;
    crState.locked = true;

    // color each flagged line by whether it fully matched, and show every
    // real issue's explanation (including ones the user never flagged)
    const container = document.getElementById(`${cfg.elPrefix}-snippet`);
    const byLine = {};
    result.results.forEach((r) => { byLine[r.line] = r; });
    container.querySelectorAll(".cr-line").forEach((row) => {
      row.classList.add("locked");
      const line = Number(row.dataset.line);
      const r = byLine[line];
      if (!r) return;
      row.classList.add(r.line_found && r.reason_correct ? "result-hit" : "result-miss");
      row.querySelectorAll(".cr-line-chip").forEach((el) => el.remove());
      const chip = document.createElement("span");
      chip.className = "cr-line-chip" + (r.line_found && r.reason_correct ? "" : " wrong");
      chip.textContent = r.reason;
      row.appendChild(chip);
    });
    document.getElementById(`${cfg.elPrefix}-submit`).hidden = true;
    document.getElementById(`${cfg.elPrefix}-bank-hint`).hidden = true;
    document.getElementById(`${cfg.elPrefix}-reason-bank`).innerHTML = "";
    document.getElementById(`${cfg.elPrefix}-hint`).textContent = "Already completed.";

    const resultBox = document.getElementById(`${cfg.elPrefix}-result`);
    resultBox.hidden = false;
    const explainLines = result.results.map((r) => `Line ${r.line}: ${r.reason} - ${r.explanation}`).join("\n\n");
    resultBox.textContent = `${result.correct_count}/${result.total} matched correctly.\n\n${explainLines}` +
      (result.points_awarded > 0 ? `\n\n+${result.points_awarded} pts` : "\n\nNo points this time - it'll come back around on a future day.");
    setMascot(result.correct_count === result.total ? "Nice catch - well spotted." : "Check the breakdown below - it'll come back around.");
    celebrateMilestones(result.milestones_hit);
    await afterComponentComplete();
  } catch (e) {
    alert(`Couldn't submit: ${e.message}`);
  }
}

document.getElementById("code-review-submit").addEventListener("click", () => submitReview("code"));
document.getElementById("critical-reasoning-submit").addEventListener("click", () => submitReview("reasoning"));

// ---------- concept check ----------
function renderConcept(concept, day) {
  document.getElementById("concept-prompt").textContent = concept.prompt;
  document.getElementById("concept-notes").value = "";
  const answerBox = document.getElementById("concept-answer");
  const gradeBox = document.getElementById("concept-grade");
  const resultBox = document.getElementById("concept-result");
  const aiFeedbackBox = document.getElementById("concept-ai-feedback");
  const aiGradeBtn = document.getElementById("concept-ai-grade");
  answerBox.hidden = true;
  answerBox.textContent = concept.model_answer;
  gradeBox.hidden = true;
  resultBox.hidden = true;
  aiFeedbackBox.hidden = true;
  // AI grading needs a Day-backed ConceptCheck lookup - there's no stateless
  // guest equivalent (a deliberate scope decision, not an oversight), so
  // guests get the plain reveal-and-self-rate flow only.
  aiGradeBtn.hidden = day.concept_completed || !appConfig.ai_grading_enabled || isGuest;
  aiGradeBtn.disabled = false;
  aiGradeBtn.textContent = "AI-grade my answer";
  document.getElementById("concept-got-it").classList.remove("btn-suggested");
  document.getElementById("concept-missed").classList.remove("btn-suggested");
  document.getElementById("concept-reveal").hidden = day.concept_completed;
  if (day.concept_completed) {
    resultBox.hidden = false;
    resultBox.textContent = day.concept_self_rating
      ? "Already completed - you marked this as understood."
      : "Already completed - you marked this as missed (no points, but that's fine, it'll come back around).";
  }
}

document.getElementById("concept-reveal").addEventListener("click", () => {
  document.getElementById("concept-answer").hidden = false;
  document.getElementById("concept-grade").hidden = false;
  document.getElementById("concept-reveal").hidden = true;
});

document.getElementById("concept-ai-grade").addEventListener("click", async () => {
  const btn = document.getElementById("concept-ai-grade");
  const notes = document.getElementById("concept-notes").value;
  if (!notes.trim()) {
    alert("Jot down your own answer first, then AI-grade it.");
    return;
  }
  btn.disabled = true;
  btn.textContent = "Grading…";
  try {
    const result = await postJSON(`${API}/concept/${current.day.id}/ai-grade`, { notes });
    const aiFeedbackBox = document.getElementById("concept-ai-feedback");
    aiFeedbackBox.hidden = false;
    document.getElementById("concept-ai-feedback-text").textContent =
      `${result.correct ? "Looks correct" : "Not quite"} - ${result.feedback}`;
    document.getElementById("concept-answer").hidden = false;
    document.getElementById("concept-grade").hidden = false;
    document.getElementById("concept-reveal").hidden = true;
    document.getElementById("concept-got-it").classList.toggle("btn-suggested", result.correct);
    document.getElementById("concept-missed").classList.toggle("btn-suggested", !result.correct);
    setMascot(result.correct ? "That's the idea - well put." : "Close - check the model answer below.");
  } catch (e) {
    alert(`AI grading unavailable: ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = "AI-grade my answer";
  }
});

async function submitConceptGrade(gotIt) {
  try {
    const result = await Progress.submitConcept(currentTrack, current.day.date, gotIt);
    document.getElementById("concept-grade").hidden = true;
    document.getElementById("concept-reveal").hidden = true;
    document.getElementById("concept-ai-grade").hidden = true;
    const resultBox = document.getElementById("concept-result");
    resultBox.hidden = false;
    resultBox.textContent = `Model answer:\n${result.model_answer}` +
      (result.points_awarded > 0 ? `\n\n+${result.points_awarded} pts` : "\n\nNo points this time - it'll come back around on a future day.");
    setMascot(gotIt ? "Logged. See you tomorrow!" : "No worries - it'll come back around.");
    celebrateMilestones(result.milestones_hit);
    await afterComponentComplete();
  } catch (e) {
    alert(`Couldn't submit: ${e.message}`);
  }
}
document.getElementById("concept-got-it").addEventListener("click", () => submitConceptGrade(true));
document.getElementById("concept-missed").addEventListener("click", () => submitConceptGrade(false));

async function afterComponentComplete() {
  await refreshStats();
  // re-pull the day so completion flags / late flag / node checkmarks stay in sync
  const day = current.day;
  const fresh = await Progress.getChallenge(currentTrack, day.date);
  renderNodes(fresh.day);
  current.day = fresh.day;
  showGuestReminder();
}

// ---------- tabs / views ----------
document.querySelectorAll(".node-btn").forEach((btn) => {
  btn.addEventListener("click", () => showTab(btn.dataset.tab));
});
function showTab(name) {
  currentTab = name;
  document.querySelectorAll(".node-btn").forEach((b) => b.classList.toggle("current", b.dataset.tab === name));
  document.getElementById("panel-quiz").hidden = name !== "quiz";
  document.getElementById("panel-code-review").hidden = name !== "code-review";
  document.getElementById("panel-critical-reasoning").hidden = name !== "critical-reasoning";
  document.getElementById("panel-concept").hidden = name !== "concept";
  if (current) renderNodes(current.day, current.code_review ? "code" : "reasoning");
  setMascot(MASCOT_MSG[name] || "");
}

function showView(name) {
  document.getElementById("challenge-view").hidden = name !== "challenge-view";
  document.getElementById("history-view").hidden = name !== "history-view";
  document.getElementById("history-toggle").textContent = name === "history-view" ? "Today" : "History";
}

async function openDay(dateStr) {
  const challenge = await Progress.getChallenge(currentTrack, dateStr);
  renderChallenge(challenge);
}

// ---------- history: list ----------
function renderHistoryList(days) {
  const list = document.getElementById("history-list");
  list.innerHTML = "";
  if (days.length === 0) {
    list.innerHTML = '<p class="hint">No days yet - come back tomorrow, or check today\'s challenge.</p>';
  }
  days.forEach((d, i) => {
    const row = document.createElement("div");
    row.className = "history-row" + (i % 2 === 1 ? " align-right" : "");
    const circleClass = d.fully_completed ? "done" : (d.is_late ? "late" : (d.is_bonus ? "bonus" : ""));
    const icon = d.fully_completed
      ? '<svg width="22" height="22" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" fill="none" stroke="var(--text)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      : d.is_late
        ? '<svg width="18" height="18" viewBox="0 0 24 24"><path d="M12 8v5l3 2" fill="none" stroke="var(--text)" stroke-width="2.5" stroke-linecap="round"/><circle cx="12" cy="12" r="8.5" fill="none" stroke="var(--text)" stroke-width="2.5"/></svg>'
        : "";
    row.innerHTML = `
      <button class="history-circle ${circleClass}">${icon}</button>
      <div class="history-labels">
        <div class="history-label">${d.date}</div>
        <div class="history-meta" style="color:${DIFF_COLORS[d.difficulty] || DIFF_COLORS.medium}">${d.difficulty} · ${d.points_earned} pts</div>
      </div>
    `;
    row.addEventListener("click", () => openDay(d.date));
    list.appendChild(row);
  });
}

// ---------- history: calendar ----------
function pad2(n) { return String(n).padStart(2, "0"); }
function dateKey(y, m, d) { return `${y}-${pad2(m + 1)}-${pad2(d)}`; }

function renderCalendar() {
  const label = document.getElementById("cal-month-label");
  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  label.textContent = `${monthNames[calMonth]} ${calYear}`;

  const grid = document.getElementById("calendar-grid");
  grid.innerHTML = "";

  const firstOfMonth = new Date(calYear, calMonth, 1);
  // Monday-first weekday index (0=Mon..6=Sun)
  const leading = (firstOfMonth.getDay() + 6) % 7;
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
  const todayStr = dateKey(new Date().getFullYear(), new Date().getMonth(), new Date().getDate());

  for (let i = 0; i < leading; i++) {
    const blank = document.createElement("div");
    blank.className = "cal-cell cal-blank";
    grid.appendChild(blank);
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const key = dateKey(calYear, calMonth, d);
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "cal-cell";
    const isFuture = key > todayStr;
    const entry = historyByDate[key];
    if (isFuture) {
      cell.classList.add("cal-future");
      cell.disabled = true;
    } else if (entry) {
      if (entry.fully_completed) cell.classList.add("cal-done");
      else if (entry.is_late) cell.classList.add("cal-late");
      else if (entry.is_bonus) cell.classList.add("cal-bonus");
      else cell.classList.add("cal-open");
    } else {
      cell.classList.add("cal-open");
    }
    if (key === todayStr) cell.classList.add("cal-today");
    cell.textContent = d;
    if (!isFuture) cell.addEventListener("click", () => openDay(key));
    grid.appendChild(cell);
  }
}

document.getElementById("cal-prev").addEventListener("click", () => {
  calMonth--;
  if (calMonth < 0) { calMonth = 11; calYear--; }
  renderCalendar();
});
document.getElementById("cal-next").addEventListener("click", () => {
  calMonth++;
  if (calMonth > 11) { calMonth = 0; calYear++; }
  renderCalendar();
});

document.getElementById("history-view-calendar").addEventListener("click", () => {
  document.getElementById("history-view-calendar").classList.add("active");
  document.getElementById("history-view-list").classList.remove("active");
  document.getElementById("calendar-view").hidden = false;
  document.getElementById("history-list").hidden = true;
});
document.getElementById("history-view-list").addEventListener("click", () => {
  document.getElementById("history-view-list").classList.add("active");
  document.getElementById("history-view-calendar").classList.remove("active");
  document.getElementById("history-list").hidden = false;
  document.getElementById("calendar-view").hidden = true;
});

document.getElementById("logout-form").addEventListener("submit", (e) => {
  if (isGuest) {
    e.preventDefault();
    window.location.href = "auth/google/login";
  }
});

document.getElementById("history-toggle").addEventListener("click", async () => {
  const isHistory = !document.getElementById("history-view").hidden;
  if (isHistory) {
    showView("challenge-view");
    return;
  }
  const days = await Progress.getHistory(currentTrack);
  historyByDate = {};
  days.forEach((d) => { historyByDate[d.date] = d; });
  renderHistoryList(days);
  const now = new Date();
  calYear = now.getFullYear();
  calMonth = now.getMonth();
  renderCalendar();
  showView("history-view");
});

// ---------- boot ----------
(async function init() {
  try {
    appConfig = await getJSON(`${API}/config`);
    const me = await getJSON(`${API}/me`);
    isGuest = me.is_guest;
    if (isGuest) {
      document.getElementById("logout-btn-label").textContent = "Sign in";
      document.getElementById("logout-btn").classList.add("guest-mode");
    } else {
      document.getElementById("me-label").textContent = (me.name || me.email).split(" ")[0];
      document.getElementById("me-wrap").hidden = false;
      // Replays whatever this browser accumulated as a guest into the now-
      // signed-in account, before anything below reads onboarded/subscribed
      // state that a successful claim may have just created.
      await Progress.maybeClaim();
    }
    tracks = Progress.getTracks(await getJSON(`${API}/tracks`));

    if (!Progress.isOnboarded(me.onboarded)) {
      document.getElementById("app-view").hidden = true;
      document.getElementById("onboarding-view").hidden = false;
      renderOnboardingTopics(tracks);
      return;
    }

    if (!tracks.some((t) => t.id === currentTrack && t.subscribed)) {
      currentTrack = tracks.find((t) => t.subscribed)?.id || tracks[0]?.id || "cpp_core";
    }
    renderTrackSwitcher();
    await loadToday();
  } catch (e) {
    setMascot("Couldn't load today's challenge");
    console.error(e);
  }
})();
