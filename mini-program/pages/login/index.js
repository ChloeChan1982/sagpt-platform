const api = require("../../utils/api");

Page({
  data: {
    loading: false,
    error: ""
  },

  login() {
    this.setData({ loading: true, error: "" });
    wx.login({
      success: async ({ code }) => {
        try {
          const data = await api.request({
            url: "/auth/login",
            method: "POST",
            data: { code }
          });
          wx.setStorageSync("sagpt_token", data.token);
          getApp().globalData.token = data.token;
          wx.switchTab({ url: "/pages/demand/index" });
        } catch (err) {
          this.setData({ error: err.message || "登录失败" });
        } finally {
          this.setData({ loading: false });
        }
      },
      fail: () => {
        this.setData({ loading: false, error: "微信登录失败" });
      }
    });
  }
});
