const STORAGE_KEY = "pcc-progress-v1";

const state = {
  course: null,
  config: null,
  progress: {},
};

function $(selector, root = document) {
  return root.querySelector(selector);
}

function colabUrl(file) {
  const { owner, repo, branch } = state.config;
  return `https://colab.research.google.com/github/${owner}/${repo}/blob/${branch}/${file}`;
}

function githubUrl(file) {
  const { owner, repo, branch } = state.config;
  return `https://github.com/${owner}/${repo}/blob/${branch}/${file}`;
}

function loadProgress() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    state.progress = raw ? JSON.parse(raw) : {};
  } catch {
    state.progress = {};
  }
}

function saveProgress() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.progress));
}

function lessonProgress(id) {
  if (!state.progress[id]) {
    state.progress[id] = { milestones: {}, quiz: {}, completedAt: null };
  }
  return state.progress[id];
}

function isLessonComplete(lesson) {
  const current = lessonProgress(lesson.id);
  const milestonesDone = lesson.milestones.every((item) => current.milestones[item.id]);
  const quizDone = lesson.quiz.every((item) => current.quiz[item.id] === true);
  return milestonesDone && quizDone;
}

function completionPercent() {
  const lessons = state.course.lessons;
  if (!lessons.length) {
    return 0;
  }
  const done = lessons.filter(isLessonComplete).length;
  return Math.round((done / lessons.length) * 100);
}

function nextLesson() {
  return state.course.lessons.find((lesson) => !isLessonComplete(lesson)) || null;
}

function renderHero() {
  const percent = completionPercent();
  $("#percent").textContent = `${percent}%`;
  $("#barFill").style.width = `${percent}%`;
  const next = nextLesson();
  const nextBox = $("#nextLesson");
  if (next) {
    nextBox.hidden = false;
    $("#nextTitle").textContent = `${next.id} · ${next.title}`;
    $("#nextLink").href = `#lesson-${next.id}`;
  } else {
    nextBox.hidden = false;
    $("#nextTitle").textContent = "You marked every lesson complete.";
    $("#nextLink").href = "#lesson-07";
  }
}

function renderRepoMeta() {
  const { owner, repo, branch } = state.config;
  $("#repoLabel").textContent = `${owner}/${repo}@${branch}`;
  $("#githubRepo").href = `https://github.com/${owner}/${repo}`;
  $("#qualityRuns").href = `https://github.com/${owner}/${repo}/actions/workflows/course-quality.yml`;
}

function renderLessons() {
  const root = $("#lessons");
  root.innerHTML = "";
  for (const lesson of state.course.lessons) {
    const current = lessonProgress(lesson.id);
    const complete = isLessonComplete(lesson);
    const article = document.createElement("article");
    article.className = "lesson";
    article.id = `lesson-${lesson.id}`;
    article.innerHTML = `
      <div class="lesson-head">
        <div>
          <h3>${lesson.id} · ${lesson.title}</h3>
          <p class="meta">${lesson.minutes} min · ${lesson.objectives[0]}</p>
        </div>
        <span class="pill${complete ? " done" : ""}">${complete ? "complete" : "in progress"}</span>
      </div>
      <p class="small">${lesson.objectives.map((item) => `• ${item}`).join("<br>")}</p>
      <p class="links">
        <a href="${colabUrl(lesson.file)}" target="_blank" rel="noreferrer">Open in Colab</a>
        <a href="${githubUrl(lesson.file)}" target="_blank" rel="noreferrer">View on GitHub</a>
      </p>
      <h4>Milestones</h4>
      <ul class="checks"></ul>
      <p class="small">${current.completedAt ? `Completed ${new Date(current.completedAt).toLocaleString()}` : "Not completed yet"}</p>
      <div class="quiz"></div>
    `;
    const list = article.querySelector(".checks");
    for (const milestone of lesson.milestones) {
      const li = document.createElement("li");
      const label = document.createElement("label");
      const box = document.createElement("input");
      box.type = "checkbox";
      box.checked = Boolean(current.milestones[milestone.id]);
      box.addEventListener("change", () => {
        const record = lessonProgress(lesson.id);
        record.milestones[milestone.id] = box.checked;
        touchCompletion(lesson);
        saveProgress();
        render();
      });
      label.append(box, ` ${milestone.label}`);
      li.append(label);
      list.append(li);
    }
    article.querySelector(".quiz").append(renderQuiz(lesson, current));
    root.append(article);
  }
}

