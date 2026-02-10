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

// === 真贋クイズ ===

// -- モード切替 --
function showQuizPanel(panelId) {
  ['quiz-create', 'quiz-list', 'quiz-play'].forEach(id => {
    document.getElementById(id).classList.add('hidden');
  });
  document.getElementById(panelId).classList.remove('hidden');
}

document.getElementById('btn-quiz-create-mode').addEventListener('click', () => showQuizPanel('quiz-create'));
document.getElementById('btn-quiz-list-mode').addEventListener('click', () => {
  showQuizPanel('quiz-list');
  loadQuizList();
});
document.getElementById('btn-quiz-play-mode').addEventListener('click', () => {
  showQuizPanel('quiz-play');
  initQuizPlay();
});

// -- 画像プレビュー --
function setupFilePreview(fileInputId, previewId, zoneId) {
  const input = document.getElementById(fileInputId);
  input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;
    const preview = document.getElementById(previewId);
    const zone = document.getElementById(zoneId);
    const reader = new FileReader();
    reader.onload = e => {
      preview.innerHTML = `<img src="${e.target.result}">`;
      preview.classList.remove('hidden');
      zone.querySelector('span').textContent = file.name;
    };
    reader.readAsDataURL(file);
  });
}
setupFilePreview('quiz-real-file', 'quiz-real-preview', 'quiz-real-zone');
setupFilePreview('quiz-fake-file', 'quiz-fake-preview', 'quiz-fake-zone');

// -- クイズ登録 --
document.getElementById('btn-quiz-submit').addEventListener('click', async () => {
  const title = document.getElementById('quiz-title').value.trim();
  const explanation = document.getElementById('quiz-explanation').value.trim();
  const realFile = document.getElementById('quiz-real-file').files[0];
  const fakeFile = document.getElementById('quiz-fake-file').files[0];

  if (!title) return alert('作品名を入力してください');
  if (!realFile) return alert('本物画像を選択してください');
  if (!fakeFile) return alert('偽物画像を選択してください');

  const form = new FormData();
  form.append('title', title);
  form.append('explanation', explanation);
  form.append('real_image', realFile);
  form.append('fake_image', fakeFile);

  const res = await fetch(`${API}/quiz`, { method: 'POST', body: form });
  if (res.ok) {
    const data = await res.json();
    alert(`クイズ登録完了: ${data.title} (${data.id})`);
    // フォームリセット
    document.getElementById('quiz-title').value = '';
    document.getElementById('quiz-explanation').value = '';
    document.getElementById('quiz-real-file').value = '';
    document.getElementById('quiz-fake-file').value = '';
    document.getElementById('quiz-real-preview').classList.add('hidden');
    document.getElementById('quiz-fake-preview').classList.add('hidden');
    document.getElementById('quiz-real-zone').querySelector('span').textContent = 'クリックして画像を選択';
    document.getElementById('quiz-fake-zone').querySelector('span').textContent = 'クリックして画像を選択';
  } else {
    alert('登録に失敗しました');
  }
});

// -- クイズ一覧 --
async function loadQuizList() {
  const res = await fetch(`${API}/quiz`);
  const quizzes = await res.json();
  const el = document.getElementById('quiz-list-items');
  if (quizzes.length === 0) {
    el.innerHTML = '<p style="color:var(--dim)">まだクイズが登録されていません。</p>';
    return;
  }
  el.innerHTML = quizzes.map(q => `
    <div class="quiz-list-card">
      ${q.real_image_url ? `<img class="quiz-list-thumb" src="${q.real_image_url}">` : '<div class="quiz-list-thumb"></div>'}
      <div class="quiz-list-info">
        <h4>${q.title}</h4>
        <div class="ql-meta">ID: ${q.id} | 解説: ${q.explanation ? q.explanation.substring(0, 40) + '...' : '(なし)'}</div>
      </div>
      <span class="quiz-list-status ${q.ready ? '' : 'not-ready'}">${q.ready ? '出題可能' : '画像未登録'}</span>
      <button onclick="deleteQuiz('${q.id}')" style="font-size:11px;margin-left:8px">削除</button>
    </div>
  `).join('');
}

async function deleteQuiz(id) {
  if (!confirm('このクイズを削除しますか？')) return;
  await fetch(`${API}/quiz/${id}`, { method: 'DELETE' });
  loadQuizList();
}

// -- 連続出題モード --
let quizSession = {
  items: [],
  current: 0,
  score: 0,
  answers: [],
  currentAnswer: null,
};

async function initQuizPlay() {
  const res = await fetch(`${API}/quiz`);
  const all = await res.json();
  const ready = all.filter(q => q.ready);

  document.getElementById('quiz-play-setup').classList.remove('hidden');
  document.getElementById('quiz-play-area').classList.add('hidden');
  document.getElementById('quiz-final-result').classList.add('hidden');
  document.getElementById('quiz-play-count').textContent = `出題可能な問題: ${ready.length}問`;
  document.getElementById('btn-quiz-start').disabled = ready.length === 0;
}

