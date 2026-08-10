let currentJobs = [];
let activeProfile = null;

document.addEventListener("DOMContentLoaded", () => {
    setupDragAndDrop();
    fetchProfile();
    loadJobs();
    fetchHistory();
});

// Setup drag and drop for resume uploader
function setupDragAndDrop() {
    const dropZone = document.getElementById("drop-zone");
    const input = document.getElementById("resume-input");

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    input.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

// Upload resume to backend API
async function handleFileUpload(file) {
    showToast(`Uploading ${file.name}...`);
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/upload-resume", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (data.status === "success") {
            showToast("Resume parsed & skills extracted successfully!", "success");
            activeProfile = data.profile;
            updateProfileUI(data.profile, data.file_name);
            loadJobs(); // Refresh jobs with new resume matching
        } else {
            showToast("Failed to parse resume: " + data.message, "error");
        }
    } catch (err) {
        showToast("Error uploading file: " + err.message, "error");
    }
}

// Fetch active profile
async function fetchProfile() {
    try {
        const res = await fetch("/api/profile");
        const data = await res.json();
        if (data.status === "success") {
            activeProfile = data.profile;
            updateProfileUI(data.profile, data.file_name);
        }
    } catch (err) {
        console.error("Error fetching profile:", err);
    }
}

// Update sidebar profile UI
function updateProfileUI(profile, fileName) {
    if (!profile) return;

    document.getElementById("profile-status").innerText = fileName || "Active Resume";
    document.getElementById("candidate-name").innerText = profile.name || "Candidate";
    document.getElementById("candidate-title").innerText = (profile.experience_level || "Tech") + " Professional";
    document.getElementById("candidate-email").innerText = profile.email || "No email detected";
    document.getElementById("candidate-phone").innerText = profile.phone || "No phone detected";
    document.getElementById("candidate-linkedin").innerText = profile.linkedin ? "LinkedIn Profile" : "No LinkedIn";

    // Set Initials Avatar
    const initials = (profile.name || "CA").split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
    document.getElementById("candidate-avatar").innerText = initials;

    // Render Skill Tags
    const skillsContainer = document.getElementById("profile-skills");
    skillsContainer.innerHTML = "";
    (profile.skills || []).forEach(skill => {
        const tag = document.createElement("span");
        tag.className = "skill-tag";
        tag.innerText = skill;
        skillsContainer.appendChild(tag);
    });
}

let searchTimeout = null;
function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(loadJobs, 400);
}

// Fetch matched jobs
async function loadJobs() {
    const loc = document.getElementById("location-select").value;
    const query = document.getElementById("keyword-search").value;
    const container = document.getElementById("jobs-container");

    container.innerHTML = `<div style="text-align: center; padding: 3rem; color: var(--text-muted);"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><p style="margin-top: 1rem;">Scanning remote jobs in India & worldwide...</p></div>`;

    try {
        const url = `/api/search-jobs?location=${encodeURIComponent(loc)}&query=${encodeURIComponent(query)}`;
        const res = await fetch(url);
        const data = await res.json();

        if (data.status === "success") {
            currentJobs = data.jobs;
            document.getElementById("jobs-count").innerText = currentJobs.length;
            document.getElementById("stat-match-count").innerText = currentJobs.length;
            renderJobs(currentJobs);
        }
    } catch (err) {
        container.innerHTML = `<div style="text-align: center; padding: 2rem; color: #ef4444;"><i class="fa-solid fa-triangle-exclamation"></i> Error loading jobs: ${err.message}</div>`;
    }
}

