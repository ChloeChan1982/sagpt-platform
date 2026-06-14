const API_KEY_STORAGE = "sagpt_admin_api_key";
const STATUSES = ["pending", "matching", "contacted", "completed", "closed"];
const STATUS_LABELS = {
  pending: "待处理",
  matching: "匹配中",
  contacted: "已联系",
  completed: "已完成",
  closed: "已关闭",
};
const state = {
  page: 1,
  pageSize: 50,
  status: "",
  country: "",
  search: "",
  total: 0,
  demands: [],
  selected: null,
};

const el = (id) => document.getElementById(id);

function apiHeaders(extra = {}) {
  return { "X-API-Key": sessionStorage.getItem(API_KEY_STORAGE) || "", ...extra };
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: apiHeaders(options.headers || {}),
  });
  if (response.status === 401) {
    logout("管理员密钥无效，请重新输入。");
    throw new Error("管理员密钥无效");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.message || body.detail || `请求失败 (${response.status})`);
  }
  return response;
}

function setBusy(button, busy, label) {
  button.disabled = busy;
  if (label) button.textContent = busy ? "处理中..." : label;
}

function showDashboard() {
  el("login-view").classList.add("hidden");
  el("dashboard").classList.remove("hidden");
}

function logout(message = "") {
  sessionStorage.removeItem(API_KEY_STORAGE);
  el("dashboard").classList.add("hidden");
  el("login-view").classList.remove("hidden");
  el("login-error").textContent = message;
  el("api-key").value = "";
}

function queryString() {
  const params = new URLSearchParams({
    page: String(state.page),
    page_size: String(state.pageSize),
  });
  if (state.status) params.set("status", state.status);
  if (state.country) params.set("country", state.country);
  if (state.search) params.set("search", state.search);
  return params.toString();
}

function statusBadge(status) {
  const badge = document.createElement("span");
  badge.className = `status-badge status-${status || "pending"}`;
  badge.textContent = STATUS_LABELS[status] || status || "未知";
  return badge;
}

function renderStats(stats) {
  const items = [["total", "全部需求"], ...STATUSES.map((status) => [status, STATUS_LABELS[status]])];
  el("stats").replaceChildren(...items.map(([key, label]) => {
    const item = document.createElement("div");
    item.className = "stat";
    const caption = document.createElement("span");
    caption.className = "stat-label";
    caption.textContent = label;
    const value = document.createElement("strong");
    value.className = "stat-value";
    value.textContent = String(stats[key] || 0);
    item.append(caption, value);
    return item;
  }));
}

function cell(text) {
  const td = document.createElement("td");
  td.textContent = text ?? "-";
  return td;
}

function renderRows() {
  const rows = state.demands.map((demand) => {
    const row = document.createElement("tr");
    if (state.selected?.id === demand.id) row.classList.add("selected");
    row.append(
      cell(formatDate(demand.created_at)),
      cell(demand.company_name || "未填写公司"),
      cell(demand.target_country),
      cell(demand.industry),
    );
    const status = document.createElement("td");
    status.append(statusBadge(demand.status));
    row.append(status, cell(Number(demand.ai_match_score || 0).toFixed(2)));
    row.addEventListener("click", () => openDetail(demand));
    return row;
  });
  el("demand-rows").replaceChildren(...rows);
  el("empty-state").classList.toggle("hidden", state.demands.length > 0);
  const pages = Math.max(1, Math.ceil(state.total / state.pageSize));
  el("page-summary").textContent = `第 ${state.page} / ${pages} 页，共 ${state.total} 条`;
  el("previous-page").disabled = state.page <= 1;
  el("next-page").disabled = state.page >= pages;
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("zh-CN", { hour12: false });
}

function addDetailPair(container, label, value) {
  const wrapper = document.createElement("div");
  const dt = document.createElement("dt");
  const dd = document.createElement("dd");
  dt.textContent = label;
  dd.textContent = value ?? "-";
  wrapper.append(dt, dd);
  container.append(wrapper);
}

function renderTags(container, values, emptyText) {
  const items = Array.isArray(values) ? values : [];
  container.replaceChildren(...(items.length ? items : [emptyText]).map((value) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = value;
    return tag;
  }));
}