document.getElementById('btn-quiz-start').addEventListener('click', async () => {
  const res = await fetch(`${API}/quiz`);
  const all = await res.json();
  const ready = all.filter(q => q.ready);
  if (ready.length === 0) return;

  // シャッフル
  for (let i = ready.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [ready[i], ready[j]] = [ready[j], ready[i]];
  }

  quizSession = { items: ready, current: 0, score: 0, answers: [], currentAnswer: null };
  document.getElementById('quiz-play-setup').classList.add('hidden');
  document.getElementById('quiz-final-result').classList.add('hidden');
  document.getElementById('quiz-play-area').classList.remove('hidden');
  loadQuizQuestion();
});

async function loadQuizQuestion() {
  const item = quizSession.items[quizSession.current];
  const res = await fetch(`${API}/quiz/${item.id}/play`);
  const data = await res.json();
  quizSession.currentAnswer = data.answer;

  document.getElementById('quiz-progress-text').textContent =
    `${quizSession.current + 1} / ${quizSession.items.length}`;
  document.getElementById('quiz-score-text').textContent =
    `正解: ${quizSession.score}`;
  document.getElementById('quiz-play-title').textContent = `「${data.title}」`;
  document.getElementById('quiz-left-img').src = data.left_image_url;
  document.getElementById('quiz-right-img').src = data.right_image_url;

  // ボタン有効化
  document.getElementById('btn-quiz-left').disabled = false;
  document.getElementById('btn-quiz-right').disabled = false;
  document.getElementById('quiz-result-area').classList.add('hidden');
  document.getElementById('quiz-explanation-display').classList.add('hidden');
}

async function submitQuizAnswer(choice) {
  const item = quizSession.items[quizSession.current];
  document.getElementById('btn-quiz-left').disabled = true;
  document.getElementById('btn-quiz-right').disabled = true;

  const res = await fetch(`${API}/quiz/${item.id}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ choice, correct_side: quizSession.currentAnswer })
  });
  const result = await res.json();

  const banner = document.getElementById('quiz-result-banner');
  if (result.correct) {
    quizSession.score++;
    banner.textContent = '正解！';
    banner.className = 'correct';
  } else {
    banner.textContent = '不正解…';
    banner.className = 'incorrect';
    if (result.explanation) {
      const expEl = document.getElementById('quiz-explanation-display');
      expEl.innerHTML = `<div class="exp-label">真贋ポイント</div><div class="exp-text">${result.explanation}</div>`;
      expEl.classList.remove('hidden');
    }
  }

  quizSession.answers.push({
    title: item.title,
    correct: result.correct,
    explanation: result.explanation || '',
  });

  document.getElementById('quiz-score-text').textContent = `正解: ${quizSession.score}`;
  document.getElementById('quiz-result-area').classList.remove('hidden');

  // 最終問題なら「次の問題へ」を「結果を見る」に変更
  const nextBtn = document.getElementById('btn-quiz-next');
  if (quizSession.current + 1 >= quizSession.items.length) {
    nextBtn.textContent = '結果を見る';
  } else {
    nextBtn.textContent = '次の問題へ';
  }
}

document.getElementById('btn-quiz-left').addEventListener('click', () => submitQuizAnswer('left'));
document.getElementById('btn-quiz-right').addEventListener('click', () => submitQuizAnswer('right'));

document.getElementById('btn-quiz-next').addEventListener('click', () => {
  quizSession.current++;
  if (quizSession.current >= quizSession.items.length) {
    showQuizFinalResult();
  } else {
    loadQuizQuestion();
  }
});

function showQuizFinalResult() {
  document.getElementById('quiz-play-area').classList.add('hidden');
  document.getElementById('quiz-final-result').classList.remove('hidden');

  const total = quizSession.items.length;
  const score = quizSession.score;
  document.getElementById('quiz-final-score').textContent = `${score} / ${total}`;

  const details = quizSession.answers.map((a, i) =>
    `<div class="final-item ${a.correct ? 'right' : 'wrong'}">
      ${i + 1}. ${a.title} — ${a.correct ? '○ 正解' : '✕ 不正解'}
      ${!a.correct && a.explanation ? `<br><small>真贋ポイント: ${a.explanation}</small>` : ''}
    </div>`
  ).join('');
  document.getElementById('quiz-final-details').innerHTML = details;
}

document.getElementById('btn-quiz-retry').addEventListener('click', () => {
  document.getElementById('quiz-final-result').classList.add('hidden');
  initQuizPlay();
});

// === Init ===
loadCatalog();
loadCategories();
loadPresets();
