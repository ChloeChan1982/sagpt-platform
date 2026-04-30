# SAGPT 后端 - 快速使用指南

## 🎉 恭喜！项目已成功创建！

您的 SAGPT 后端系统已准备就绪！

---

## 📋 项目包含的内容

### ✅ 4 个核心功能模块

1. **需求收集与 AI 匹配引擎** - 收集用户需求，智能匹配服务提供商
2. **AI 合规报告生成器** - 生成中英文合规报告
3. **AI 聊天助手** - 专业的海外扩张咨询
4. **服务提供商管理** - 完整的 CRUD 功能

### ✅ 完整的技术架构

- **后端**: Express.js + Node.js
- **AI**: 火山引擎 Coding Plan API
- **数据库**: SQLite (轻量级，零配置)
- **安全**: CORS, Helmet, 速率限制
- **部署**: Docker 支持

---

## 🚀 三步快速启动

### 第一步：配置 API 密钥

编辑 `.env` 文件，添加您的火山引擎 API 密钥：

```bash
# 找到这一行
VOLCENGINE_API_KEY=your_volcengine_api_key_here

# 替换为您的实际密钥
VOLCENGINE_API_KEY=sk-xxxxxx-xxxxxx-xxxxxx
```

### 第二步：安装依赖

```bash
cd sagpt-backend
npm install
```

（如果还没安装的话）

### 第三步：启动服务器

```bash
# 开发模式（推荐）
npm run dev

# 或生产模式
npm start
```

服务器启动后，访问：
```
http://localhost:3000/api/v1/health
```

---

## 📊 API 使用示例

### 1. 列出服务提供商

```bash
curl -X GET http://localhost:3000/api/v1/providers
```

### 2. 提交用户需求

```bash
curl -X POST http://localhost:3000/api/v1/requests \
  -H "Content-Type: application/json" \
  -d '{
    "targetCountry": "United States",
    "industry": "E-commerce",
    "businessGoal": "setup",
    "budgetRange": "10000-50000",
    "urgency": "high",
    "contactInfo": {
      "companyName": "Example Corp",
      "contactPerson": "Zhang San",
      "email": "zhang@example.com",
      "phone": "+86 13800138000"
    }
  }'
```

### 3. 生成合规报告

```bash
curl -X POST http://localhost:3000/api/v1/reports \
  -H "Content-Type: application/json" \
  -d '{
    "country": "United States",
    "industry": "E-commerce",
    "language": "en"
  }'
```

### 4. 使用聊天助手

```bash
# 创建会话
curl -X POST http://localhost:3000/api/v1/chat/sessions

# 发送消息（替换 session_id）
curl -X POST http://localhost:3000/api/v1/chat/sessions/chat_xxxxxx/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What are the legal requirements for setting up a business in the US?",
    "language": "en"
  }'
```

---

## 📁 项目文件说明

### 核心代码位置

```
sagpt-backend/
├── src/
│   ├── controllers/          # API 业务逻辑
│   ├── services/             # 核心服务
│   ├── routes/               # API 路由定义
│   ├── config/               # 配置文件
│   └── middlewares/          # 中间件
├── .env                      # 环境变量（已创建）
├── package.json              # 项目依赖
├── PROJECT_SUMMARY.md        # 完整项目文档
└── README.md                 # 项目说明
```

### 关键文件

| 文件 | 用途 |
|------|------|
| `.env` | 配置 API 密钥和环境变量 |
| `src/config/volcengine.js` | 火山引擎 API 配置 |
| `src/config/database.js` | 数据库配置 |
| `PROJECT_SUMMARY.md` | 完整的项目文档 |

---

## 🔧 自定义配置

### 修改火山引擎 API 端点

如果您的 API 地址不同，编辑 `src/config/volcengine.js`：

```javascript
this.baseURL = 'https://your-custom-endpoint.com/api';
```

### 修改数据库路径

编辑 `.env` 文件：
```
DATABASE_PATH=./data/your-database.db
```

---

## 🐳 使用 Docker 部署

### 构建镜像

```bash
docker build -t sagpt-backend .
```

### 运行容器

```bash
docker run -d \
  -p 3000:3000 \
  --env-file .env \
  --name sagpt-backend \
  sagpt-backend
```

### 使用 Docker Compose

```bash
docker-compose up -d
```

---

## 📚 下一步

### 1. 完善火山引擎 API 集成

根据您实际获取的火山引擎 Coding Plan API 文档，修改 `src/config/volcengine.js` 中的 API 调用方法。

### 2. 连接前端

将您已有的 Readdy 前端连接到这个后端 API：
- API 基础地址: `http://localhost:3000/api/v1`
- 所有端点已在 `PROJECT_SUMMARY.md` 中详细说明

### 3. 添加认证

如果需要用户认证，可以使用 `src/middlewares/auth.js` 中已准备好的 JWT 认证框架。

---

## 🆘 遇到问题？

### 常见问题

**Q: 服务器启动失败？**
```
检查 .env 文件中的端口是否被占用
修改 PORT=3000 为其他端口
```

**Q: 数据库错误？**
```
确保有读写权限
chmod 755 data/
```

**Q: API 调用失败？**
```
检查 VOLCENGINE_API_KEY 是否正确
查看日志输出: npm run logs
```

### 查看日志

```bash
# 开发模式会直接在终端输出日志
npm run dev
```

---

## 📞 获取帮助

### 文档位置

1. **完整项目文档**: `PROJECT_SUMMARY.md`
2. **API 使用说明**: `README.md`
3. **代码注释**: 所有主要文件都有 JSDoc 注释

---

## 🎯 总结

您现在拥有：
- ✅ 完整的 MVP 后端系统
- ✅ 4 个核心功能模块
- ✅ 火山引擎 API 集成框架
- ✅ 完整的数据库设计
- ✅ Docker 容器化支持
- ✅ 详细的文档和示例

**项目已准备好使用！** 🎉

---

*最后更新: 2026年4月12日*
*版本: 1.0.0*