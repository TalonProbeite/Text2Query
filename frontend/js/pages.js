/* =====================================================
   SQLCRAFT — pages.js
   Инициализация страниц: index, auth, workshop.
   Зависит от core.js (должен подключаться первым).
   ===================================================== */

/* ── INDEX PAGE INIT ────────────────────────────────────── */
function initIndex() {
  if (!document.getElementById('index-page')) return;

  const authError = sessionStorage.getItem('auth_error');
  if (authError) {
    sessionStorage.removeItem('auth_error');
    setTimeout(() => showToast(authError, 'error'), 200);
  }

  // Проверяем реальный статус сессии через сервер
  api.getMe().then(me => {
    const navbarAuth = document.getElementById('navbar-auth');
    if (!navbarAuth) return;
    if (me.is_logged) {
      const initial = (me.name || '?')[0].toUpperCase();
      navbarAuth.innerHTML = `
        <div class="navbar-user-card">
          <div class="navbar-user-avatar">${initial}</div>
          <div class="navbar-user-info">
            <div class="navbar-user-name">${me.name}</div>
            <div class="navbar-user-plan">${me.plan || 'free'}</div>
          </div>
        </div>
        <a class="btn btn-primary btn-sm" href="workshop.html">Мастерская →</a>
      `;
    } else {
      // Токен просрочен или невалиден — чистим localStorage
      localStorage.removeItem('sqlcraft_user');
    }
  }).catch(() => {
    localStorage.removeItem('sqlcraft_user');
  });

  const cursor = document.getElementById('hero-cursor');
  if (cursor) {
    const texts = [
      'Покажи топ-10 клиентов по выручке за этот месяц',
      'Найди незавершённые заказы старше 7 дней',
      'Средний чек по категориям товаров',
    ];
    let ti = 0, ci = 0, deleting = false;
    const targetEl = document.getElementById('hero-typing');
    if (targetEl) {
      function type() {
        const text = texts[ti];
        if (!deleting) {
          targetEl.textContent = text.slice(0, ++ci);
          if (ci === text.length) { deleting = true; setTimeout(type, 1800); return; }
        } else {
          targetEl.textContent = text.slice(0, --ci);
          if (ci === 0) { deleting = false; ti = (ti + 1) % texts.length; }
        }
        setTimeout(type, deleting ? 30 : 55);
      }
      setTimeout(type, 600);
    }
  }

  document.querySelectorAll('[data-goto]').forEach(el => {
    el.addEventListener('click', () => window.location.href = el.dataset.goto);
  });
}

/* ── AUTH PAGE INIT ─────────────────────────────────────── */
function initAuth() {
  if (!document.getElementById('auth-page')) return;

  // Проверяем через сервер — localStorage врать может (просроченный токен)
  api.getMe().then(me => {
    if (me.is_logged) {
      window.location.href = 'workshop.html';
    } else {
      // Токен невалиден — чистим localStorage
      localStorage.removeItem('sqlcraft_user');
    }
  }).catch(() => {
    localStorage.removeItem('sqlcraft_user');
  });

  const tabs = document.querySelectorAll('.auth-tab');
  const panels = document.querySelectorAll('.auth-form-panel');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(tab.dataset.panel)?.classList.add('active');
    });
  });

  function showAlert(form, msg) {
    const id = form === 'login' ? 'alert-login' : 'alert-register';
    let el = document.getElementById(id);
    if (!el) {
      el = document.createElement('div');
      el.id = id;
      el.className = 'auth-alert';
      const btn = document.getElementById(form === 'login' ? 'login-btn' : 'register-btn');
      btn?.parentNode.insertBefore(el, btn);
    }
    el.textContent = msg;
    el.style.display = 'flex';
  }

  function clearAlert(form) {
    const el = document.getElementById(form === 'login' ? 'alert-login' : 'alert-register');
    if (el) el.style.display = 'none';
  }

  document.getElementById('login-btn')?.addEventListener('click', async () => {
    const email = document.getElementById('login-email')?.value?.trim();
    const pass  = document.getElementById('login-pass')?.value;
    if (!email || !pass) return showAlert('login', 'Заполните все поля');
    clearAlert('login');
    const btn = document.getElementById('login-btn');
    btn.disabled = true; btn.textContent = 'Вход...';
    try {
      const { user } = await api.login(email, pass);
      auth.setSession(user);
      window.location.href = 'workshop.html';
    } catch (err) {
      showAlert('login', err.msg || err.message || 'Неизвестная ошибка');
    } finally {
      btn.disabled = false; btn.textContent = 'Войти';
    }
  });

  document.getElementById('register-btn')?.addEventListener('click', async () => {
    const name  = document.getElementById('reg-name')?.value?.trim();
    const email = document.getElementById('reg-email')?.value?.trim();
    const pass  = document.getElementById('reg-pass')?.value;
    if (!name || !email || !pass) return showAlert('register', 'Заполните все поля');
    if (pass.length < 8) return showAlert('register', 'Пароль должен быть минимум 8 символов');
    clearAlert('register');
    const btn = document.getElementById('register-btn');
    btn.disabled = true; btn.textContent = 'Регистрация...';
    try {
      const { user } = await api.register(name, email, pass);
      auth.setSession(user);
      window.location.href = 'workshop.html';
    } catch (err) {
      showAlert('register', err.msg || err.message || 'Неизвестная ошибка');
    } finally {
      btn.disabled = false; btn.textContent = 'Создать аккаунт';
    }
  });
}

