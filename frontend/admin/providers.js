const API_KEY_STORAGE = 'sagpt-provider-admin-key';

const STATUS_LABELS = {
  pending: '待审核',
  contacted: '已联系',
  approved: '已通过',
  rejected: '已拒绝',
};

const state = {
  apiKey: localStorage.getItem(API_KEY_STORAGE) || '',
  page: 1,
  pageSize: 50,
  total: 0,
  providers: [],
  selectedId: null,
};

const nodes = {
  loginView: document.getElementById('login-view'),
  dashboardView: document.getElementById('dashboard-view'),
  apiKeyInput: document.getElementById('api-key-input'),
  loginButton: document.getElementById('login-button'),
  loginError: document.getElementById('login-error'),
  refreshButton: document.getElementById('refresh-button'),
  exportButton: document.getElementById('export-button'),
  logoutButton: document.getElementById('logout-button'),
  demandsButton: document.getElementById('demands-button'),
  searchInput: document.getElementById('search-input'),
  statusFilter: document.getElementById('status-filter'),
  countryFilter: document.getElementById('country-filter'),
  filterButton: document.getElementById('filter-button'),
  clearButton: document.getElementById('clear-button'),
  errorBanner: document.getElementById('error-banner'),
  tableBody: document.getElementById('provider-table-body'),
  emptyState: document.getElementById('empty-state'),
  pageSummary: document.getElementById('page-summary'),
  prevButton: document.getElementById('prev-button'),
  nextButton: document.getElementById('next-button'),
  detailPanel: document.getElementById('detail-panel'),
  detailPlaceholder: document.getElementById('detail-placeholder'),
  detailContent: document.getElementById('detail-content'),
  closeDetailButton: document.getElementById('close-detail-button'),
  detailName: document.getElementById('detail-name'),
  detailCreated: document.getElementById('detail-created'),
  detailStatus: document.getElementById('detail-status'),
  detailEmail: document.getElementById('detail-email'),
  detailExperience: document.getElementById('detail-experience'),
  detailCountries: document.getElementById('detail-countries'),
  detailCategories: document.getElementById('detail-categories'),
  detailBio: document.getElementById('detail-bio'),
  detailPortfolio: document.getElementById('detail-portfolio'),
  statusForm: document.getElementById('status-form'),
  statusSelect: document.getElementById('status-select'),
  reviewedByInput: document.getElementById('reviewed-by-input'),
  reviewNotesInput: document.getElementById('review-notes-input'),
  saveStatusButton: document.getElementById('save-status-button'),
  statusMessage: document.getElementById('status-message'),
  statTotal: document.getElementById('stat-total'),
  statPending: document.getElementById('stat-pending'),
  statContacted: document.getElementById('stat-contacted'),
  statApproved: document.getElementById('stat-approved'),
  statRejected: document.getElementById('stat-rejected'),
};

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));
}

function showError(message) {
  nodes.errorBanner.textContent = message;
  nodes.errorBanner.classList.remove('hidden');
}

function clearError() {
  nodes.errorBanner.textContent = '';
  nodes.errorBanner.classList.add('hidden');
}

function authHeaders() {
  return { 'X-API-Key': state.apiKey };
}

