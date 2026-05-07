let currentProject = null;
let projectTypes = [];

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  return res.json();
}

function title(value) {
  return String(value || "").replaceAll("_", " ");
}

function mediaCard(file) {
  const lower = file.name.toLowerCase();
  let preview = "";
  if (lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png") || lower.endsWith(".webp")) {
    preview = `<img src="${file.url}" alt="${file.name}">`;
  } else if (lower.endsWith(".mp4") || lower.endsWith(".webm")) {
    preview = `<video controls src="${file.url}"></video>`;
  }
  return `<div class="media-card">${preview}<a href="${file.url}" target="_blank">${file.name}</a></div>`;
}

async function loadHealth() {
  const health = await api("/api/health");
  $("health").textContent = health.fal_key_set ? "FAL key ready" : "FAL key missing";
}

function setSelectedType(type) {
  const form = $("projectForm");
  form.elements.video_type.value = type.id;
  form.elements.target_duration_seconds.value = type.default_duration;
  form.elements.audience.value = type.default_audience;
  form.elements.style.value = type.default_style;
  form.elements.goal.value = type.starter_goal;
  $("selectedType").textContent = type.name;

  document.querySelectorAll(".type-card").forEach((card) => {
    card.classList.toggle("active", card.dataset.type === type.id);
  });
}

async function loadProjectTypes() {
  projectTypes = await api("/api/project-types");
  $("typeCatalog").innerHTML = projectTypes.map((type) => `
    <button class="type-card" data-type="${type.id}" type="button">
      <strong>${type.name}</strong>
      <p>${type.description}</p>
      <div class="pill-row">${type.best_for.slice(0, 4).map((item) => `<span class="pill">${item}</span>`).join("")}</div>
      <p>Needs: ${type.needs.join(", ")}</p>
    </button>
  `).join("");

  document.querySelectorAll(".type-card").forEach((card) => {
    card.addEventListener("click", () => {
      const type = projectTypes.find((item) => item.id === card.dataset.type);
      setSelectedType(type);
    });
  });

  if (projectTypes.length) {
    setSelectedType(projectTypes[0]);
  }
}

async function loadProjects() {
  const projects = await api("/api/projects");
  $("projectList").innerHTML = projects.map((project) => `
    <button class="project-item" data-project="${project.project}">
      <strong>${project.project}</strong>
      <span>${title(project.video_type)} - ${title(project.approval_status)}</span>
    </button>
  `).join("") || `<p class="muted">No projects yet.</p>`;

  document.querySelectorAll("[data-project]").forEach((button) => {
    button.addEventListener("click", () => loadProject(button.dataset.project));
  });
}

async function loadProject(project) {
  currentProject = project;
  const detail = await api(`/api/projects/${project}`);
  const manifest = detail.manifest || {};
  const checklist = manifest.checklist || [];
  const outputs = detail.outputs || {};

  const media = Object.entries(outputs)
    .flatMap(([folder, files]) => files.slice(0, 6).map((file) => ({ ...file, folder })))
    .filter((file) => /\.(jpg|jpeg|png|webp|mp4|webm)$/i.test(file.name));

  $("projectDetail").classList.remove("empty");
  $("projectDetail").innerHTML = `
    <h3>${project}</h3>
    <p class="muted">${title(manifest.video_type)} - ${title(manifest.approval_status)}</p>
    <div class="checklist">
      ${checklist.map((item) => `<div class="check-item ${item.done ? "done" : ""}">${item.done ? "[x]" : "[ ]"} ${item.label}</div>`).join("")}
    </div>
    <details>
      <summary>Brief</summary>
      <pre>${detail.brief || ""}</pre>
    </details>
    <details>
      <summary>Scene plan JSON</summary>
      <pre>${JSON.stringify(detail.scene_plan || {}, null, 2)}</pre>
    </details>
    <h3>Recent Media</h3>
    <div class="media-grid">${media.map(mediaCard).join("") || `<p class="muted">No media yet.</p>`}</div>
    ${commandBlock(detail.commands)}
  `;
}

async function loadJobs() {
  const jobs = await api("/api/jobs");
  $("jobs").innerHTML = jobs.map((job) => `
    <div class="job">
      <strong>${job.stage}</strong>
      <span class="muted">${job.project} - ${job.status}</span>
      <pre>${job.output || job.command.join(" ")}</pre>
    </div>
  `).join("") || `<p class="muted">No jobs yet.</p>`;
}

function formPayload(form) {
  const data = new FormData(form);
  return {
    name: data.get("name"),
    video_type: data.get("video_type"),
    goal: data.get("goal"),
    audience: data.get("audience"),
    aspect_ratio: data.get("aspect_ratio"),
    target_duration_seconds: Number(data.get("target_duration_seconds")),
    style: data.get("style"),
    voiceover: data.get("voiceover") === "on",
    must_include: data.get("must_include"),
    must_avoid: data.get("must_avoid"),
  };
}

function thoughtPayload(form) {
  const data = new FormData(form);
  return {
    thought: data.get("thought"),
    video_type: data.get("video_type"),
    aspect_ratio: data.get("aspect_ratio"),
    target_duration_seconds: Number(data.get("target_duration_seconds")),
  };
}

function commandBlock(commands) {
  if (!commands) return "";
  return `
    <h3>FAL Commands</h3>
    <div class="commands">
      ${Object.entries(commands).map(([stage, list]) => `
        <details open>
          <summary>${title(stage)}</summary>
          ${list.map((command) => `<pre>${command}</pre>`).join("")}
        </details>
      `).join("")}
    </div>
  `;
}

$("projectForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const created = await api("/api/projects", {
    method: "POST",
    body: JSON.stringify(formPayload(event.currentTarget)),
  });
  await loadProjects();
  await loadProject(created.project);
});

$("thoughtForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const created = await api("/api/projects/from-thought", {
    method: "POST",
    body: JSON.stringify(thoughtPayload(event.currentTarget)),
  });
  await loadProjects();
  await loadProject(created.project);
});

$("refreshProjects").addEventListener("click", loadProjects);
$("reloadProject").addEventListener("click", () => currentProject && loadProject(currentProject));
$("refreshJobs").addEventListener("click", loadJobs);

setInterval(loadJobs, 5000);

loadHealth().catch((error) => ($("health").textContent = error.message));
loadProjectTypes();
loadProjects();
loadJobs();
