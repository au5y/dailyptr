const API = "/api";
let current = null; // currently loaded ChallengeOut
let appConfig = { ai_grading_enabled: false };
let quizPicks = {}; // qid -> chosen index, client-side only until submit
let tracks = []; // [{id, name, uses_sandbox}]
let currentTrack = localStorage.getItem("cdr-track") || "cpp_core";
let currentTab = "quiz";
let historyByDate = {}; // date string -> DayOut, for the current track (refreshed each time History opens)
let calYear, calMonth; // calendar's currently displayed month (0-based month)

// ---------- block mode (Duolingo-style "assemble the code") ----------
let blockModeEnabled = localStorage.getItem("cdr-block-mode") === "1";
let blockBank = []; // shuffled reference-solution lines not yet placed
let blockAssembly = []; // lines placed, in order
let blocksLoadedForDayId = null;

const DIFF_COLORS = {
  easy: "#859900",
  medium: "#b58900",
  hard: "#cb4b16",
  expert: "#dc322f",
};

const MASCOT_MSG = {
  quiz: "Warm up with a quick quiz.",
  code: "Time to write some real C++.",
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

function currentTrackMeta() {
  return tracks.find((t) => t.id === currentTrack) || { id: currentTrack, name: currentTrack, uses_sandbox: true };
}

// ---------- track switcher ----------
function renderTrackSwitcher() {
  const nav = document.getElementById("track-switcher");
  nav.innerHTML = "";
  tracks.forEach((t) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "track-pill" + (t.id === currentTrack ? " active" : "");
    btn.textContent = t.name;
    btn.addEventListener("click", () => switchTrack(t.id));
    nav.appendChild(btn);
  });
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
}

// ---------- challenge rendering ----------
function difficultyBadgeClass(d) {
  return `badge badge-${d}`;
}

function renderChallenge(challenge) {
  current = challenge;
  quizPicks = {};
  const { day, quiz, coding, concept } = challenge;

  const badge = document.getElementById("challenge-badge");
  badge.textContent = `${day.difficulty} · ${day.date}`;
  badge.className = difficultyBadgeClass(day.difficulty);
  document.getElementById("blob-diff").style.background =
    `radial-gradient(circle, ${DIFF_COLORS[day.difficulty] || DIFF_COLORS.medium} 0%, transparent 70%)`;

  document.getElementById("challenge-late").hidden = !day.is_late;

  renderNodes(day);
  renderQuiz(quiz, day);
  renderCode(coding, day);
  renderConcept(concept, day);

  showView("challenge-view");
  showTab(currentTab || "quiz");
}

document.getElementById("reset-day-btn").addEventListener("click", async () => {
  if (!confirm("Reset today's progress? You'll lose the points earned today and can try the same quiz/code/concept check again.")) return;
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
  nodeState("node-code", day.coding_completed, currentTab === "code");
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
      const dot = document.createElement("span");
      dot.className = "choice-indicator";
      btn.appendChild(dot);
      btn.appendChild(document.createTextNode(choice));
      if (day.quiz_completed) btn.classList.add("locked");
      btn.addEventListener("click", () => {
        if (day.quiz_completed || document.getElementById("quiz-submit").hidden) return;
        quizPicks[q.id] = ci;
        div.querySelectorAll(".choice").forEach((b) => b.classList.remove("selected"));
        btn.classList.add("selected");
      });
      div.appendChild(btn);
    });
    container.appendChild(div);
  });

  const submitBtn = document.getElementById("quiz-submit");
  const resultBox = document.getElementById("quiz-result");
  resultBox.hidden = true;
  submitBtn.hidden = day.quiz_completed;
  if (day.quiz_completed) {
    resultBox.hidden = false;
    resultBox.textContent = `Already completed: ${day.quiz_correct}/${day.quiz_total} correct.`;
  }
}

