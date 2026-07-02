const config = require("./config");

function token() {
  return wx.getStorageSync("sagpt_token") || "";
}

function request({ url, method = "GET", data }) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${config.apiBaseUrl}${url}`,
      method,
      data,
      header: {
        Authorization: `Bearer ${token()}`,
        "Content-Type": "application/json"
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
          return;
        }
        reject(new Error((res.data && res.data.detail) || "\u8bf7\u6c42\u5931\u8d25"));
      },
      fail() {
        reject(new Error("\u7f51\u7edc\u8fde\u63a5\u5931\u8d25"));
      }
    });
  });
}

module.exports = {
  request
};
