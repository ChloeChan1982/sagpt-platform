# SAGPT 后端快速部署指南

## 🚀 快速开始

### 1. 本地测试启动

```bash
cd sagpt-backend

# 安装依赖
npm install

# 初始化数据库（已自动创建的跳过）
node init-db.js

# 启动服务器
npm start

# 测试服务器健康状态
curl http://localhost:3000/api/v1/health
```

### 2. Docker 部署（推荐）

```bash
cd sagpt-backend

# 构建镜像
docker build -t sagpt-backend .

# 运行容器
docker run -d \
  --name sagpt-backend \
  -p 3000:3000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --restart unless-stopped \
  sagpt-backend

# 查看日志
docker logs -f sagpt-backend

# 测试健康状态
curl http://localhost:3000/api/v1/health
```

### 3. 使用 Docker Compose

**创建 docker-compose.yml：**
```yaml
version: '3.8'
services:
  sagpt-backend:
    build: .
    container_name: sagpt-backend
    ports:
      - "3000:3000"
    volumes:
      - ./data:/app/data
    environment:
      - NODE_ENV=production
      - PORT=3000
      - CORS_ORIGIN=https://sagpt.com
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**启动：**
```bash
docker-compose up -d
```

---

## 📋 API 文档

### 健康检查
```http
GET /api/v1/health
Response:
{
  "success": true,
  "data": {
    "message": "SAGPT Backend API is healthy",
    "timestamp": "2026-04-24T14:30:00.000Z",
    "version": "1.0.0"
  }
}
```

### 提交企业需求
```http
POST /api/v1/requests
Content-Type: application/json

Body:
{
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
}

Response:
{
  "success": true,
  "data": {
    "request": { ... },
    "matchedProviders": [ ... ]
  }
}
```

### 获取服务商列表
```http
GET /api/v1/providers
Response:
{
  "success": true,
  "data": {
    "providers": [
      {
        "provider_id": "prov_1234567890_1",
        "name": "Global Legal Services Inc.",
        "country": "United States",
        "serviceType": "legal",
        "pricingTier": "premium",
        "rating": 4.8,
        "description": "Specialized in e-commerce legal setup and compliance",
        "contactEmail": "info@globallegal.com",
        "website": "https://www.globallegal.com"
      }
    ]
  }
}
```

### 生成合规报告
```http
POST /api/v1/reports
Content-Type: application/json

Body:
{
  "country": "United States",
  "industry": "E-commerce",
  "language": "en"
}

Response:
{
  "success": true,
  "data": {
    "report": {
      "country": "United States",
      "industry": "E-commerce",
      "language": "en",
      "content": "# United States E-commerce 市场分析报告..."
    }
  }
}
```

### 聊天功能
```http
POST /api/v1/chat/sessions
Response:
{
  "success": true,
  "data": {
    "sessionId": "session_1234567890_abc123"
  }
}

POST /api/v1/chat/sessions/:sessionId/messages
Content-Type: application/json

Body:
{
  "content": "How to register a company in US?",
  "language": "en"
}

Response:
{
  "success": true,
  "data": {
    "message": {
      "role": "assistant",
      "content": "Thank you for your question...",
      "timestamp": "2026-04-24T14:30:00.000Z"
    }
  }
}
```

---

## 🔧 配置文件说明

### .env 文件配置

```env
# 服务器配置
PORT=3000
NODE_ENV=development

# 安全配置
CORS_ORIGIN=https://sagpt.com
JWT_SECRET=your_secret_key_here

# 数据库配置
DATABASE_PATH=./data/sagpt.db

# 火山引擎 AI 配置（可选，当前版本模拟）
VOLCENGINE_API_KEY=your_api_key
VOLCENGINE_API_BASE_URL=https://api.volcengine.com

# 日志配置
LOG_LEVEL=info
```

### Docker 环境变量

```bash
# 在 docker run 中添加
--env NODE_ENV=production
--env CORS_ORIGIN=https://sagpt.com
--env JWT_SECRET=your_production_secret
```

---

## 📈 监控与维护

### 查看日志

```bash
# Docker 容器日志
docker logs -f sagpt-backend

# 本地文件日志
cat logs/app.log

# 使用 Winston 查询
tail -f logs/app.log
```

### 数据库管理

```bash
# 查看数据库文件大小
ls -lh data/sagpt.db

# 备份数据库
cp data/sagpt.db data/sagpt_$(date +%Y%m%d_%H%M%S).db

# 清理旧数据（保留30天）
node -e "
const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./data/sagpt.db');

const cutoffDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

db.run('DELETE FROM user_requests WHERE submittedAt < ?', [cutoffDate], (err) => {
  if (err) console.error(err);
  else console.log('Old requests deleted');
});

db.close();
"
```

---

## 🐳 Docker 常用命令

```bash
# 查看容器状态
docker ps

# 重启容器
docker restart sagpt-backend

# 进入容器
docker exec -it sagpt-backend /bin/bash

# 备份数据卷
docker run --rm \
  -v sagpt-backend_data:/volume \
  -v $(pwd)/backup:/backup \
  ubuntu tar czf /backup/backup.tar.gz -C /volume ./

# 恢复数据
docker run --rm \
  -v sagpt-backend_data:/volume \
  -v $(pwd)/backup:/backup \
  ubuntu tar xzf /backup/backup.tar.gz -C /volume
```

---

## 🆘 常见问题

### 1. 端口占用问题

**症状：** 服务器无法启动，提示 "EADDRINUSE"

**解决：**
```bash
# 查找并终止占用3000端口的进程
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti :3000 | xargs kill -9

# 或修改端口
export PORT=3001
npm start
```

### 2. 数据库权限问题

**症状：** SQLite 连接失败，提示 "Permission denied"

**解决：**
```bash
# Windows（以管理员身份运行）
icacls data /grant Users:(F) /T

# Linux
chmod -R 755 data
chown -R www-data:www-data data
```

### 3. CORS 错误

**症状：** 浏览器控制台显示 CORS 错误

**解决：**
```bash
# 在 .env 文件中添加
CORS_ORIGIN=https://sagpt.com

# 重启服务器
npm start
```

### 4. 启动失败

**检查步骤：**
1. 检查 Node.js 版本：`node -v` (需要 16+ 版本)
2. 检查依赖是否完整：`npm install`
3. 检查数据库连接：`node init-db.js`
4. 查看完整日志：`node src/server.js` (直接运行查看详细错误)

---

## 📞 支持

遇到问题请检查：
1. GitHub Issues：提交问题描述和日志
2. Discord/Slack：加入社区讨论
3. Email：联系技术支持 team@sagpt.com

---

**🎉 恭喜！** 您的 SAGPT 后端服务已成功部署！