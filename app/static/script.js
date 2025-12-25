const API_BASE = "http://192.168.127.145:8080/api/v1";

const els = {
  form: document.getElementById("generator-form"),
  submitBtn: document.getElementById("submit-btn"),
  queueBody: document.getElementById("queue-table-body"),
  queueCount: document.getElementById("queue-count"),
  gain: document.getElementById("gain"),
  gainVal: document.getElementById("gain-val"),
  clearBtn: document.getElementById("clear-queue-btn"),
  toastEl: document.getElementById("toast"),
  toastMsg: document.getElementById("toast-msg"),
};

const toast = new bootstrap.Toast(els.toastEl);

// -------------------------
function showToast(msg) {
  els.toastMsg.textContent = msg;
  toast.show();
}

// -------------------------
async function fetchJobs() {
  const res = await fetch(`${API_BASE}/jobs`);
  if (!res.ok) return;

  const jobs = await res.json();
  jobs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  renderJobs(jobs);
}

// -------------------------
function renderJobs(jobs) {
  els.queueBody.innerHTML = "";
  els.queueCount.textContent = jobs.filter((j) => ["QUEUED", "PROCESSING"].includes(j.status)).length;

  if (!jobs.length) {
    els.queueBody.innerHTML = `
      <tr>
        <td colspan="4" class="text-center text-muted py-4">
          Queue is empty
        </td>
      </tr>`;
    return;
  }

  for (const job of jobs) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>
        <span class="badge status-${job.status}">
          ${job.status}
        </span>
      </td>
      <td class="prompt-cell" title="${job.prompt}">
        ${job.prompt}
      </td>
      <td class="duration-cell">
        ${formatDuration(job.duration_s)}
      </td>
      <td class="created-cell">
        ${new Date(job.created_at).toLocaleTimeString([], {
          hour12: false,
        })}
      </td>
      <td class="text-end">
        ${renderActions(job)}
      </td>
    `;

    els.queueBody.appendChild(tr);
  }
}

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;

  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function renderActions(job) {
  // queued -> cancel
  if (job.status === "QUEUED") {
    return `
      <button
        class="btn btn-sm btn-outline-danger"
        title="Cancel job"
        onclick="cancelJob('${job.id}')"
      >
        <i class="bi bi-x-lg"></i>
      </button>
    `;
  }

  // completed -> download + delete
  if (job.status === "COMPLETED") {
    return `
      <div class="action-buttons">
        <a
          class="btn btn-sm btn-outline-primary"
          href="${API_BASE}/jobs/${job.id}/download"
          title="Download file"
        >
          <i class="bi bi-download"></i>
        </a>

        <button
          class="btn btn-sm btn-outline-warning"
          title="Delete job and file"
          onclick="cancelJob('${job.id}')"
        >
          <i class="bi bi-trash"></i>
        </button>
      </div>
    `;
  }

  // failed -> delete
  if (job.status === "FAILED") {
    return `
      <button
        class="btn btn-sm btn-outline-danger"
        title="Delete failed job"
        onclick="cancelJob('${job.id}')"
      >
        <i class="bi bi-trash"></i>
      </button>
    `;
  }

  // processing -> no actions
  return "";
}

// -------------------------
els.gain.addEventListener("input", () => {
  const v = parseFloat(els.gain.value);
  els.gainVal.textContent = `${v > 0 ? "+" : ""}${v}dB`;
});

// -------------------------
els.form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    prompt: document.getElementById("prompt").value.trim(),
    duration_s: Number(document.getElementById("duration").value),
    format: document.getElementById("format").value,
    gain_db: Number(els.gain.value),
  };

  setLoading(true);

  try {
    const res = await fetch(`${API_BASE}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error();
    showToast("Job queued");
    els.form.reset();
    els.gainVal.textContent = "0dB";
    fetchJobs();
  } finally {
    setLoading(false);
  }
});

// -------------------------
els.clearBtn.addEventListener("click", async () => {
  if (!confirm("Cancel all queued jobs?")) return;
  await fetch(`${API_BASE}/jobs?status=QUEUED`, { method: "DELETE" });
  showToast("Queue cleared");
  fetchJobs();
});

window.cancelJob = async (id) => {
  await fetch(`${API_BASE}/jobs/${id}`, { method: "DELETE" });
  showToast("Job cancelled");
  fetchJobs();
};

// -------------------------
function setLoading(state) {
  const spinner = els.submitBtn.querySelector(".spinner-border");
  const text = els.submitBtn.querySelector(".btn-text");

  spinner.classList.toggle("d-none", !state);
  els.submitBtn.disabled = state;
  text.textContent = state ? "Submitting…" : "Queue Generation Job";
}

// -------------------------
fetchJobs();
setInterval(fetchJobs, 3000);
