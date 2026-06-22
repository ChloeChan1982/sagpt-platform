const api = require("../../utils/api");

Page({
  data: {
    demand: null,
    error: "",
    statusText: {
      pending: "待处理",
      matching: "匹配中",
      contacted: "已联系",
      completed: "已完成",
      closed: "已关闭"
    }
  },

  onLoad(options) {
    this.loadDemand(options.id);
  },

  async loadDemand(id) {
    try {
      const demand = await api.request({ url: `/demands/${id}` });
      this.setData({ demand });
    } catch (err) {
      this.setData({ error: err.message || "加载失败" });
    }
  }
});
