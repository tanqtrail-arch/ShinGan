// ShinGan Dashboard
const API = '/api';

// === Tab Navigation ===
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'history') loadHistory();
    if (btn.dataset.tab === 'references') loadReferences();
  });
});

// === Catalog ===
async function loadCatalog(category) {
  const url = category ? `${API}/prompts?category=${category}` : `${API}/prompts`;
  const res = await fetch(url);
  const prompts = await res.json();
  const grid = document.getElementById('prompt-grid');
  document.getElementById('cat-count').textContent = `${prompts.length} prompts`;

  grid.innerHTML = prompts.map(p => `
    <div class="card">
      <h3>${p.name_ja}</h3>
      <div class="meta">${p.category_label} | ${p.resolution} | ${p.aspect_ratio}</div>
      <div class="prompt-text">${p.prompt}</div>
      <div class="tags">
        ${p.use_thinking ? '<span class="tag">Thinking</span>' : ''}
        ${p.use_search_grounding ? '<span class="tag">Search</span>' : ''}
        <span class="tag">${p.id}</span>
      </div>
      <div class="actions">
        <button onclick="generateFromCatalog('${p.id}')" class="btn-primary">Generate</button>
      </div>
    </div>
  `).join('');
}

async function loadCategories() {
  const res = await fetch(`${API}/categories`);
  const cats = await res.json();
  const sel = document.getElementById('cat-filter');
  const batchSel = document.getElementById('batch-cat');
  cats.forEach(c => {
    sel.innerHTML += `<option value="${c.id}">${c.label} (${c.count})</option>`;
    batchSel.innerHTML += `<option value="${c.id}">${c.label} (${c.count})</option>`;
  });
}

document.getElementById('cat-filter').addEventListener('change', e => {
  loadCatalog(e.target.value || null);
});

async function generateFromCatalog(id) {
  const res = await fetch(`${API}/generate/${id}`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: '{}' });
  const data = await res.json();
  alert(`Generated: ${data.id}\nStatus: ${data.status}\nPrompt saved.`);
}

// === Builder ===
async function loadPresets() {
  const res = await fetch(`${API}/builder/presets`);
  const p = await res.json();

  fillSelect('b-style', p.styles);
  fillSelect('b-composition', p.compositions);
  fillSelect('b-lighting', p.lightings);
  fillSelect('b-ar', p.aspect_ratios);
  fillSelect('b-res', p.resolutions);
}

function fillSelect(id, obj) {
  const sel = document.getElementById(id);
  Object.entries(obj).forEach(([k, v]) => {
    sel.innerHTML += `<option value="${v}">${k} - ${v}</option>`;
  });
}

document.getElementById('btn-compile').addEventListener('click', async () => {
  const body = {
    subject: document.getElementById('b-subject').value,
    action: document.getElementById('b-action').value,
    location: document.getElementById('b-location').value,
    style: document.getElementById('b-style').value,
    composition: document.getElementById('b-composition').value,
    lighting: document.getElementById('b-lighting').value,
    constraint: document.getElementById('b-constraint').value,
  };
  // Map AR back to key
  const arSel = document.getElementById('b-ar');
  const arKey = arSel.selectedIndex > 0 ? arSel.options[arSel.selectedIndex].value : '1:1';
  body.aspect_ratio = arKey;

  const resSel = document.getElementById('b-res');
  body.resolution = resSel.selectedIndex > 0 ? resSel.options[resSel.selectedIndex].value : '2K';

  const res = await fetch(`${API}/builder/compile`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  });
  const data = await res.json();
  const box = document.getElementById('compiled-output');
  box.textContent = data.compiled_prompt;
  box.classList.remove('hidden');
  document.getElementById('btn-generate-built').classList.remove('hidden');
  document.getElementById('btn-generate-built').onclick = () => generateFree(data.compiled_prompt);
});

