const api = require("../../utils/api");
const draft = require("../../utils/draft");

Page({
  data: {
    error: "",
    submitting: false,
    industries: ["软件", "电商", "制造", "专业服务", "消费品", "其他"],
    scenarios: ["市场进入", "合规咨询", "投资设立", "税务筹划", "本地服务商对接", "其他"],
    budgets: ["¥10,000 - ¥100,000", "¥100,000 - ¥1,000,000", "¥1,000,000以上", "待确定"],
    form: draft.createEmptyDraft()
  },

  onLoad() {
    this.setData({ form: draft.loadDraft() });
  },

  onShow() {
    if (!wx.getStorageSync("sagpt_token")) {
      wx.redirectTo({ url: "/pages/login/index" });
    }
  },

  updateForm(nextForm) {
    this.setData({ form: nextForm });
    draft.saveDraft(nextForm);
  },

  onInput(event) {
    const field = event.currentTarget.dataset.field;
    this.updateForm({
      ...this.data.form,
      [field]: event.detail.value
    });
  },

  onIndustryChange(event) {
    this.updateForm({
      ...this.data.form,
      industry: this.data.industries[event.detail.value]
    });
  },

  onScenarioChange(event) {
    this.updateForm({
      ...this.data.form,
      scenario: this.data.scenarios[event.detail.value]
    });
  },

  onBudgetChange(event) {
    this.updateForm({
      ...this.data.form,
      budget_range: this.data.budgets[event.detail.value]
    });
  },

  onPrivacyChange(event) {
    this.updateForm({
      ...this.data.form,
      privacy_accepted: event.detail.value.includes("accepted")
    });
  },

  openPrivacy() {
    wx.navigateTo({ url: "/pages/privacy/index" });
  },

  async bindPhone(event) {
    const code = event.detail && event.detail.code;
    if (!code) return;
    try {
      const data = await api.request({
        url: "/profile/phone",
        method: "POST",
        data: { code }
      });
      this.updateForm({
        ...this.data.form,
        phone: data.phone,
        wechat_phone: data.phone
      });
    } catch (err) {
      this.setData({ error: err.message || "获取手机号失败" });
    }
  },

  validateForm() {
    const form = this.data.form;
    const required = [
      ["company_name", "请填写公司名称"],
      ["target_country", "请填写目标国家"],
      ["industry", "请选择行业"],
      ["scenario", "请选择服务场景"],
      ["budget_range", "请选择预算范围"],
      ["description", "请填写咨询事项说明"],
      ["wechat_phone", "请填写联系微信或手机号"],
      ["phone", "请填写联系电话"]
    ];
    for (const [field, message] of required) {
      if (!form[field]) {
        return message;
      }
    }
    if (form.description.length < 10) {
      return "咨询事项说明至少10个字";
    }
    if (!form.privacy_accepted) {
      return "请先阅读并同意隐私政策";
    }
    return "";
  },

  async submitDemand() {
    if (this.data.submitting) return;
    const validationError = this.validateForm();
    if (validationError) {
      this.setData({ error: validationError });
      return;
    }

    const form = this.data.form;
    this.setData({ submitting: true, error: "" });
    try {
      const demand = await api.request({
        url: "/demands",
        method: "POST",
        data: {
          ...form,
          client_request_id: form.client_request_id
        }
      });
      draft.clearDraft();
      wx.showToast({ title: "已提交", icon: "success" });
      this.setData({ form: draft.createEmptyDraft() });
      wx.navigateTo({ url: `/pages/demand-detail/index?id=${demand.id}` });
    } catch (err) {
      this.setData({ error: err.message || "提交失败" });
    } finally {
      this.setData({ submitting: false });
    }
  }
});
