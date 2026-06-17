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
        reject(new Error((res.data && res.data.detail) || "请求失败"));
      },
      fail() {
        reject(new Error("网络连接失败"));
      }
    });
  });
}

function uploadAttachment(filePath, name) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${config.apiBaseUrl}/attachments`,
      filePath,
      name: "file",
      header: {
        Authorization: `Bearer ${token()}`
      },
      formData: { name },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(res.data));
          return;
        }
        reject(new Error("附件上传失败"));
      },
      fail() {
        reject(new Error("附件上传失败"));
      }
    });
  });
}

module.exports = {
  request,
  uploadAttachment
};
