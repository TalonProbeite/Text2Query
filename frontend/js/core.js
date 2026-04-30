/* =====================================================
   SQLCRAFT — core.js
   Общие модули: конфиг, моки, утилиты, auth, api,
   export, подсветка SQL, компонент DialectSelector.
   ===================================================== */

/* ── CONFIG ─────────────────────────────────────────────── */
const API_BASE = '/api/v1';

/* ── MOCK DATA ──────────────────────────────────────────── */


/* ── UTILS ──────────────────────────────────────────────── */
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => showToast('Скопировано в буфер', 'success'));
}

/* ── AUTH MODULE ────────────────────────────────────────── */
const auth = {
  getUser() {
    try { return JSON.parse(localStorage.getItem('sqlcraft_user') || 'null'); }
    catch { return null; }
  },
  setSession(user) {
    localStorage.setItem('sqlcraft_user', JSON.stringify(user));
  },
  async logout() {
    localStorage.removeItem('sqlcraft_user');
    sessionStorage.clear();
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (e) {
      console.warn('Logout request failed:', e);
    }
    window.location.href = 'index.html';
  },
  isLoggedIn() {
    return !!this.getUser();
  },
  requireAuth() {
    if (!this.isLoggedIn()) { this.logout(); return false; }
    return true;
  },
};

/* ── GLOBAL 401 INTERCEPTOR WITH REFRESH ────────────────── */
(function() {
  const _fetch = window.fetch;

  // Маршруты где 401 — норма или сам refresh, не перехватываем
  const SKIP = [
    '/auth/login', '/auth/signup', '/auth/refresh', '/auth/me',
    '/auth/verify_mail', '/auth/update_email',
    '/auth//resend_verification_code',
  ];

  let isRefreshing = false;
  let queue = [];

  function flushQueue(success) {
    queue.forEach(({ resolve, reject }) => success ? resolve() : reject());
    queue = [];
  }

  async function doRefresh() {
    const r = await _fetch('/auth/refresh', { method: 'POST', credentials: 'include' });
    if (!r.ok) return false;
    const d = await r.json().catch(() => ({}));
    return d.success === true;
  }

  window.fetch = async function(...args) {
    const url = args[0].toString();
    if (SKIP.some(s => url.includes(s))) return _fetch(...args);

    const res = await _fetch(...args);
    if (res.status !== 401) return res;

    // Получили 401 — пробуем refresh
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        queue.push({
          resolve: async () => resolve(await _fetch(...args)),
          reject:  () => reject(new Error('Unauthorized')),
        });
      });
    }

    isRefreshing = true;
    const ok = await doRefresh().catch(() => false);
    isRefreshing = false;

    if (ok) {
      flushQueue(true);
      return _fetch(...args); // повторяем оригинальный запрос
    } else {
      flushQueue(false);
      localStorage.removeItem('sqlcraft_user');
      sessionStorage.setItem('auth_error', 'Сессия истекла, войдите снова');
      window.location.href = 'auth.html';
      return res;
    }
  };
})();

