const api = require("../../utils/api");
const config = require("../../utils/config");

function requestId() {
  return `wx-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

Page({
  data: {
    error: "",
    submitting: false,
    improving: false,
    attachments: [],
    industries: ["电商", "制造业", "软件", "专业服务", "新能源", "其他"],
    scenarios: ["投资设立", "市场进入", "合规咨询", "税务筹划", "本地服务商对接", "其他"],
    budgets: ["¥10,000 - ¥100,000", "¥100,000 - ¥1,000,000", "¥1,000,000以上", "待评估"],
    form: {
      company_name: "",
      target_country: "",
      industry: "",
      scenario: "",
      budget_range: "",
      urgency: "normal",
      description: "",
      email: "",
      wechat_phone: "",
      phone: ""
    }
  },

  onShow() {
    if (!wx.getStorageSync("sagpt_token")) {
      wx.redirectTo({ url: "/pages/login/index" });
    }
  },

  onInput(event) {
    const field = event.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: event.detail.value });
  },

  onIndustryChange(event) {
    this.setData({ "form.industry": this.data.industries[event.detail.value] });
  },

  onScenarioChange(event) {
    this.setData({ "form.scenario": this.data.scenarios[event.detail.value] });
  },

  onBudgetChange(event) {
    this.setData({ "form.budget_range": this.data.budgets[event.detail.value] });
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
      this.setData({
        "form.phone": data.phone,
        "form.wechat_phone": data.phone
      });
    } catch (err) {
      this.setData({ error: err.message || "手机号授权失败" });
    }
  },

  async improveDescription() {
    const form = this.data.form;
    if (!form.description || form.description.length < 10) {
      this.setData({ error: "请先填写至少10个字的需求描述" });
      return;
    }
    this.setData({ improving: true, error: "" });
    try {
      const data = await api.request({
        url: "/demands/improve",
        method: "POST",
        data: {
          target_country: form.target_country || "待确认",
          industry: form.industry || "待确认",
          scenario: form.scenario || "待确认",
          budget_range: form.budget_range || "待评估",
          description: form.description
        }
      });
      this.setData({ "form.description": data.suggestion });
    } catch (err) {
      this.setData({ error: err.message || "AI 优化失败" });
    } finally {
      this.setData({ improving: false });
    }
  },

  chooseAttachment() {
    if (this.data.attachments.length >= 3) {
      this.setData({ error: "最多上传3个附件" });
      return;
    }
    wx.chooseMessageFile({
      count: 3 - this.data.attachments.length,
      type: "file",
      success: async ({ tempFiles }) => {
        try {
          const uploaded = [];
          for (const file of tempFiles) {
            const attachment = await api.uploadAttachment(file.path, file.name);
            uploaded.push(attachment);
          }
          this.setData({ attachments: this.data.attachments.concat(uploaded), error: "" });
        } catch (err) {
          this.setData({ error: err.message || "附件上传失败" });
        }
      }
    });
  },

  async requestSubscriptions() {
    const tmplIds = [config.contactedTemplateId, config.completedTemplateId].filter(
      (id) => id && !id.includes("替换")
    );
    if (!tmplIds.length) return;

    try {
      const result = await new Promise((resolve, reject) => {
        wx.requestSubscribeMessage({
          tmplIds,
          success: resolve,
          fail: reject
        });
      });
      for (const id of tmplIds) {
        if (result[id] === "accept") {
          await api.request({
            url: "/subscriptions/grant",
            method: "POST",
            data: { template_id: id, accepted: true }
          });
        }
      }
    } catch (err) {
      console.warn("subscription skipped", err);
    }
  },

  async submitDemand() {
    const form = this.data.form;
    const required = ["company_name", "target_country", "industry", "scenario", "budget_range", "description", "wechat_phone", "phone"];
    for (const field of required) {
      if (!form[field]) {
        this.setData({ error: "请完整填写必填项" });
        return;
      }
    }

    this.setData({ submitting: true, error: "" });
    try {
      await this.requestSubscriptions();
      await api.request({
        url: "/demands",
        method: "POST",
        data: {
          ...form,
          client_request_id: requestId(),
          attachment_ids: this.data.attachments.map((item) => item.attachment_id)
        }
      });
      wx.showToast({ title: "提交成功", icon: "success" });
      this.setData({
        attachments: [],
        form: {
          company_name: "",
          target_country: "",
          industry: "",
          scenario: "",
          budget_range: "",
          urgency: "normal",
          description: "",
          email: "",
          wechat_phone: "",
          phone: ""
        }
      });
      wx.switchTab({ url: "/pages/demands/index" });
    } catch (err) {
      this.setData({ error: err.message || "提交失败" });
    } finally {
      this.setData({ submitting: false });
    }
  }
});
