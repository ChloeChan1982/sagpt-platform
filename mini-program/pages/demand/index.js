const api = require("../../utils/api");
const config = require("../../utils/config");
const draft = require("../../utils/draft");

const EMPTY_ATTACHMENT_LIST = [];

Page({
  data: {
    error: "",
    submitting: false,
    improving: false,
    attachments: EMPTY_ATTACHMENT_LIST,
    industries: ["电商", "制造业", "软件", "专业服务", "新能源", "其他"],
    scenarios: ["投资设立", "市场进入", "合规咨询", "税务筹划", "本地服务商对接", "其他"],
    budgets: ["¥10,000 - ¥100,000", "¥100,000 - ¥1,000,000", "¥1,000,000以上", "待评估"],
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
      wx.showModal({
        title: "使用 AI 优化描述？",
        content: data.suggestion,
        confirmText: "替换",
        cancelText: "保留原文",
        success: (result) => {
          if (result.confirm) {
            this.updateForm({
              ...this.data.form,
              description: data.suggestion
            });
          }
        }
      });
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
            if (file.size > 20 * 1024 * 1024) {
              throw new Error("单个附件不能超过20MB");
            }
            const attachment = await api.uploadAttachment(file.path, file.name);
            uploaded.push(attachment);
          }
          this.setData({
            attachments: this.data.attachments.concat(uploaded),
            error: ""
          });
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

  validateForm() {
    const form = this.data.form;
    const required = [
      ["company_name", "请填写公司名称"],
      ["target_country", "请填写目标国家"],
      ["industry", "请选择行业"],
      ["scenario", "请选择服务场景"],
      ["budget_range", "请选择预算范围"],
      ["description", "请填写需求描述"],
      ["wechat_phone", "请填写微信或手机号"],
      ["phone", "请填写联系电话"]
    ];
    for (const [field, message] of required) {
      if (!form[field]) {
        return message;
      }
    }
    if (form.description.length < 10) {
      return "需求描述至少10个字";
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
      await this.requestSubscriptions();
      const demand = await api.request({
        url: "/demands",
        method: "POST",
        data: {
          ...form,
          client_request_id: form.client_request_id,
          attachment_ids: this.data.attachments.map((item) => item.attachment_id)
        }
      });
      draft.clearDraft();
      wx.showToast({ title: "提交成功", icon: "success" });
      this.setData({
        attachments: [],
        form: draft.createEmptyDraft()
      });
      wx.navigateTo({ url: `/pages/demand-detail/index?id=${demand.id}` });
    } catch (err) {
      this.setData({ error: err.message || "提交失败" });
    } finally {
      this.setData({ submitting: false });
    }
  }
});
