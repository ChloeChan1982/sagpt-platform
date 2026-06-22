const DRAFT_KEY = "sagpt_demand_draft";

function newClientRequestId() {
  return `wx-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function createEmptyDraft() {
  return {
    client_request_id: newClientRequestId(),
    company_name: "",
    target_country: "",
    industry: "",
    scenario: "",
    budget_range: "",
    urgency: "normal",
    description: "",
    email: "",
    wechat_phone: "",
    phone: "",
    privacy_accepted: false
  };
}

function loadDraft() {
  return wx.getStorageSync(DRAFT_KEY) || createEmptyDraft();
}

function saveDraft(form) {
  wx.setStorageSync(DRAFT_KEY, form);
}

function clearDraft() {
  wx.removeStorageSync(DRAFT_KEY);
}

module.exports = {
  createEmptyDraft,
  loadDraft,
  saveDraft,
  clearDraft
};
