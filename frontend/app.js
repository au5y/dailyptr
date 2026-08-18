const API = "/api";
let current = null; // currently loaded ChallengeOut

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

// ---------- stats ----------
async function refreshStats() {
  const stats = await getJSON(`${API}/stats`);
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
  const { day, quiz, coding, concept } = challenge;

  document.getElementById("challenge-date").textContent = day.date;
  const badge = document.getElementById("challenge-badge");
  badge.textContent = day.difficulty;
  badge.className = difficultyBadgeClass(day.difficulty);

  document.getElementById("challenge-late").hidden = !day.is_late;

  renderTabChecks(day);
  renderQuiz(quiz, day);
  renderCode(coding, day);
  renderConcept(concept, day);

  showView("challenge-view");
  showTab("quiz");
}

function renderTabChecks(day) {
  document.getElementById("tab-quiz-check").textContent = day.quiz_completed ? "✓" : "";
  document.getElementById("tab-code-check").textContent = day.coding_completed ? "✓" : "";
  document.getElementById("tab-concept-check").textContent = day.concept_completed ? "✓" : "";
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
      const label = document.createElement("label");
      label.className = "choice";
      label.dataset.qid = q.id;
      label.dataset.ci = ci;
      const input = document.createElement("input");
      input.type = "radio";
      input.name = `q-${q.id}`;
      input.value = ci;
      label.appendChild(input);
      label.appendChild(document.createTextNode(choice));
      div.appendChild(label);
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
  const answers = {};
  document.querySelectorAll("#quiz-questions input[type=radio]:checked").forEach((input) => {
    const qid = input.name.replace("q-", "");
    answers[qid] = parseInt(input.value, 10);
  });
  try {
    const result = await postJSON(`${API}/quiz/${current.day.id}/submit`, { answers });
    const resultBox = document.getElementById("quiz-result");
    resultBox.hidden = false;
    resultBox.textContent = `${result.correct}/${result.total} correct - +${result.points_awarded} pts\n\n` +
      Object.entries(result.explanations).map(([qid, ex]) => {
        const ok = result.results[qid];
        return `${ok ? "✅" : "❌"} ${ex}`;
      }).join("\n\n");
    document.getElementById("quiz-submit").hidden = true;
    document.querySelectorAll("#quiz-questions .choice").forEach((label) => {
      const qid = label.dataset.qid;
      const ci = parseInt(label.dataset.ci, 10);
      const input = label.querySelector("input");
      input.disabled = true;
    });
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
  const editor = document.getElementById("code-editor");
  editor.value = coding.starter_code;
  const resultBox = document.getElementById("code-result");
  resultBox.hidden = true;
  resultBox.className = "result-box";
  document.getElementById("code-submit").textContent = day.coding_completed
    ? "Re-run (already solved, no extra points)"
    : "Compile & Run";
}

document.getElementById("code-submit").addEventListener("click", async () => {
  const btn = document.getElementById("code-submit");
  const resultBox = document.getElementById("code-result");
  const code = document.getElementById("code-editor").value;
  btn.disabled = true;
  btn.textContent = "Compiling…";
  resultBox.hidden = true;
  try {
    const result = await postJSON(`${API}/coding/${current.day.id}/submit`, { code });
    resultBox.hidden = false;
    resultBox.className = "result-box " + (result.passed ? "pass" : "fail");
    let text = `${result.passed ? "✅ PASSED" : "❌ FAILED"} ${result.tests_passed}/${result.tests_total} tests`;
    if (result.points_awarded > 0) text += `  (+${result.points_awarded} pts)`;
    text += "\n\n" + (result.output || "");
    if (result.error) text += "\n\n--- stderr ---\n" + result.error;
    resultBox.textContent = text;
    if (result.passed) await afterComponentComplete();
  } catch (e) {
    alert(`Couldn't run code: ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = current.day.coding_completed ? "Re-run (already solved, no extra points)" : "Compile & Run";
  }
});

// ---------- concept check ----------
function renderConcept(concept, day) {
  document.getElementById("concept-prompt").textContent = concept.prompt;
  document.getElementById("concept-notes").value = "";
  const answerBox = document.getElementById("concept-answer");
  const gradeBox = document.getElementById("concept-grade");
  const resultBox = document.getElementById("concept-result");
  answerBox.hidden = true;
  answerBox.textContent = concept.model_answer;
  gradeBox.hidden = true;
  resultBox.hidden = true;
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

async function submitConceptGrade(gotIt) {
  try {
    const result = await postJSON(`${API}/concept/${current.day.id}/submit`, { self_rating_correct: gotIt });
    document.getElementById("concept-grade").hidden = true;
    document.getElementById("concept-reveal").hidden = true;
    const resultBox = document.getElementById("concept-result");
    resultBox.hidden = false;
    resultBox.textContent = `Model answer:\n${result.model_answer}` +
      (result.points_awarded > 0 ? `\n\n+${result.points_awarded} pts` : "\n\nNo points this time - it'll come back around on a future day.");
    await afterComponentComplete();
  } catch (e) {
    alert(`Couldn't submit: ${e.message}`);
  }
}
document.getElementById("concept-got-it").addEventListener("click", () => submitConceptGrade(true));
document.getElementById("concept-missed").addEventListener("click", () => submitConceptGrade(false));

async function afterComponentComplete() {
  await refreshStats();
  // re-pull the day so completion flags / late flag / tab checkmarks stay in sync
  const day = current.day;
  const fresh = await getJSON(`${API}/day/${day.date}`);
  renderTabChecks(fresh.day);
  current.day = fresh.day;
}

// ---------- tabs / views ----------
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => showTab(tab.dataset.tab));
});
function showTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.getElementById("panel-quiz").hidden = name !== "quiz";
  document.getElementById("panel-code").hidden = name !== "code";
  document.getElementById("panel-concept").hidden = name !== "concept";
}

function showView(name) {
  document.getElementById("challenge-view").hidden = name !== "challenge-view";
  document.getElementById("history-view").hidden = name !== "history-view";
}

// ---------- history ----------
document.getElementById("history-toggle").addEventListener("click", async () => {
  const days = await getJSON(`${API}/history`);
  const list = document.getElementById("history-list");
  list.innerHTML = "";
  if (days.length === 0) {
    list.innerHTML = '<p class="hint">No days yet - come back tomorrow, or check today\'s challenge.</p>';
  }
  days.forEach((d) => {
    const row = document.createElement("div");
    row.className = "history-row";
    const dotClass = d.fully_completed ? "done" : (d.is_late ? "late" : "open");
    row.innerHTML = `
      <div class="hr-left">
        <span class="status-dot ${dotClass}"></span>
        <span>${d.date}</span>
        <span class="badge ${difficultyBadgeClass(d.difficulty)}">${d.difficulty}</span>
      </div>
      <span class="hr-points">${d.points_earned} pts</span>
    `;
    row.addEventListener("click", async () => {
      const challenge = await getJSON(`${API}/day/${d.date}`);
      renderChallenge(challenge);
    });
    list.appendChild(row);
  });
  showView("history-view");
});

// ---------- boot ----------
(async function init() {
  try {
    await refreshStats();
    const today = await getJSON(`${API}/today`);
    renderChallenge(today);
  } catch (e) {
    document.getElementById("challenge-date").textContent = "Couldn't load today's challenge";
    console.error(e);
  }
})();
