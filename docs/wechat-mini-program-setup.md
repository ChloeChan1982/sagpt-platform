# SAGPT 微信小程序接入说明

## 功能范围

小程序只面向中国企业客户：

- 微信登录后发布出海服务需求。
- 可授权手机号，也可手动填写微信/手机号。
- 可上传 PDF、Word、Excel、图片附件。
- 可调用后端 AI 优化需求描述。
- 可查看自己提交过的需求状态。
- 可授权订阅消息；后台把需求状态改成 `contacted` 或 `completed` 时，后端会尝试发送微信订阅通知。

海外专家注册、会员中心、Stripe 收费不放入小程序。

## 微信公众平台配置

在微信公众平台小程序后台配置：

- request 合法域名：`https://api.sagpt.com`
- uploadFile 合法域名：`https://api.sagpt.com`
- downloadFile 合法域名：`https://api.sagpt.com`

然后创建两个订阅消息模板：

- 需求已联系通知：填入 Render 环境变量 `WECHAT_CONTACTED_TEMPLATE_ID`
- 需求已完成通知：填入 Render 环境变量 `WECHAT_COMPLETED_TEMPLATE_ID`

模板字段建议至少包含：

- `thing1`：需求或公司名称
- `phrase2`：状态
- `thing3`：目标国家

## Render 后端环境变量

在 `sagpt-api` 服务里设置：

- `WECHAT_APP_ID`：小程序 AppID
- `WECHAT_APP_SECRET`：小程序 AppSecret
- `WECHAT_CONTACTED_TEMPLATE_ID`：需求已联系订阅消息模板 ID
- `WECHAT_COMPLETED_TEMPLATE_ID`：需求已完成订阅消息模板 ID
- `UPLOAD_DIR`：建议保持 `/var/data/sagpt-uploads`

修改后点 `Save, rebuild, and deploy`。

## 小程序项目配置

用微信开发者工具打开：

`mini-program/`

首次打开后修改：

- `mini-program/project.config.json` 里的 `appid`
- `mini-program/utils/config.js` 里的两个模板 ID

## 后端接口

小程序调用的接口都在：

`https://api.sagpt.com/api/mini`

主要接口：

- `POST /auth/login`
- `GET /me`
- `POST /profile/phone`
- `POST /subscriptions/grant`
- `POST /attachments`
- `GET /attachments/{attachment_id}`
- `POST /demands/improve`
- `POST /demands`
- `GET /demands`
- `GET /demands/{demand_id}`

## 上线前检查

- 微信开发者工具里可以完成微信登录。
- 提交需求后，后台 `https://api.sagpt.com/admin/demands` 能立即看到记录。
- 后台下载 CSV 能包含最新需求。
- 后台把需求状态改为“已联系”或“已完成”后，Stripe 相关功能不受影响，小程序用户在授权订阅消息后可收到通知。
