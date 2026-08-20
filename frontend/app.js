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
    tracks = await postJSON(`${API}/onboarding`, { tracks: Array.from(onboardingPicks) });
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
        tracks = await postJSON(`${API}/subscribe`, { track: t.id });
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
  const today = await getJSON(`${API}/today?track=${encodeURIComponent(currentTrack)}`);
  renderChallenge(today);
}

// ---------- stats ----------
async function refreshStats() {
  const stats = await getJSON(`${API}/stats?track=${encodeURIComponent(currentTrack)}`);
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
  const { day, quiz, code_review, concept } = challenge;

  const badge = document.getElementById("challenge-badge");
  badge.textContent = `${day.difficulty} · ${day.date}`;
  badge.className = difficultyBadgeClass(day.difficulty);
  document.getElementById("blob-diff").style.background =
    `radial-gradient(circle, ${DIFF_COLORS[day.difficulty] || DIFF_COLORS.medium} 0%, transparent 70%)`;

  document.getElementById("challenge-late").hidden = !day.is_late;
  document.getElementById("challenge-bonus").hidden = !day.is_bonus;

  renderNodes(day);
  renderQuiz(quiz, day);
  renderCodeReview(code_review, day);
  renderConcept(concept, day);

  showView("challenge-view");
  showTab(currentTab || "quiz");
}

document.getElementById("reset-day-btn").addEventListener("click", async () => {
  if (!confirm("Reset today's progress? You'll lose the points earned today and can try the same quiz/code review/concept check again.")) return;
  try {
    const fresh = await postJSON(`${API}/day/${current.day.id}/reset`, {});
    renderChallenge(fresh);
    await refreshStats();
    setMascot("Fresh start - let's go again.");
  } catch (e) {
    alert(`Couldn't reset: ${e.message}`);
  }
});

function renderNodes(day) {
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
  nodeState("node-code-review", day.code_review_completed, currentTab === "code-review");
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
    const result = await postJSON(`${API}/quiz/${current.day.id}/question/${q.id}/answer`, { choice_index: ci });
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
// code review currently on screen. flagged: ordered array of line numbers
// (max MAX_FLAGS). reasons: {line -> reason text} for lines matched to a
// reason so far. active: the flagged line waiting for a reason tap (or null).
const MAX_CR_FLAGS = 3;
let crState = { flagged: [], reasons: {}, active: null, bank: [], locked: false };

function renderCodeReview(challenge, day) {
  document.getElementById("code-review-title").textContent = challenge.title;
  crState = { flagged: [], reasons: {}, active: null, bank: challenge.reason_bank.map((reason) => ({ reason, used: false })), locked: day.code_review_completed };

  const resultBox = document.getElementById("code-review-result");
  resultBox.hidden = true;
  document.getElementById("code-review-submit").hidden = day.code_review_completed;
  document.getElementById("code-review-bank-hint").hidden = day.code_review_completed;
  document.getElementById("code-review-hint").textContent = day.code_review_completed
    ? "Already completed."
    : `Click the line(s) with a bug or smell (up to ${MAX_CR_FLAGS}), then tap a reason below to match it.`;

  renderCrSnippet(challenge.snippet);
  renderCrBank();

  if (day.code_review_completed) {
    resultBox.hidden = false;
    resultBox.textContent = `Already completed: ${day.code_review_correct}/${day.code_review_total} matched correctly.`;
  }
}

function renderCrSnippet(snippet) {
  const container = document.getElementById("code-review-snippet");
  container.innerHTML = "";
  snippet.split("\n").forEach((codeLine, idx) => {
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
    code.textContent = codeLine;
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
  renderCrSnippet(current.code_review.snippet);
  renderCrBank();
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

  renderCrSnippet(current.code_review.snippet);
  renderCrBank();
}

function renderCrBank() {
  const container = document.getElementById("code-review-reason-bank");
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
  const bankHint = document.getElementById("code-review-bank-hint");
  bankHint.classList.toggle("dim", crState.active === null);
}

document.getElementById("code-review-submit").addEventListener("click", async () => {
  if (crState.flagged.length === 0) {
    alert("Flag at least one line first.");
    return;
  }
  const matches = crState.flagged.filter((line) => crState.reasons[line]).map((line) => ({ line, reason: crState.reasons[line] }));
  try {
    const result = await postJSON(`${API}/code-review/${current.day.id}/submit`, { matches });
    current.day.code_review_completed = true;
    current.day.code_review_correct = result.correct_count;
    current.day.code_review_total = result.total;
    crState.locked = true;

    // color each flagged line by whether it fully matched, and show every
    // real issue's explanation (including ones the user never flagged)
    const container = document.getElementById("code-review-snippet");
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
    document.getElementById("code-review-submit").hidden = true;
    document.getElementById("code-review-bank-hint").hidden = true;
    document.getElementById("code-review-reason-bank").innerHTML = "";
    document.getElementById("code-review-hint").textContent = "Already completed.";

    const resultBox = document.getElementById("code-review-result");
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
});

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
  aiGradeBtn.hidden = day.concept_completed || !appConfig.ai_grading_enabled;
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
    const result = await postJSON(`${API}/concept/${current.day.id}/submit`, { self_rating_correct: gotIt });
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
  const fresh = await getJSON(`${API}/day/${day.date}?track=${encodeURIComponent(currentTrack)}`);
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
  document.getElementById("panel-concept").hidden = name !== "concept";
  if (current) renderNodes(current.day);
  setMascot(MASCOT_MSG[name] || "");
}

function showView(name) {
  document.getElementById("challenge-view").hidden = name !== "challenge-view";
  document.getElementById("history-view").hidden = name !== "history-view";
  document.getElementById("history-toggle").textContent = name === "history-view" ? "Today" : "History";
}

async function openDay(dateStr) {
  const challenge = await getJSON(`${API}/day/${dateStr}?track=${encodeURIComponent(currentTrack)}`);
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
  const days = await getJSON(`${API}/history?track=${encodeURIComponent(currentTrack)}`);
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
    }
    tracks = await getJSON(`${API}/tracks`);

    if (!me.onboarded) {
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