function openDetail(demand) {
  state.selected = demand;
  renderRows();
  const fragment = el("detail-template").content.cloneNode(true);
  fragment.querySelector('[data-field="company_name"]').textContent = demand.company_name || "未填写公司";
  fragment.querySelector('[data-field="description"]').textContent = demand.description || "-";
  const grid = fragment.querySelector(".detail-grid");
  [
    ["提交时间", formatDate(demand.created_at)],
    ["状态", STATUS_LABELS[demand.status] || demand.status],
    ["邮箱", demand.email],
    ["联系电话", demand.phone],
    ["微信/手机", demand.wechat_phone],
    ["目标国家", demand.target_country],
    ["行业", demand.industry],
    ["场景", demand.scenario],
    ["预算", demand.budget_range],
    ["紧急程度", demand.urgency],
    ["AI 匹配分数", Number(demand.ai_match_score || 0).toFixed(2)],
    ["需求 ID", demand.id],
  ].forEach(([label, value]) => addDetailPair(grid, label, value));
  renderTags(fragment.querySelector('[data-field="matched_expert_ids"]'), demand.matched_expert_ids, "暂无匹配专家");
  renderTags(fragment.querySelector('[data-field="attachments"]'), demand.attachments, "暂无附件");
  fragment.querySelector("#detail-status").value = demand.status;
  fragment.querySelector('[data-action="close"]').addEventListener("click", closeDetail);
  fragment.querySelector("#status-form").addEventListener("submit", updateStatus);
  el("detail-panel").replaceChildren(fragment);
  el("detail-panel").classList.add("open");
}

function closeDetail() {
  state.selected = null;
  el("detail-panel").classList.remove("open");
  el("detail-panel").innerHTML = '<div class="detail-placeholder">选择一条需求查看完整信息</div>';
  renderRows();
}

async function updateStatus(event) {
  event.preventDefault();
  if (!state.selected) return;
  const button = el("save-status");
  const message = el("status-message");
  setBusy(button, true, "保存状态");
  message.textContent = "";
  try {
    const response = await apiFetch(`/api/demands/admin/${state.selected.id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: el("detail-status").value }),
    });
    const updated = await response.json();
    state.selected = updated;
    message.textContent = "状态已更新";
    await loadDashboard(false);
    openDetail(updated);
  } catch (error) {
    message.textContent = error.message;
  } finally {
    setBusy(button, false, "保存状态");
  }
}

async function loadDashboard(showError = true) {
  el("page-error").classList.add("hidden");
  try {
    const [statsResponse, listResponse] = await Promise.all([
      apiFetch("/api/demands/admin/stats"),
      apiFetch(`/api/demands/admin/list?${queryString()}`),
    ]);
    const stats = await statsResponse.json();
    const list = await listResponse.json();
    state.total = list.total;
    state.demands = list.demands;
    renderStats(stats);
    renderRows();
  } catch (error) {
    if (showError && sessionStorage.getItem(API_KEY_STORAGE)) {
      el("page-error").textContent = error.message;
      el("page-error").classList.remove("hidden");
    }
    throw error;
  }
}

async function exportCsv() {
  const button = el("export-button");
  setBusy(button, true, "下载 CSV");
  try {
    const params = new URLSearchParams();
    if (state.status) params.set("status", state.status);
    if (state.country) params.set("country", state.country);
    if (state.search) params.set("search", state.search);
    const response = await apiFetch(`/api/demands/admin/export.csv?${params}`);
    const blob = await response.blob();
    const disposition = response.headers.get("content-disposition") || "";
    const match = disposition.match(/filename="([^"]+)"/);
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = match?.[1] || "sagpt-demands.csv";
    link.click();
    URL.revokeObjectURL(link.href);
  } catch (error) {
    el("page-error").textContent = error.message;
    el("page-error").classList.remove("hidden");
  } finally {
    setBusy(button, false, "下载 CSV");
  }
}

el("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = el("login-button");
  el("login-error").textContent = "";
  sessionStorage.setItem(API_KEY_STORAGE, el("api-key").value.trim());
  setBusy(button, true, "进入后台");
  try {
    await loadDashboard(false);
    showDashboard();
  } catch (error) {
    if (sessionStorage.getItem(API_KEY_STORAGE)) logout(error.message);
  } finally {
    setBusy(button, false, "进入后台");
  }
});

el("filters").addEventListener("submit", async (event) => {
  event.preventDefault();
  state.page = 1;
  state.search = el("search").value.trim();
  state.status = el("status-filter").value;
  state.country = el("country-filter").value.trim();
  await loadDashboard();
});
el("clear-filters").addEventListener("click", async () => {
  el("filters").reset();
  Object.assign(state, { page: 1, status: "", country: "", search: "" });
  await loadDashboard();
});
el("refresh-button").addEventListener("click", () => loadDashboard());
el("export-button").addEventListener("click", exportCsv);
el("logout-button").addEventListener("click", () => logout());
el("previous-page").addEventListener("click", async () => { state.page -= 1; await loadDashboard(); });
el("next-page").addEventListener("click", async () => { state.page += 1; await loadDashboard(); });

if (sessionStorage.getItem(API_KEY_STORAGE)) {
  loadDashboard(false).then(showDashboard).catch(() => logout("管理员密钥已失效，请重新输入。"));
}
