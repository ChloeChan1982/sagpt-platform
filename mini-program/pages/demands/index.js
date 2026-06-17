const api = require("../../utils/api");

Page({
  data: {
    loading: false,
    error: "",
    demands: [],
    statusText: {
      pending: "待处理",
      matching: "匹配中",
      contacted: "已联系",
      completed: "已完成",
      closed: "已关闭"
    }
  },

  onShow() {
    this.loadDemands();
  },

  async loadDemands() {
    this.setData({ loading: true, error: "" });
    try {
      const demands = await api.request({ url: "/demands" });
      this.setData({ demands });
    } catch (err) {
      if ((err.message || "").includes("401")) {
        wx.redirectTo({ url: "/pages/login/index" });
        return;
      }
      this.setData({ error: err.message || "加载失败" });
    } finally {
      this.setData({ loading: false });
    }
  },

  openDetail(event) {
    wx.navigateTo({
      url: `/pages/demand-detail/index?id=${event.currentTarget.dataset.id}`
    });
  }
});
