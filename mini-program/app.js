App({
  globalData: {
    token: "",
    user: null
  },

  onLaunch() {
    const token = wx.getStorageSync("sagpt_token");
    if (token) {
      this.globalData.token = token;
    }
  }
});