document.getElementById("quiz-submit").addEventListener("click", async () => {
  try {
    const result = await postJSON(`${API}/quiz/${current.day.id}/submit`, { answers: quizPicks });
    const resultBox = document.getElementById("quiz-result");
    resultBox.hidden = false;
    resultBox.textContent = `${result.correct}/${result.total} correct - +${result.points_awarded} pts\n\n` +
      Object.entries(result.explanations).map(([qid, ex]) => {
        const ok = result.results[qid];
        return `${ok ? "✓" : "✗"} ${ex}`;
      }).join("\n\n");
    document.getElementById("quiz-submit").hidden = true;
    document.querySelectorAll("#quiz-questions .choice").forEach((btn) => {
      btn.classList.add("locked");
      const qid = btn.dataset.qid;
      const ci = parseInt(btn.dataset.ci, 10);
      if (ci === result.correct_indices[qid]) btn.classList.add("correct");
      else if (quizPicks[qid] === ci) btn.classList.add("incorrect");
      btn.classList.remove("selected");
    });
    setMascot(result.correct === result.total ? "Perfect score! Let's keep moving." : `${result.correct}/${result.total} - nice, on to the next one.`);
    await afterComponentComplete();
  } catch (e) {
    alert(`Couldn't submit quiz: ${e.message}`);
  }
});

// ---------- coding ----------
function renderCode(coding, day) {
  document.getElementById("code-title").textContent = coding.title;
  document.getElementById("code-description").textContent = coding.description;
  document.getElementById("code-tests").textContent = `Test cases: ${coding.test_case_summary}`;

  const docsPanel = document.getElementById("code-docs");
  const docsLinks = document.getElementById("code-docs-links");
  docsLinks.innerHTML = "";
  const docs = coding.docs || [];
  docsPanel.hidden = docs.length === 0;
  docs.forEach((d) => {
    const a = document.createElement("a");
    a.href = d.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.className = "docs-link";
    a.textContent = d.label;
    docsLinks.appendChild(a);
  });

  const editor = document.getElementById("code-editor");
  editor.value = coding.starter_code;
  const resultBox = document.getElementById("code-result");
  resultBox.hidden = true;
  resultBox.className = "panel-result";
  document.getElementById("code-reference").hidden = true;

  const usesSandbox = currentTrackMeta().uses_sandbox;
  const submitBtn = document.getElementById("code-submit");
  if (day.coding_completed) {
    submitBtn.textContent = usesSandbox ? "Re-run (already solved, no extra points)" : "Re-submit (already solved, no extra points)";
  } else {
    submitBtn.textContent = usesSandbox ? "Compile & Run" : "Submit & Compare";
  }

  blockBank = [];
  blockAssembly = [];
  blocksLoadedForDayId = null;
  document.getElementById("block-mode-toggle").checked = blockModeEnabled;
  applyBlockModeVisibility();
  if (blockModeEnabled) loadBlocksForCurrentDay();
}

function applyBlockModeVisibility() {
  document.getElementById("code-editor").hidden = blockModeEnabled;
  document.getElementById("code-blocks").hidden = !blockModeEnabled;
}

async function loadBlocksForCurrentDay() {
  if (!current) return;
  const dayId = current.day.id;
  if (blocksLoadedForDayId === dayId) return;
  try {
    const result = await getJSON(`${API}/coding/${dayId}/blocks`);
    blockBank = result.lines;
    blockAssembly = [];
    blocksLoadedForDayId = dayId;
  } catch (e) {
    blockBank = [];
    blockAssembly = [];
  }
  renderBlocks();
}

function renderBlocks() {
  const bank = document.getElementById("blocks-bank");
  const assembly = document.getElementById("blocks-assembly");
  const emptyHint = document.getElementById("blocks-empty-hint");
  bank.innerHTML = "";
  // Only remove previously-rendered chips - #blocks-empty-hint is a static
  // child of #blocks-assembly too, and assembly.innerHTML = "" would wipe it
  // out along with the chips, breaking every render after the first.
  assembly.querySelectorAll(".block-chip").forEach((el) => el.remove());

  blockAssembly.forEach((line, i) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "block-chip in-assembly";
    chip.textContent = line;
    chip.title = "Tap to send back to the pile";
    chip.addEventListener("click", () => {
      blockAssembly.splice(i, 1);
      blockBank.push(line);
      renderBlocks();
    });
    assembly.appendChild(chip);
  });
  emptyHint.hidden = blockAssembly.length > 0;

  blockBank.forEach((line, i) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "block-chip";
    chip.textContent = line;
    chip.title = "Tap to add to your solution";
    chip.addEventListener("click", () => {
      blockBank.splice(i, 1);
      blockAssembly.push(line);
      renderBlocks();
    });
    bank.appendChild(chip);
  });
}

