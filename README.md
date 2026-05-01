# SAGPT AI Backend - 部署与集成指南

## 📦 项目概述

这是 SAGPT 网站的独立 AI 后端服务，与 Readdy 前端配合使用。提供：
- ✅ AI 智能匹配引擎（向量相似度 + LLM 重排序）
- ✅ 7x24 AI 文本客服（GPT-4o）
- ✅ 需求提交 + 即时匹配预览
- ✅ 专家语义搜索
- ✅ 服务商入驻管理

## 🏗 架构

```
Readdy 前端 (sagpt.com)
    ↓ fetch/POST
SAGPT API (api.sagpt.com:8000/api/*)
    ↓
PostgreSQL + pgvector ← OpenAI Embeddings
Redis (会话缓存)
```

## 🚀 快速启动（本地开发）

### 1. 前提条件
- Docker + Docker Compose
- OpenAI API Key ([获取](https://platform.openai.com/api-keys))

### 2. 克隆并配置
```bash
cd sagpt-backend

# 创建环境变量文件
cp .env.example .env

# 编辑 .env，填入你的 OpenAI API Key
nano .env
```

### 3. 启动服务
```bash
# 一键启动（PostgreSQL + Redis + API）
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止
docker-compose down
```

### 4. 初始化数据
```bash
# 进入容器并运行种子脚本
docker-compose exec api python scripts/seed_data.py
```

### 5. 测试 API
```bash
# 健康检查
curl http://localhost:8000/health

# 提交测试需求
curl -X POST http://localhost:8000/api/demands/submit \
  -H "Content-Type: application/json" \
  -d '{
    "target_country": "Saudi Arabia",
    "industry": "E-commerce",
    "scenario": "Investment & Setup",
    "budget_range": "$10,000 - $100,000",
    "urgency": "normal",
    "description": "Need legal services to set up an e-commerce company in Riyadh",
    "email": "test@example.com",
    "company_name": "TestCorp"
  }'

# 查看专家列表
curl "http://localhost:8000/api/experts?country=UAE&page=1"

# AI 聊天测试
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What do I need to open a company in Saudi Arabia?", "fingerprint": "test123"}'
```

## 🌐 生产部署

### 选项 A: 云服务器部署（推荐）

以 Ubuntu + Docker 为例：

```bash
# 1. 购买云服务器（推荐：阿里云/腾讯云/AWS，2核4G起）
# 2. 安装 Docker
curl -fsSL https://get.docker.com | sh

# 3. 上传项目到服务器（使用 scp 或 git）
scp -r sagpt-backend root@your-server-ip:/opt/

# 4. 配置生产环境变量
export OPENAI_API_KEY="sk-你的密钥"
export API_SECRET_KEY="随机强密码"
export ALLOWED_ORIGINS="https://sagpt.com,https://www.sagpt.com"

# 5. 启动
cd /opt/sagpt-backend
docker-compose up -d

# 6. 配置 Nginx 反向代理（已包含在 docker-compose 中）
# 如需 HTTPS，使用 certbot:
certbot --nginx -d api.sagpt.com
```

### 选项 B: Serverless 部署（Render/Railway/Fly.io）

以 **Render** 为例（免费）：

1. 将代码推送到 GitHub
2. 在 Render 创建 New Web Service
3. 选择 Docker 环境
4. 设置环境变量：`OPENAI_API_KEY`, `DATABASE_URL`
5. 部署完成，获取 URL（如 `https://sagpt-api.onrender.com`）

### 选项 C: Vercel + Neon（无服务器）

```bash
# 使用 Next.js API Routes 部署（需要适配代码）
# 或部署到 Vercel Functions
```

## 🔗 Readdy 前端集成

### 步骤 1: 在 Readdy 添加自定义代码

1. 登录 [Readdy.ai](https://readdy.ai) 编辑你的网站
2. 找到 **"Custom Code"** 或 **"HTML/JS Block"** 设置
3. 添加以下代码到 `<head>` 或页面底部：

```html
<!-- 方式1: 直接嵌入（推荐用于测试） -->
<script src="https://api.sagpt.com/static/sagpt-integration.js"></script>

<!-- 方式2: 如果你上传到了 CDN -->
<script src="https://your-cdn.com/sagpt-integration.js"></script>
```

### 步骤 2: 修改 API 地址

在 `sagpt-integration.js` 中修改配置：

```javascript
const CONFIG = {
  API_BASE_URL: 'https://api.sagpt.com/api',  // 你的后端地址
  // ...
};
```

### 步骤 3: 配置 CORS

确保后端允许你的 Readdy 域名：

```bash
# 在 .env 或 docker-compose.yml 中设置：
ALLOWED_ORIGINS=https://sagpt.com,https://www.sagpt.com
```

### 步骤 4: 测试集成

1. 在 Readdy 预览/发布网站
2. 访问 `sagpt.com`
3. 点击右下角 "Talk with Us" 聊天按钮
4. 发送测试消息，应收到 AI 回复
5. 填写 Submit Demand 表单，提交后应看到 AI 匹配预览

## 🔧 自定义配置

### 更换 LLM 模型

编辑 `.env`：
```bash
# OpenAI（默认）
OPENAI_MODEL=gpt-4o           # 或 gpt-4o-mini（更便宜）
EMBEDDING_MODEL=text-embedding-3-large

# 如需使用 Claude，修改 app/services/ai_service.py
# 添加 Anthropic client
```

### 调整匹配算法权重

编辑 `app/services/ai_service.py` 中的 `_calculate_match_score`：
```python
# 修改权重分配
country_score = 1.0 * 0.4      # 国家匹配 40%
vector_score = similarity * 0.3  # 向量相似度 30%
specialty_score = overlap * 0.2    # 专业重叠 20%
exp_score = years / 20 * 0.1      # 经验加成 10%
```

### 扩展国家列表

编辑 `app/models/schemas.py` 中的验证，或直接在前端表单增加选项。

## 📊 API 文档

启动后端后访问：
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### 核心端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/demands/submit` | POST | 提交需求 + AI 匹配 |
| `/api/demands/{id}/matches` | GET | 查看匹配结果 |
| `/api/chat` | POST | 流式 AI 聊天 |
| `/api/chat/message` | POST | 非流式 AI 聊天 |
| `/api/experts` | GET | 专家列表/筛选 |
| `/api/experts/search/semantic` | GET | 语义搜索 |
| `/api/providers/apply` | POST | 服务商申请 |

## 🐛 常见问题

### Q: 聊天一直显示 "Connecting..."
A: 检查 `OPENAI_API_KEY` 是否正确设置，以及后端是否正常运行：`curl http://localhost:8000/health`

### Q: Readdy 前端调用 API 报 CORS 错误
A: 确保 `ALLOWED_ORIGINS` 包含了你的 Readdy 域名（如 `https://sagpt.com`）

### Q: 向量匹配不工作
A: pgvector 扩展需要正确安装。运行：`docker-compose exec db psql -U sagpt -d sagpt -c "CREATE EXTENSION IF NOT EXISTS vector;"`

### Q: 如何连接自己的专家数据库？
A: 修改 `scripts/seed_data.py` 添加你的专家数据，或构建数据导入 API。

## 🗺 路线图

- [x] 核心 API + AI 聊天
- [x] 需求提交 + 即时匹配预览
- [x] 专家语义搜索
- [ ] 服务商后台登录系统
- [ ] 需求追踪仪表盘
- [ ] AI 合规扫描器
- [ ] 多语言自动翻译
- [ ] 支付集成（Stripe）
- [ ] 邮件/短信通知系统

## 📞 支持

如有问题，请检查：
1. 后端健康状态：`/health`
2. Docker 日志：`docker-compose logs`
3. 环境变量配置

---

**⚠️ 重要**: 生产环境请务必：
- 修改 `API_SECRET_KEY` 为强密码
- 配置 HTTPS（使用 Nginx + certbot）
- 设置数据库定期备份
- 监控 OpenAI API 用量和费用
