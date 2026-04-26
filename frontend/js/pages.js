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
        <button class="btn btn-primary btn-sm" onclick="goToWorkshop()">Мастерская →</button>
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
      goToWorkshop();
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
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return showAlert('login', 'Введите корректный email');
    if (pass.length < 8) return showAlert('login', 'Пароль должен быть минимум 8 символов');
    clearAlert('login');
    const btn = document.getElementById('login-btn');
    btn.disabled = true; btn.textContent = 'Вход...';
    try {
      const { user } = await api.login(email, pass);
      auth.setSession(user);
      goToWorkshop();
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
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return showAlert('register', 'Введите корректный email');
    if (pass.length < 8) return showAlert('register', 'Пароль должен быть минимум 8 символов');
    clearAlert('register');
    const btn = document.getElementById('register-btn');
    btn.disabled = true; btn.textContent = 'Регистрация...';
    try {
      const { user } = await api.register(name, email, pass);
      auth.setSession(user);
      // Сохраняем полный AuthResponse для страницы верификации
      localStorage.setItem('sqlcraft_user', JSON.stringify(user));
      window.location.href = 'verify.html';
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

  // User card
  api.getMe().then(me => {
    if (!me.is_logged) return;
    const nameEl   = document.getElementById('user-name');
    const planEl   = document.getElementById('user-plan');
    const avatarEl = document.getElementById('user-avatar');
    if (nameEl)   nameEl.textContent   = me.name || '';
    if (planEl)   planEl.textContent   = me.plan || 'free';
    if (avatarEl) avatarEl.textContent = (me.name || '?')[0].toUpperCase();
  }).catch(() => {});

  let currentSQL  = '';
  let lastResults = null;
  let activeDBId  = null;   // id БД (из DbConnectResponse)
  let dbs         = [];     // список DbConnectResponse

  const promptTextarea = document.getElementById('prompt-textarea');
  const generateBtn    = document.getElementById('generate-btn');
  const sqlEditor      = document.getElementById('sql-output-body');
  const execBtn        = document.getElementById('exec-sql-btn');
  const executeSection = document.getElementById('execute-section');
  const resultsSection = document.getElementById('results-section');

  function getActiveDB() { return dbs.find(d => d.id === activeDBId) || null; }

  /* ── DIALECT ── */
  const dialectBtn  = document.getElementById('dialect-btn');
  const dialectDrop = document.getElementById('dialect-dropdown');
  const dialect = dialectBtn && dialectDrop ? new DialectSelector(dialectBtn, dialectDrop) : null;

  /* ── DB LIST ── */
  function renderDBList() {
    const list = document.getElementById('db-list');
    const label = document.getElementById('active-db-label');
    if (!list) return;

    if (dbs.length === 0) {
      list.innerHTML = '<div style="font-size:12px; font-family:var(--font-mono); color:var(--text-dim); padding:6px 2px;">Нет подключений</div>';
      if (label) label.textContent = 'База данных не выбрана';
      return;
    }

    list.innerHTML = dbs.map(db => {
      const isSelected = db.id === activeDBId;
      const dot = db.is_active
        ? '<span class="db-status-dot active"></span>'
        : '<span class="db-status-dot inactive"></span>';
      const sessionBanner = !db.is_active ? `
        <div class="db-session-banner">
          <span>Сессия не активна</span>
          <button onclick="event.stopPropagation(); openSessionModal(${db.id}, '${db.db_alias}')">Активировать</button>
        </div>` : '';
      return `
        <div class="db-item ${isSelected ? 'selected' : ''}" onclick="selectDB(${db.id})">
          <div class="db-item-row">
            ${dot}
            <div class="db-item-info">
              <div class="db-item-alias">${db.db_alias}</div>
              <div class="db-item-meta">${db.db_name}</div>
            </div>
            <div class="db-item-actions">
              <button class="db-action-btn danger" title="Удалить"
                onclick="event.stopPropagation(); deleteDB(${db.id})">✕</button>
            </div>
          </div>
          ${sessionBanner}
        </div>`;
    }).join('');

    const active = getActiveDB();
    if (label) label.textContent = active
      ? `${active.db_alias} ${active.is_active ? '· активна' : '· нет сессии'}`
      : 'База данных не выбрана';
  }

  window.selectDB = function(id) {
    activeDBId = id;
    renderDBList();
  };

  window.deleteDB = async function(id) {
    if (!confirm('Удалить эту базу данных?')) return;
    try {
      await api.deleteDB(id);
      dbs = dbs.filter(d => d.id !== id);
      if (activeDBId === id) activeDBId = dbs.length ? dbs[0].id : null;
      renderDBList();
      showToast('БД удалена', 'info');
    } catch {
      showToast('Не удалось удалить БД', 'error');
    }
  };

  /* ── SESSION MODAL ── */
  let pendingSessionId = null;
  const sessionModal = document.getElementById('session-modal');

  window.openSessionModal = function(dbId, alias) {
    pendingSessionId = dbId;
    const nameEl = document.getElementById('session-db-name');
    if (nameEl) nameEl.textContent = alias;
    const passEl = document.getElementById('session-password');
    if (passEl) passEl.value = '';
    sessionModal?.classList.add('open');
  };
  window.closeSessionModal = function() {
    sessionModal?.classList.remove('open');
    pendingSessionId = null;
  };

  document.getElementById('session-submit')?.addEventListener('click', async () => {
    const pass = document.getElementById('session-password')?.value;
    if (!pass) return showToast('Введите пароль', 'error');
    const btn = document.getElementById('session-submit');
    btn.disabled = true; btn.textContent = 'Подключение...';
    try {
      await api.startSession(pendingSessionId, pass);
      // Обновляем is_active у нужной БД
      const db = dbs.find(d => d.id === pendingSessionId);
      if (db) db.is_active = true;
      renderDBList();
      closeSessionModal();
      showToast('Сессия активирована', 'success');
    } catch (err) {
      showToast(err.message || 'Ошибка активации', 'error');
    } finally {
      btn.disabled = false; btn.textContent = 'Активировать';
    }
  });

  /* ── ADD DB MODAL ── */
  const dbModal = document.getElementById('db-modal');
  window.openDBModal  = () => dbModal?.classList.add('open');
  window.closeDBModal = () => dbModal?.classList.remove('open');

  document.getElementById('db-connect-btn')?.addEventListener('click', openDBModal);

  document.getElementById('db-connect-submit')?.addEventListener('click', async () => {
    const alias  = document.getElementById('db-alias')?.value?.trim();
    const dbName = document.getElementById('db-database-name')?.value?.trim();
    const host   = document.getElementById('db-host')?.value?.trim() || 'localhost';
    if (!alias)  return showToast('Введите псевдоним', 'error');
    if (!dbName) return showToast('Введите имя базы данных', 'error');

    const btn = document.getElementById('db-connect-submit');
    btn.disabled = true; btn.textContent = 'Подключение...';
    try {
      const result = await api.connectDB({
        host,
        port:           document.getElementById('db-port')?.value || '5432',
        database_name:  dbName,
        database_alias: alias,
        db_username:    document.getElementById('db-username')?.value?.trim() || '',
        password:       document.getElementById('db-password')?.value || '',
        dialect:        document.getElementById('db-dialect')?.value || 'postgresql',
        ssl:            document.getElementById('db-ssl')?.checked || false,
      });
      // result = DbConnectResponse {id, db_alias, db_name, is_active}
      dbs.push(result);
      if (!activeDBId) activeDBId = result.id;
      renderDBList();
      closeDBModal();
      showToast(`БД «${result.db_alias}» добавлена!`, 'success');
    } catch (err) {
      showToast(err.message || 'Ошибка подключения', 'error');
    } finally {
      btn.disabled = false; btn.textContent = 'Подключить';
    }
  });

  /* ── LOAD DBs ON START ── */
  async function loadDBs() {
    try {
      dbs = await api.getUserDBs();
      if (dbs.length && !activeDBId) activeDBId = dbs[0].id;
    } catch {
      dbs = [];
    }
    renderDBList();
  }
  loadDBs();

  /* ── HISTORY ── */
  let history = [];

  function formatDate(isoStr) {
    const d = new Date(isoStr);
    return d.toLocaleString('ru-RU', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' });
  }

  function renderHistory() {
    const container = document.getElementById('history-list');
    if (!container) return;
    if (history.length === 0) {
      container.innerHTML = '<div style="font-size:12px; font-family:var(--font-mono); color:var(--text-dim); padding:8px 4px;">История пуста</div>';
      return;
    }
    container.innerHTML = history.map((h, i) => `
      <div class="history-item" data-index="${i}">
        <div class="history-item-query">${h.prompt}</div>
        <div class="history-item-time">${formatDate(h.created_at)}</div>
      </div>`).join('');
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
      document.querySelectorAll('.dialect-option').forEach(opt =>
        opt.classList.toggle('active', opt.dataset.value === h.dialect));
    }
    renderSQL(h.query, h.is_danger);
    document.querySelectorAll('.history-item').forEach((el, j) =>
      el.classList.toggle('active', j === i));
  }

  function addHistoryItem(entry) { history.unshift(entry); renderHistory(); }

  async function loadHistory() {
    try { history = await api.getHistory(); }
    catch { history = []; showToast('Не удалось загрузить историю', 'error'); }
    renderHistory();
  }
  loadHistory();

  /* ── LOGOUT ── */
  document.getElementById('logout-btn')?.addEventListener('click', () => auth.logout());

  /* ── GENERATE ── */
  if (generateBtn && promptTextarea) {
    generateBtn.addEventListener('click', handleGenerate);
    promptTextarea.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') handleGenerate();
    });
  }

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
      addHistoryItem({ prompt, query, is_danger, dialect: dialect ? dialect.value : 'postgresql', created_at: new Date().toISOString() });
      if (is_danger) showToast('⚠️ Запрос может изменить или удалить данные', 'error');
      else showToast('SQL сгенерирован', 'success');
    } catch (err) {
      showToast(err.msg || err.message || 'Ошибка генерации', 'error');
    } finally {
      setGenerating(false);
    }
  }

  function setGenerating(v) {
    if (!generateBtn) return;
    generateBtn.disabled = v;
    generateBtn.innerHTML = v ? '<span>◌</span> Генерация...' : '⚡ Генерировать SQL';
  }

  function renderSQL(sql, is_danger = false) {
    if (sqlEditor) sqlEditor.value = sql;
    currentSQL = sql;
    const badge = document.getElementById('danger-badge');
    if (badge) badge.style.display = is_danger ? 'inline-flex' : 'none';
  }

  /* ── EXECUTE ── */
  if (execBtn) execBtn.addEventListener('click', handleExecute);

  async function handleExecute() {
    const sql = sqlEditor ? sqlEditor.value.trim() : currentSQL;
    if (!sql) { showToast('Сначала введите или сгенерируйте SQL', 'error'); return; }
    const db = getActiveDB();
    if (!db) { showToast('Выберите базу данных', 'error'); return; }
    if (!db.is_active) { showToast('Сначала активируйте сессию для этой БД', 'error'); openSessionModal(db.id, db.db_alias); return; }

    if (execBtn) { execBtn.disabled = true; execBtn.textContent = '▶ Выполнение...'; }
    if (executeSection) executeSection.style.display = 'block';
    if (resultsSection) resultsSection.style.display = 'block';

    try {
      const results = await api.executeSQL(sql, db.id);
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
    const tbody    = document.getElementById('results-tbody');
    const thead    = document.getElementById('results-thead');
    const footer   = document.getElementById('results-footer-info');
    const wrap     = document.getElementById('results-table-wrap');
    const expandBtn = document.getElementById('results-expand-btn');
    if (!tbody || !thead) return;

    thead.innerHTML = results.columns.map(c => `<th>${c}</th>`).join('');
    if (results.rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="99" style="text-align:center; color:var(--text-dim); padding:20px;">Запрос вернул 0 строк</td></tr>';
    } else {
      tbody.innerHTML = results.rows.map(row =>
        `<tr>${row.map(v => `<td class="${v === null ? 'null-val' : ''}">${v === null ? 'NULL' : v}</td>`).join('')}</tr>`
      ).join('');
    }

    // collapse logic
    if (wrap && expandBtn) {
      const total = results.rows.length;
      if (total > 10) {
        wrap.classList.add('collapsed');
        expandBtn.classList.add('visible');
        expandBtn.textContent = `▼ Показать все ${total} строк`;
        expandBtn.onclick = () => {
          wrap.classList.remove('collapsed');
          expandBtn.classList.remove('visible');
        };
      } else {
        wrap.classList.remove('collapsed');
        expandBtn.classList.remove('visible');
      }
    }

    if (footer) footer.textContent = `${results.rowCount} строк`;
  }

  /* ── COPY / EXPORT ── */
  document.getElementById('copy-sql-btn')?.addEventListener('click', () => {
    const sql = sqlEditor?.value || currentSQL;
    if (sql) copyToClipboard(sql); else showToast('Нет SQL для копирования', 'error');
  });
  document.getElementById('export-sql')?.addEventListener('click', () => {
    const sql = sqlEditor?.value || currentSQL;
    if (!sql) return showToast('Нет SQL для экспорта', 'error');
    exportUtils.download('query.sql', sql, 'text/plain');
    showToast('SQL файл скачан', 'success');
  });
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
}


/* ── BOOT ───────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initIndex();
  initAuth();
  initWorkshop();
});