/* ── API LAYER ──────────────────────────────────────────── */
const api = {
  async getMe() {
    const res = await fetch('/auth/me', {
      method: 'GET',
      credentials: 'include',
    });
    if (!res.ok) return { is_logged: false };
    return res.json();
  },

  async generateSQL(prompt, dialect) {
    const res = await fetch('/sql/get_sql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ prompt, sql_type: dialect }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      if (res.status === 400) throw { msg: 'Запрос не связан с SQL — попробуйте переформулировать' };
      if (res.status === 502) throw { msg: 'Сервис генерации недоступен, попробуйте позже' };
      throw { msg: data.detail || 'Неизвестная ошибка' };
    }
    const data = await res.json();
    return { query: data.query, is_danger: data.is_danger };
  },

  async executeSQL(sql, dbId) {
    const res = await fetch('/user_db/execute_query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ id: dbId, query: sql }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      if (res.status === 400) throw { msg: data.detail || 'Ошибка выполнения запроса' };
      throw { msg: 'Ошибка сервера при выполнении запроса' };
    }
    const rows = await res.json();
    if (!Array.isArray(rows) || !rows.length) return { columns: [], rows: [], rowCount: 0 };
    const columns = Object.keys(rows[0]);
    return {
      columns,
      rows: rows.map(r => columns.map(c => r[c] ?? null)),
      rowCount: rows.length,
    };
  },

  async getHistory() {
    const res = await fetch('/history/get_history', {
      method: 'GET',
      credentials: 'include',
    });
    if (!res.ok) throw { msg: 'Не удалось загрузить историю' };
    return res.json();
  },

  async connectDB(config) {
    const res = await fetch('/user_db/try_connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        host:            config.host,
        port:            parseInt(config.port),
        database_name:   config.database_name,
        database_alias:  config.database_alias,
        db_username:     config.db_username,
        password:        config.password,
        dialect:         config.dialect,
        ssl:             config.ssl,
      }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      if (res.status === 400) throw new Error(data.detail || 'Не удалось подключиться к БД');
      throw new Error('Ошибка сервера при подключении');
    }
    return await res.json(); // DbConnectResponse {id, db_alias, db_name, is_active}
  },

  async getUserDBs() {
    const res = await fetch('/user_db/get_users_db', {
      method: 'GET',
      credentials: 'include',
    });
    if (!res.ok) throw { msg: 'Не удалось загрузить базы данных' };
    return res.json(); // list[DbConnectResponse]
  },

  async startSession(dbId, password) {
    const res = await fetch('/user_db/start_session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ id: dbId, password }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      if (res.status === 400) throw new Error(data.detail || 'Неверный пароль или ошибка подключения');
      throw new Error('Ошибка сервера');
    }
    return res.json();
  },

  async deleteDB(dbId) {
    // заглушка — ручка ещё не реализована
    return { success: true };
  },

  async login(email, password) {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include',
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const detail = typeof data.detail === 'string' ? data.detail.toLowerCase() : '';
      if (res.status === 401 || detail.includes('incorrect') || detail.includes('password') || detail.includes('email')) {
        throw { msg: 'Неверный email или пароль' };
      }
      if (res.status === 403 || detail.includes('forbidden') || detail.includes('banned')) {
        throw { msg: 'Доступ запрещён' };
      }
      if (res.status === 404 || detail.includes('not found') || detail.includes('user')) {
        throw { msg: 'Пользователь с таким email не найден' };
      }
      if (res.status >= 500) {
        throw { msg: 'Ошибка сервера. Попробуйте позже' };
      }
      throw { msg: data.detail || 'Неизвестная ошибка' };
    }
    const data = await res.json();
    return { user: { id: data.id, name: data.name, email: data.email, plan: data.plan, is_verified: data.is_verified } };
  },

  async register(name, email, password) {
    const res = await fetch('/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
      credentials: 'include',
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const detail = typeof data.detail === 'string' ? data.detail.toLowerCase() : '';
      if (detail.includes('already') || detail.includes('exist') || detail.includes('duplicate') || detail.includes('unique')) {
        throw { msg: 'Этот email уже зарегистрирован' };
      }
      if (detail.includes('email') && detail.includes('invalid')) {
        throw { msg: 'Некорректный формат email' };
      }
      if (detail.includes('password')) {
        throw { msg: 'Пароль не соответствует требованиям' };
      }
      if (res.status === 400) {
        throw { msg: data.detail || 'Регистрация не удалась. Проверьте введённые данные' };
      }
      if (res.status >= 500) {
        throw { msg: 'Ошибка сервера. Попробуйте позже' };
      }
      throw { msg: data.detail || 'Неизвестная ошибка' };
    }
    const data = await res.json();
    return { user: { id: data.id, name: data.name, email: data.email, plan: data.plan, is_verified: data.is_verified } };
  },
};

/* ── DIALECT SELECTOR ───────────────────────────────────── */
class DialectSelector {
  constructor(btnEl, dropEl) {
    this.btn = btnEl;
    this.drop = dropEl;
    this.value = 'postgresql';
    this._setupEvents();
  }
  _setupEvents() {
    this.btn.addEventListener('click', (e) => { e.stopPropagation(); this._toggle(); });
    document.addEventListener('click', () => this._close());
    this.drop.querySelectorAll('.dialect-option').forEach(opt => {
      opt.addEventListener('click', (e) => {
        e.stopPropagation();
        this.value = opt.dataset.value;
        this.btn.querySelector('.dialect-current').textContent = opt.dataset.label;
        this.drop.querySelectorAll('.dialect-option').forEach(o => o.classList.remove('active'));
        opt.classList.add('active');
        this._close();
      });
    });
  }
  _toggle() { this.btn.classList.toggle('open'); this.drop.classList.toggle('open'); }
  _close()  { this.btn.classList.remove('open'); this.drop.classList.remove('open'); }
}

/* ── EXPORT UTILS ───────────────────────────────────────── */
const exportUtils = {
  toCSV(results) {
    const header = results.columns.join(',');
    const rows = results.rows.map(r => r.map(v => v === null ? '' : `"${v}"`).join(','));
    return [header, ...rows].join('\n');
  },
  toJSON(results) {
    const arr = results.rows.map(r => {
      const obj = {};
      results.columns.forEach((c, i) => { obj[c] = r[i]; });
      return obj;
    });
    return JSON.stringify(arr, null, 2);
  },
  download(filename, content, mime) {
    const blob = new Blob([content], { type: mime });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  },
};

/* ── SQL HIGHLIGHTER ────────────────────────────────────── */
function highlightSQL(sql) {
  const keywords = ['SELECT','FROM','WHERE','JOIN','LEFT','RIGHT','INNER','OUTER',
    'ON','GROUP','BY','ORDER','HAVING','LIMIT','OFFSET','INSERT','UPDATE','DELETE',
    'INTO','VALUES','SET','CREATE','TABLE','ALTER','DROP','INDEX','AND','OR','NOT',
    'IN','IS','NULL','AS','DISTINCT','COUNT','SUM','AVG','MIN','MAX','CASE','WHEN',
    'THEN','ELSE','END','WITH','UNION','ALL','INTERVAL','DATE_SUB','NOW','datetime'];
  let out = sql
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  out = out.replace(/'[^']*'/g, m => `<span class="sql-str">${m}</span>`);
  out = out.replace(/(--[^\n]*)/g, `<span class="sql-cmt">$1</span>`);
  const kwRe = new RegExp(`\\b(${keywords.join('|')})\\b`, 'g');
  out = out.replace(kwRe, `<span class="sql-kw">$1</span>`);
  out = out.replace(/\b(\d+)\b/g, `<span class="sql-num">$1</span>`);
  return out;
}