async function generateFree(prompt) {
  const res = await fetch(`${API}/generate`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ prompt })
  });
  const data = await res.json();
  alert(`Generated: ${data.id}\nStatus: ${data.status}`);
}

// === Batch ===
document.getElementById('btn-batch').addEventListener('click', async () => {
  const cat = document.getElementById('batch-cat').value;
  if (!cat) return alert('Select a category');
  const count = document.getElementById('batch-count').value || null;

  const res = await fetch(`${API}/batch/category`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ category: cat, count: count ? parseInt(count) : null })
  });
  const data = await res.json();
  const el = document.getElementById('batch-results');
  el.innerHTML = `<p>${data.length} results created</p>` +
    data.map(r => `<div class="history-item">
      <span class="hi-id">${r.id}</span>
      <span class="hi-prompt">${r.prompt_used.substring(0,60)}...</span>
      <span class="hi-status status-${r.status}">${r.status}</span>
    </div>`).join('');
});

// === References ===
async function loadReferences() {
  const res = await fetch(`${API}/references`);
  const data = await res.json();
  const el = document.getElementById('ref-list');
  const groups = Object.entries(data);
  if (groups.length === 0) {
    el.innerHTML = '<p style="color:var(--dim)">No reference groups yet.</p>';
    return;
  }
  el.innerHTML = groups.map(([g, paths]) => `
    <div class="ref-group">
      <h4>${g} <button onclick="clearRef('${g}')" style="font-size:11px">Clear</button></h4>
      <div class="ref-paths">${paths.length ? paths.join('<br>') : '(empty)'}</div>
    </div>
  `).join('');
}

document.getElementById('btn-add-ref').addEventListener('click', async () => {
  const group = document.getElementById('ref-group').value;
  const path = document.getElementById('ref-path').value;
  if (!group || !path) return;
  await fetch(`${API}/references/${group}`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ paths: [path] })
  });
  loadReferences();
  document.getElementById('ref-path').value = '';
});

async function clearRef(group) {
  await fetch(`${API}/references/${group}`, { method: 'DELETE' });
  loadReferences();
}

// === History ===
async function loadHistory() {
  const res = await fetch(`${API}/history`);
  const data = await res.json();
  const el = document.getElementById('history-list');
  if (data.length === 0) {
    el.innerHTML = '<p style="color:var(--dim)">No history yet.</p>';
    return;
  }
  el.innerHTML = data.map(r => `
    <div class="history-item">
      <div class="img-placeholder" onclick="openAttach('${r.id}')">
        ${r.image_url ? `<img src="${r.image_url}">` : 'Attach'}
      </div>
      <span class="hi-id">${r.id}</span>
      <span class="hi-prompt">${(r.prompt_used || '').substring(0,80)}</span>
      <span class="hi-status status-${r.status}">${r.status}</span>
    </div>
  `).join('');
}

document.getElementById('btn-refresh-history').addEventListener('click', loadHistory);
document.getElementById('btn-export-history').addEventListener('click', async () => {
  const res = await fetch(`${API}/history/export`);
  const data = await res.json();
  const blob = new Blob([JSON.stringify(data, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'shingan_history.json';
  a.click();
});

// === Attach Modal ===
let attachTargetId = null;

function openAttach(id) {
  attachTargetId = id;
  document.getElementById('attach-id').textContent = 'Result: ' + id;
  document.getElementById('attach-modal').classList.remove('hidden');
}

document.getElementById('btn-attach-cancel').addEventListener('click', () => {
  document.getElementById('attach-modal').classList.add('hidden');
});

document.getElementById('btn-attach-submit').addEventListener('click', async () => {
  const file = document.getElementById('attach-file').files[0];
  if (!file || !attachTargetId) return;
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API}/attach/${attachTargetId}`, { method: 'POST', body: form });
  if (res.ok) {
    document.getElementById('attach-modal').classList.add('hidden');
    loadHistory();
  } else {
    alert('Attach failed');
  }
});

// === Init ===
loadCatalog();
loadCategories();
loadPresets();