document.getElementById("block-mode-toggle").addEventListener("change", (e) => {
  blockModeEnabled = e.target.checked;
  localStorage.setItem("cdr-block-mode", blockModeEnabled ? "1" : "0");
  applyBlockModeVisibility();
  if (blockModeEnabled) loadBlocksForCurrentDay();
});

document.getElementById("blocks-clear").addEventListener("click", () => {
  blockBank = blockBank.concat(blockAssembly);
  blockAssembly = [];
  renderBlocks();
});

document.getElementById("code-submit").addEventListener("click", async () => {
  const btn = document.getElementById("code-submit");
  const resultBox = document.getElementById("code-result");
  const referenceBox = document.getElementById("code-reference");
  const code = blockModeEnabled ? blockAssembly.join("\n") : document.getElementById("code-editor").value;
  const usesSandbox = currentTrackMeta().uses_sandbox;
  if (blockModeEnabled && !code.trim()) {
    alert("Assemble the pieces into your solution first.");
    return;
  }
  btn.disabled = true;
  btn.textContent = usesSandbox ? "Compiling…" : "Submitting…";
  setMascot(usesSandbox ? "Compiling your code…" : "Checking your submission…");
  resultBox.hidden = true;
  referenceBox.hidden = true;
  try {
    const result = await postJSON(`${API}/coding/${current.day.id}/submit`, { code });
    resultBox.hidden = false;
    resultBox.className = "panel-result " + (result.passed ? "" : "fail");
    if (usesSandbox) {
      let text = `${result.passed ? "✓ PASSED" : "✗ FAILED"} ${result.tests_passed}/${result.tests_total} tests`;
      if (result.points_awarded > 0) text += `  (+${result.points_awarded} pts)`;
      text += "\n\n" + (result.output || "");
      if (result.error) text += "\n\n--- stderr ---\n" + result.error;
      resultBox.textContent = text;
    } else {
      resultBox.textContent = result.points_awarded > 0
        ? `✓ Logged  (+${result.points_awarded} pts)`
        : "✓ Logged";
      if (result.reference_solution) {
        referenceBox.hidden = false;
        referenceBox.textContent = `Reference solution:\n${result.reference_solution}`;
      }
    }
    setMascot(result.passed ? "Nice work - on to the next one." : "Not quite - check the output and try again.");
    if (result.passed) await afterComponentComplete();
  } catch (e) {
    alert(`Couldn't submit: ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = current.day.coding_completed
      ? (usesSandbox ? "Re-run (already solved, no extra points)" : "Re-submit (already solved, no extra points)")
      : (usesSandbox ? "Compile & Run" : "Submit & Compare");
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
}

// ---------- tabs / views ----------
document.querySelectorAll(".node-btn").forEach((btn) => {
  btn.addEventListener("click", () => showTab(btn.dataset.tab));
});
function showTab(name) {
  currentTab = name;
  document.querySelectorAll(".node-btn").forEach((b) => b.classList.toggle("current", b.dataset.tab === name));
  document.getElementById("panel-quiz").hidden = name !== "quiz";
  document.getElementById("panel-code").hidden = name !== "code";
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
    const circleClass = d.fully_completed ? "done" : (d.is_late ? "late" : "");
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
    tracks = await getJSON(`${API}/tracks`);
    if (!tracks.some((t) => t.id === currentTrack)) currentTrack = tracks[0]?.id || "cpp_core";
    renderTrackSwitcher();
    await loadToday();
  } catch (e) {
    setMascot("Couldn't load today's challenge");
    console.error(e);
  }
})();