async function apiFetch(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });

  if (response.status === 401 || response.status === 403) {
    throw new Error('API Key 无效或权限不足');
  }

  if (!response.ok) {
    let message = `请求失败：HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = data.message || data.detail || message;
    } catch (_error) {
      // Keep default HTTP message.
    }
    throw new Error(message);
  }

  return response;
}

function showDashboard() {
  nodes.loginView.classList.add('hidden');
  nodes.dashboardView.classList.remove('hidden');
}

function showLogin(message = '') {
  nodes.dashboardView.classList.add('hidden');
  nodes.loginView.classList.remove('hidden');
  nodes.loginError.textContent = message;
}

function statusLabel(status) {
  return STATUS_LABELS[status] || status || '未知';
}

function formatList(values) {
  if (!Array.isArray(values) || values.length === 0) return '-';
  return values.join('、');
}

function formatDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', { hour12: false });
}

function currentFilters() {
  const params = new URLSearchParams({
    page: String(state.page),
    page_size: String(state.pageSize),
  });

  const search = nodes.searchInput.value.trim();
  const status = nodes.statusFilter.value;
  const country = nodes.countryFilter.value.trim();

  if (search) params.set('search', search);
  if (status) params.set('status', status);
  if (country) params.set('country', country);

  return params;
}

function renderStats(stats) {
  nodes.statTotal.textContent = stats.total || 0;
  nodes.statPending.textContent = stats.pending || 0;
  nodes.statContacted.textContent = stats.contacted || 0;
  nodes.statApproved.textContent = stats.approved || 0;
  nodes.statRejected.textContent = stats.rejected || 0;
}

function renderTable() {
  nodes.tableBody.innerHTML = state.providers.map((provider) => {
    const selected = provider.id === state.selectedId ? ' class="selected"' : '';
    return `
      <tr data-id="${escapeHtml(provider.id)}"${selected}>
        <td>${escapeHtml(formatDate(provider.created_at))}</td>
        <td>${escapeHtml(provider.name || '-')}</td>
        <td>${escapeHtml(provider.email || '-')}</td>
        <td>${escapeHtml(formatList(provider.target_countries))}</td>
        <td>${escapeHtml(formatList(provider.service_categories))}</td>
        <td><span class="status-badge status-${escapeHtml(provider.status || 'pending')}">${escapeHtml(statusLabel(provider.status))}</span></td>
      </tr>
    `;
  }).join('');

  const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
  nodes.pageSummary.textContent = `第 ${state.page} / ${totalPages} 页，共 ${state.total} 条`;
  nodes.prevButton.disabled = state.page <= 1;
  nodes.nextButton.disabled = state.page >= totalPages;
  nodes.emptyState.classList.toggle('hidden', state.providers.length > 0);
}

function renderDetail() {
  const provider = state.providers.find((item) => item.id === state.selectedId);

  nodes.detailPlaceholder.classList.toggle('hidden', Boolean(provider));
  nodes.detailContent.classList.toggle('hidden', !provider);
  nodes.detailPanel.classList.toggle('open', Boolean(provider));

  if (!provider) return;

  nodes.detailName.textContent = provider.name || '-';
  nodes.detailCreated.textContent = formatDate(provider.created_at);
  nodes.detailStatus.innerHTML = `<span class="status-badge status-${escapeHtml(provider.status || 'pending')}">${escapeHtml(statusLabel(provider.status))}</span>`;
  nodes.detailEmail.textContent = provider.email || '-';
  nodes.detailExperience.textContent = provider.experience_years ? `${provider.experience_years} 年` : '-';
  nodes.detailCountries.textContent = formatList(provider.target_countries);
  nodes.detailCategories.textContent = formatList(provider.service_categories);
  nodes.detailBio.textContent = provider.bio || '-';
  nodes.detailPortfolio.textContent = provider.portfolio || '-';
  nodes.statusSelect.value = provider.status || 'pending';
  nodes.reviewedByInput.value = provider.reviewed_by || '';
  nodes.reviewNotesInput.value = provider.review_notes || '';
  nodes.statusMessage.textContent = '';
}

async function loadStats() {
  const response = await apiFetch('/api/providers/admin/stats');
  renderStats(await response.json());
}

async function loadApplications() {
  clearError();
  const response = await apiFetch(`/api/providers/admin/list?${currentFilters().toString()}`);
  const data = await response.json();
  state.providers = data.applications || [];
  state.total = data.total || 0;

  if (!state.providers.some((item) => item.id === state.selectedId)) {
    state.selectedId = state.providers[0]?.id || null;
  }

  renderTable();
  renderDetail();
}

async function loadAll() {
  try {
    await Promise.all([loadStats(), loadApplications()]);
  } catch (error) {
    showError(error.message || '加载失败');
    if (/API Key/.test(error.message || '')) showLogin(error.message);
  }
}

async function saveStatus(event) {
  event.preventDefault();
  if (!state.selectedId) return;

  nodes.saveStatusButton.disabled = true;
  nodes.statusMessage.textContent = '保存中...';

  try {
    const response = await apiFetch(`/api/providers/admin/${encodeURIComponent(state.selectedId)}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: nodes.statusSelect.value,
        reviewed_by: nodes.reviewedByInput.value.trim() || null,
        review_notes: nodes.reviewNotesInput.value.trim() || null,
      }),
    });

    const updated = await response.json();
    state.providers = state.providers.map((provider) => (
      provider.id === updated.id ? updated : provider
    ));
    nodes.statusMessage.textContent = '已保存';
    renderTable();
    renderDetail();
    await loadStats();
  } catch (error) {
    nodes.statusMessage.textContent = error.message || '保存失败';
  } finally {
    nodes.saveStatusButton.disabled = false;
  }
}

async function exportCsv() {
  try {
    const response = await apiFetch(`/api/providers/admin/export.csv?${currentFilters().toString()}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sagpt-providers-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    showError(error.message || '导出失败');
  }
}

nodes.loginButton.addEventListener('click', () => {
  const key = nodes.apiKeyInput.value.trim();
  if (!key) {
    nodes.loginError.textContent = '请输入 API Key';
    return;
  }
  state.apiKey = key;
  localStorage.setItem(API_KEY_STORAGE, key);
  showDashboard();
  loadAll();
});

nodes.apiKeyInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') nodes.loginButton.click();
});

nodes.refreshButton.addEventListener('click', loadAll);
nodes.exportButton.addEventListener('click', exportCsv);
nodes.logoutButton.addEventListener('click', () => {
  localStorage.removeItem(API_KEY_STORAGE);
  state.apiKey = '';
  state.providers = [];
  state.selectedId = null;
  showLogin();
});
nodes.demandsButton.addEventListener('click', () => {
  window.location.href = '/admin/demands';
});
nodes.filterButton.addEventListener('click', () => {
  state.page = 1;
  loadAll();
});
nodes.clearButton.addEventListener('click', () => {
  nodes.searchInput.value = '';
  nodes.statusFilter.value = '';
  nodes.countryFilter.value = '';
  state.page = 1;
  loadAll();
});
nodes.prevButton.addEventListener('click', () => {
  if (state.page > 1) {
    state.page -= 1;
    loadAll();
  }
});
nodes.nextButton.addEventListener('click', () => {
  if (state.page * state.pageSize < state.total) {
    state.page += 1;
    loadAll();
  }
});
nodes.tableBody.addEventListener('click', (event) => {
  const row = event.target.closest('tr[data-id]');
  if (!row) return;
  state.selectedId = row.dataset.id;
  renderTable();
  renderDetail();
});
nodes.closeDetailButton.addEventListener('click', () => {
  state.selectedId = null;
  renderDetail();
});
nodes.statusForm.addEventListener('submit', saveStatus);

if (state.apiKey) {
  nodes.apiKeyInput.value = state.apiKey;
  showDashboard();
  loadAll();
} else {
  showLogin();
}