function touchCompletion(lesson) {
  const record = lessonProgress(lesson.id);
  record.completedAt = isLessonComplete(lesson) ? record.completedAt || new Date().toISOString() : null;
}

function renderQuiz(lesson, current) {
  const wrap = document.createElement("div");
  wrap.innerHTML = "<h4>Exit check</h4>";
  const list = document.createElement("div");
  list.className = "quiz-list";
  lesson.quiz.forEach((question, index) => {
    const item = document.createElement("div");
    item.className = "quiz-item";
    const fieldset = document.createElement("fieldset");
    const legend = document.createElement("legend");
    legend.textContent = `${index + 1}. ${question.question}`;
    fieldset.append(legend);
    question.choices.forEach((choice, choiceIndex) => {
      const label = document.createElement("label");
      label.className = "choice";
      const input = document.createElement("input");
      input.type = "radio";
      input.name = `${lesson.id}-${question.id}`;
      input.value = String(choiceIndex);
      if (current.quiz[`${question.id}-choice`] === choiceIndex) {
        input.checked = true;
      }
      input.addEventListener("change", () => {
        const record = lessonProgress(lesson.id);
        record.quiz[`${question.id}-choice`] = choiceIndex;
        record.quiz[question.id] = choiceIndex === question.answer;
        touchCompletion(lesson);
        saveProgress();
        render();
      });
      label.append(input, ` ${choice}`);
      fieldset.append(label);
    });
    const feedback = document.createElement("p");
    feedback.className = "feedback";
    if (current.quiz[question.id] === true) {
      feedback.classList.add("ok");
      feedback.textContent = "Correct.";
    } else if (current.quiz[question.id] === false) {
      feedback.classList.add("bad");
      feedback.textContent = "Not yet. Try another option.";
    }
    item.append(fieldset, feedback);
    list.append(item);
  });
  wrap.append(list);
  return wrap;
}

function render() {
  renderRepoMeta();
  renderHero();
  renderLessons();
}

function exportProgress() {
  const blob = new Blob([JSON.stringify(state.progress, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "python-crash-course-progress.json";
  link.click();
  URL.revokeObjectURL(url);
}

function importProgress(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      state.progress = JSON.parse(reader.result);
      saveProgress();
      render();
    } catch {
      window.alert("That file is not valid progress JSON.");
    }
  };
  reader.readAsText(file);
}

function resetProgress() {
  if (window.confirm("Clear progress stored in this browser?")) {
    state.progress = {};
    localStorage.removeItem(STORAGE_KEY);
    render();
  }
}

async function boot() {
  const [course, config] = await Promise.all([
    fetch("course.json").then((res) => res.json()),
    fetch("config.json").then((res) => res.json()),
  ]);
  state.course = course;
  state.config = config;
  $("#courseTitle").textContent = course.title;
  $("#courseSubtitle").textContent = course.subtitle;
  loadProgress();
  $("#exportBtn").addEventListener("click", exportProgress);
  $("#resetBtn").addEventListener("click", resetProgress);
  $("#importInput").addEventListener("change", (event) => {
    const file = event.target.files && event.target.files[0];
    if (file) {
      importProgress(file);
      event.target.value = "";
    }
  });
  render();
}

boot().catch((error) => {
  $("#courseSubtitle").textContent = `Could not load the dashboard: ${error}`;
});
