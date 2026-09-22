const API = window.ARKAN_API || '/api';
const $ = (selector) => document.querySelector(selector);
const notice = $('#notice');

function showNotice(message, error = false) {
  notice.textContent = message;
  notice.className = `notice ${error ? 'error' : 'success'}`;
  notice.hidden = false;
  setTimeout(() => { notice.hidden = true; }, 4000);
}

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { headers: {'Content-Type': 'application/json'}, ...options });
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || `Request failed (${response.status})`);
  return response.json();
}

function navigate(view) {
  document.querySelectorAll('.view').forEach((element) => { element.hidden = element.id !== view; });
  document.querySelectorAll('.nav').forEach((element) => element.classList.toggle('active', element.dataset.view === view));
  if (view === 'projects') loadProjects();
  if (view === 'jobs') loadJobs();
  if (view === 'engines') loadEngines();
}

document.querySelectorAll('[data-view], [data-view-target]').forEach((element) => {
  element.addEventListener('click', () => navigate(element.dataset.view || element.dataset.viewTarget));
});

function status(value) { return `<span class="status ${value}">${value}</span>`; }
function jobsTable(jobs) {
  if (!jobs.length) return '<p class="muted">No jobs yet.</p>';
  return `<table><thead><tr><th>Job</th><th>Engine</th><th>Status</th><th>Updated</th></tr></thead><tbody>${jobs.map(job => `<tr><td class="mono">${job.id.slice(0, 8)}</td><td>${job.engine}</td><td>${status(job.status)}</td><td>${job.updated_at || job.created_at}</td></tr>`).join('')}</tbody></table>`;
}

async function loadOverview() {
  try {
    const [projects, jobs, engines] = await Promise.all([request('/projects'), request('/jobs'), request('/engines')]);
    $('#project-count').textContent = projects.projects.length;
    $('#job-count').textContent = jobs.jobs.length;
    $('#engine-count').textContent = engines.engines.length;
    $('#recent-jobs').innerHTML = jobsTable(jobs.jobs.slice(0, 5));
  } catch (error) { showNotice(error.message, true); }
}
async function loadProjects() {
  try { const data = await request('/projects'); $('#projects-list').innerHTML = data.projects.length ? data.projects.map(project => `<article class="project card"><div class="project-icon">${project.name.charAt(0).toUpperCase()}</div><div><h3>${project.name}</h3><p class="muted">${project.description || 'No description'}</p><span class="mono">${project.id}</span></div></article>`).join('') : '<p class="muted">Create your first project.</p>'; } catch (error) { showNotice(error.message, true); }
}
async function loadJobs() { try { const data = await request('/jobs'); $('#jobs-list').innerHTML = jobsTable(data.jobs); } catch (error) { showNotice(error.message, true); } }
async function loadEngines() { try { const data = await request('/engines'); $('#engines-list').innerHTML = data.engines.map(engine => `<article class="engine card"><div class="engine-header"><h3>${engine.name}</h3><span class="status online">available</span></div><p class="muted">${engine.description || 'Registered Arkan engine adapter'}</p><div class="tags">${(engine.supported_languages || []).map(language => `<span>${language}</span>`).join('')}</div><small>timeout: ${engine.timeout_seconds || '—'}s · license: ${engine.license || 'review required'}</small></article>`).join(''); } catch (error) { showNotice(error.message, true); } }

$('#project-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try { await request('/projects', {method: 'POST', body: JSON.stringify({name: $('#project-name').value, description: $('#project-description').value || null})}); event.target.reset(); showNotice('Project created'); loadProjects(); loadOverview(); } catch (error) { showNotice(error.message, true); }
});
loadOverview();