/* ── WORKSHOP PAGE INIT ─────────────────────────────────── */
function initWorkshop() {
  if (!document.getElementById('workshop-page')) return;
  if (!auth.requireAuth()) return;
  document.body.style.visibility = 'visible';

  // User card — берём реальные данные с сервера
  api.getMe().then(me => {
    if (!me.is_logged) return;
    const nameEl   = document.getElementById('user-name');
    const planEl   = document.getElementById('user-plan');
    const avatarEl = document.getElementById('user-avatar');
    if (nameEl)   nameEl.textContent   = me.name || me.email || '';
    if (planEl)   planEl.textContent   = me.plan || 'free';
    if (avatarEl) avatarEl.textContent = (me.name || '?')[0].toUpperCase();
  }).catch(() => {});

  let currentSQL     = '';
  let lastResults    = null;
  // Multi-DB state
  const connectedDBs = [];
  let activeDBId = null;
  function hasActiveDB() { return activeDBId !== null; }

  // Dialect
  const dialectBtn  = document.getElementById('dialect-btn');
  const dialectDrop = document.getElementById('dialect-dropdown');
  const dialect = dialectBtn && dialectDrop ? new DialectSelector(dialectBtn, dialectDrop) : null;

  // Elements
  const resultsSection = document.getElementById('results-section');
  const executeSection = document.getElementById('execute-section');
  const execBtn        = document.getElementById('exec-sql-btn');
  const promptTextarea = document.getElementById('prompt-textarea');
  const generateBtn    = document.getElementById('generate-btn');
  const sqlEditor      = document.getElementById('sql-output-body');

  /* ── HISTORY ──────────────────────────────────────────── */
  let history = [];

  function formatDate(isoStr) {
    const d = new Date(isoStr);
    return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  }

  function renderHistory() {
    const container = document.getElementById('history-list');
    if (!container) return;
    if (history.length === 0) {
      container.innerHTML = `<div style="font-size:12px; font-family:var(--font-mono); color:var(--text-dim); padding: 8px 4px;">История пуста</div>`;
      return;
    }
    container.innerHTML = history.map((h, i) => `
      <div class="history-item" data-index="${i}">
        <div class="history-item-query">${h.prompt}</div>
        <div class="history-item-time">${formatDate(h.created_at)}</div>
      </div>
    `).join('');

    container.querySelectorAll('.history-item').forEach(el => {
      el.addEventListener('click', () => selectHistory(+el.dataset.index));
    });
  }

  function selectHistory(i) {
    const h = history[i];
    if (!h) return;

    if (promptTextarea) promptTextarea.value = h.prompt;

    if (dialect) {
      dialect.value = h.dialect;
      if (dialectBtn) dialectBtn.querySelector('.dialect-current').textContent = h.dialect;
      document.querySelectorAll('.dialect-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.value === h.dialect);
      });
    }

    currentSQL = h.query;
    renderSQL(h.query, h.is_danger);

    document.querySelectorAll('.history-item').forEach((el, j) =>
      el.classList.toggle('active', j === i)
    );
  }

  function addHistoryItem(entry) {
    history.unshift(entry);
    renderHistory();
  }

  async function loadHistory() {
    try {
      history = await api.getHistory();
    } catch {
      history = [];
      showToast('Не удалось загрузить историю', 'error');
    }
    renderHistory();
  }

  loadHistory();

  /* ── LOGOUT ───────────────────────────────────────────── */
  document.getElementById('logout-btn')?.addEventListener('click', () => auth.logout());

  /* ── DB CONNECT BTN ───────────────────────────────────── */
  document.getElementById('db-connect-btn')?.addEventListener('click', () => openDBModal());

  /* ── GENERATE ─────────────────────────────────────────── */
  if (generateBtn && promptTextarea) {
    generateBtn.addEventListener('click', handleGenerate);
    promptTextarea.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') handleGenerate();
    });
  }

  // Синхронизируем currentSQL с тем что юзер мог отредактировать в редакторе
  if (sqlEditor) {
    sqlEditor.addEventListener('input', () => { currentSQL = sqlEditor.value; });
  }

  async function handleGenerate() {
    const prompt = promptTextarea.value.trim();
    if (!prompt) { showToast('Введите запрос', 'error'); return; }
    setGenerating(true);
    try {
      const { query, is_danger } = await api.generateSQL(prompt, dialect ? dialect.value : 'postgresql');
      renderSQL(query, is_danger);
      addHistoryItem({
        prompt,
        query,
        is_danger,
        dialect: dialect ? dialect.value : 'postgresql',
        created_at: new Date().toISOString(),
      });
      if (is_danger) {
        showToast('⚠️ Запрос может изменить или удалить данные — проверьте перед выполнением', 'error');
      } else {
        showToast('SQL сгенерирован', 'success');
      }
      if (executeEnabled && hasActiveDB()) await handleExecute();
    } catch (err) {
      showToast(err.msg || err.message || 'Неизвестная ошибка', 'error');
    } finally {
      setGenerating(false);
    }
  }

  function setGenerating(v) {
    if (!generateBtn) return;
    generateBtn.disabled = v;
    generateBtn.innerHTML = v
      ? '<span class="spin-icon">◌</span> Генерация...'
      : '⚡ Генерировать SQL';
    if (v) {
      const spin = generateBtn.querySelector('.spin-icon');
      if (spin) spin.style.animation = 'spin 1s linear infinite';
    }
  }

  function renderSQL(sql, is_danger = false) {
    if (sqlEditor) sqlEditor.value = sql;
    currentSQL = sql;
    const badge = document.getElementById('danger-badge');
    if (badge) badge.style.display = is_danger ? 'inline-flex' : 'none';
  }

  /* ── EXECUTE ──────────────────────────────────────────── */
  if (execBtn) execBtn.addEventListener('click', handleExecute);

  async function handleExecute() {
    const sql = sqlEditor ? sqlEditor.value.trim() : currentSQL;
    if (!sql) { showToast('Сначала сгенерируйте или введите SQL', 'error'); return; }
    if (!hasActiveDB()) { showToast('Подключите базу данных', 'error'); return; }
    if (execBtn) { execBtn.disabled = true; execBtn.textContent = '▶ Выполнение...'; }
    if (executeSection) executeSection.style.display = 'block';
    if (resultsSection) resultsSection.style.display = 'block';
    try {
      const activeDB = connectedDBs.find(d => d.id === activeDBId);
      const results = await api.executeSQL(sql, activeDB.config);
      lastResults = results;
      renderResults(results);
      showToast(`Получено ${results.rowCount} строк`, 'success');
    } catch (err) {
      showToast(err.msg || err.message || 'Ошибка выполнения', 'error');
    } finally {
      if (execBtn) { execBtn.disabled = false; execBtn.textContent = '▶ Выполнить'; }
    }
  }

  function renderResults(results) {
    const tbody  = document.getElementById('results-tbody');
    const thead  = document.getElementById('results-thead');
    const footer = document.getElementById('results-footer-info');
    if (!tbody || !thead) return;
    thead.innerHTML = results.columns.map(c => `<th>${c}</th>`).join('');
    tbody.innerHTML = results.rows.map(row =>
      `<tr>${row.map(v => `<td class="${v === null ? 'null-val' : ''}">${v === null ? 'NULL' : v}</td>`).join('')}</tr>`
    ).join('');
    if (footer) footer.textContent = `${results.rowCount} строк • ${results.execMs}ms`;
  }

  /* ── COPY SQL ─────────────────────────────────────────── */
  const copyBtn = document.getElementById('copy-sql-btn');
  if (copyBtn) copyBtn.addEventListener('click', () => {
    if (currentSQL) copyToClipboard(currentSQL);
    else showToast('Нет SQL для копирования', 'error');
  });

  /* ── EXPORT ───────────────────────────────────────────── */
  document.getElementById('export-csv')?.addEventListener('click', () => {
    if (!lastResults) return showToast('Нет данных для экспорта', 'error');
    exportUtils.download('results.csv', exportUtils.toCSV(lastResults), 'text/csv');
    showToast('CSV экспортирован', 'success');
  });
  document.getElementById('export-json')?.addEventListener('click', () => {
    if (!lastResults) return showToast('Нет данных для экспорта', 'error');
    exportUtils.download('results.json', exportUtils.toJSON(lastResults), 'application/json');
    showToast('JSON экспортирован', 'success');
  });
  document.getElementById('export-sql')?.addEventListener('click', () => {
    if (!currentSQL) return showToast('Нет SQL для экспорта', 'error');
    exportUtils.download('query.sql', currentSQL, 'text/plain');
    showToast('SQL файл скачан', 'success');
  });

  /* ── DB MODAL ─────────────────────────────────────────── */
  const dbModal = document.getElementById('db-modal');
  window.openDBModal  = () => dbModal?.classList.add('open');
  window.closeDBModal = () => dbModal?.classList.remove('open');

  const dbConnectSubmitBtn = document.getElementById('db-connect-submit');
  if (dbConnectSubmitBtn) {
    dbConnectSubmitBtn.addEventListener('click', async () => {
      dbConnectSubmitBtn.disabled = true;
      dbConnectSubmitBtn.textContent = 'Подключение...';
      try {
        const dbName  = document.getElementById('db-name')?.value?.trim() || 'mydb';
        const host    = document.getElementById('db-host')?.value?.trim() || 'localhost';
        const db_type = document.getElementById('db-type')?.value || 'postgresql';
        const config = {
          host,
          port:     document.getElementById('db-port')?.value || '5432',
          db_name:  dbName,
          username: document.getElementById('db-user')?.value?.trim() || '',
          password: document.getElementById('db-pass')?.value || '',
          db_type,
        };
        await api.connectDB(config);
        const id = Date.now();
        connectedDBs.push({ id, name: dbName, host, config });
        activeDBId = id;
        renderDBList();
        closeDBModal();
        showToast(`БД «${dbName}» подключена!`, 'success');
        if (executeSection) executeSection.style.display = 'block';
      } catch (err) {
        showToast(`Ошибка подключения: ${err.message}`, 'error');
      } finally {
        dbConnectSubmitBtn.disabled = false;
        dbConnectSubmitBtn.textContent = 'Подключить';
      }
    });
  }

  function renderDBList() {
    const list = document.getElementById('db-list');
    if (!list) return;
    if (connectedDBs.length === 0) {
      list.innerHTML = `<div style="font-size:12px; font-family:var(--font-mono); color:var(--text-dim); padding: 6px 2px;">Нет подключений</div>`;
      return;
    }
    list.innerHTML = connectedDBs.map(db => `
      <div class="db-entry ${db.id === activeDBId ? 'db-entry-active' : ''}"
           onclick="selectDB(${db.id})"
           style="
             border-radius: 6px;
             border: 1px solid ${db.id === activeDBId ? 'var(--border-hi)' : 'transparent'};
             background: ${db.id === activeDBId ? 'var(--bg-hover)' : 'transparent'};
             margin-bottom: 4px; cursor: pointer; transition: all 0.15s;
           ">
        <div style="display:flex; align-items:center; gap:8px; padding: 8px 10px;">
          <span class="status-dot online" style="width:6px;height:6px; flex-shrink:0;"></span>
          <div style="flex:1; overflow:hidden;">
            <div style="font-size:12px; font-family:var(--font-mono); font-weight:700; color:var(--text); text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">${db.name}</div>
            <div style="font-size:10px; font-family:var(--font-mono); color:var(--text-dim);">${db.config.db_type} · ${db.host}</div>
          </div>
          <button onclick="event.stopPropagation(); disconnectDB(${db.id})"
            style="background:none; border:none; color:var(--text-dim); cursor:pointer; font-size:13px; padding:0 2px; line-height:1; transition:color 0.15s;"
            title="Отключить"
            onmouseover="this.style.color='#ff6b6b'"
            onmouseout="this.style.color='var(--text-dim)'">✕</button>
        </div>
      </div>
    `).join('');
  }

  window.selectDB = function(id) {
    activeDBId = id;
    renderDBList();
  };

  window.disconnectDB = function(id) {
    const idx = connectedDBs.findIndex(d => d.id === id);
    if (idx === -1) return;
    const name = connectedDBs[idx].name;
    connectedDBs.splice(idx, 1);
    if (activeDBId === id) {
      activeDBId = connectedDBs.length > 0 ? connectedDBs[connectedDBs.length - 1].id : null;
    }
    renderDBList();
    if (connectedDBs.length === 0 && executeSection) {
      executeSection.style.display = 'none';
      if (resultsSection) resultsSection.style.display = 'none';
    }
    showToast(`БД «${name}» отключена`, 'info');
  };
}

/* ── BOOT ───────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initIndex();
  initAuth();
  initWorkshop();
});