// Render dynamic Job Cards
function renderJobs(jobs) {
    const container = document.getElementById("jobs-container");
    container.innerHTML = "";

    if (jobs.length === 0) {
        container.innerHTML = `<div style="text-align: center; padding: 3rem; color: var(--text-muted);"><i class="fa-regular fa-folder-open fa-2x"></i><p style="margin-top: 1rem;">No matching remote jobs found for these criteria.</p></div>`;
        return;
    }

    jobs.forEach(job => {
        const matchScore = job.match_score || 75;
        const matchClass = matchScore >= 80 ? "match-high" : "match-medium";
        const matchedSkillsStr = (job.matching_skills || []).slice(0, 4).join(", ") || "Relevant skills";

        const card = document.createElement("div");
        card.className = "job-card";
        card.innerHTML = `
            <div class="job-header">
                <div>
                    <h3 class="job-title">${escapeHtml(job.title)}</h3>
                    <p class="company-name"><i class="fa-regular fa-building"></i> ${escapeHtml(job.company)}</p>
                </div>
                <div class="match-badge ${matchClass}">
                    <i class="fa-solid fa-fire"></i> ${matchScore}% Match
                </div>
            </div>

            <div class="job-meta-row">
                <div class="job-meta-item loc-tag">
                    <i class="fa-solid fa-globe"></i> ${escapeHtml(job.remote_type || job.location)}
                </div>
                <div class="job-meta-item">
                    <i class="fa-solid fa-money-bill-wave"></i> ${escapeHtml(job.salary || "Competitive")}
                </div>
                <div class="job-meta-item">
                    <i class="fa-regular fa-calendar"></i> Posted: ${escapeHtml(job.posted_date || "Recent")}
                </div>
                <div class="job-meta-item">
                    <i class="fa-solid fa-layer-group"></i> ${escapeHtml(job.source || "Direct ATS")}
                </div>
            </div>

            <p class="job-desc">${escapeHtml(job.description.substring(0, 240))}...</p>

            <div class="job-actions">
                <div class="matched-skills-preview">
                    Matched Skills: <span>${escapeHtml(matchedSkillsStr)}</span>
                </div>
                <div style="display: flex; gap: 0.6rem;">
                    <button class="btn btn-secondary" onclick="viewCoverLetter('${job.id}')">
                        <i class="fa-solid fa-file-lines"></i> Cover Letter
                    </button>
                    <button class="btn btn-primary" onclick="applySingleJob('${job.id}')">
                        <i class="fa-solid fa-paper-plane"></i> Auto-Apply Now
                    </button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

// Single Job Auto-Apply
async function applySingleJob(jobId) {
    const job = currentJobs.find(j => j.id === jobId);
    if (!job) return;

    showToast(`Applying to ${job.title} at ${job.company}...`);

    const formData = new FormData();
    formData.append("job_id", jobId);
    formData.append("job_data_json", JSON.stringify(job));

    try {
        const res = await fetch("/api/apply-job", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (data.status === "success") {
            showToast(`Applied successfully to ${job.company}!`, "success");
            fetchHistory();
        } else {
            showToast(`Application error: ${data.message}`, "error");
        }
    } catch (err) {
        showToast("Error submitting application: " + err.message, "error");
    }
}

// Batch Auto-Apply
async function runBatchApply() {
    const loc = document.getElementById("location-select").value;
    if (!confirm(`Are you sure you want to trigger FULL AUTO-APPLY to all matching remote jobs in (${loc})?`)) return;

    showToast("Starting Batch Auto-Apply sequence for matched jobs...", "info");

    const formData = new FormData();
    formData.append("location", loc);
    formData.append("min_score", 70);

    try {
        const res = await fetch("/api/batch-apply", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (data.status === "success") {
            showToast(`Auto-applied to ${data.total_applied} jobs successfully!`, "success");
            fetchHistory();
        }
    } catch (err) {
        showToast("Batch application failed: " + err.message, "error");
    }
}

// Cover Letter Preview Modal
function viewCoverLetter(jobId) {
    const job = currentJobs.find(j => j.id === jobId);
    if (!job || !job.cover_letter) return;

    document.getElementById("cover-letter-text").value = job.cover_letter;
    document.getElementById("cover-modal").style.display = "flex";
}

function closeModal() {
    document.getElementById("cover-modal").style.display = "none";
}

function copyCoverLetter() {
    const text = document.getElementById("cover-letter-text").value;
    navigator.clipboard.writeText(text);
    showToast("Cover letter copied to clipboard!", "success");
}

// Application History
async function fetchHistory() {
    try {
        const res = await fetch("/api/history");
        const data = await res.json();
        if (data.status === "success") {
            document.getElementById("stat-applied-count").innerText = data.total;
            renderHistory(data.history);
        }
    } catch (err) {
        console.error("Error loading history:", err);
    }
}

function renderHistory(history) {
    const list = document.getElementById("history-list");
    list.innerHTML = "";
    if (!history || history.length === 0) {
        list.innerHTML = `<p style="color: var(--text-dim); text-align: center; padding: 1rem;">No applications submitted yet.</p>`;
        return;
    }

    history.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";
        div.innerHTML = `
            <div class="history-item-title">${escapeHtml(item.title)} - ${escapeHtml(item.company)}</div>
            <div class="history-item-sub">
                <span class="status-submitted"><i class="fa-solid fa-check-circle"></i> ${escapeHtml(item.status)}</span>
                <span>${escapeHtml(item.applied_at || 'Just now')}</span>
            </div>
        `;
        list.appendChild(div);
    });
}

// Toast notification helper
function showToast(msg, type = "info") {
    const toast = document.getElementById("toast");
    toast.innerText = msg;
    toast.className = `toast show ${type}`;
    setTimeout(() => {
        toast.className = "toast";
    }, 4000);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}
