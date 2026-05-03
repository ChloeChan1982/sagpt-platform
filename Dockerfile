FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# 复制并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有代码
COPY . .

# 暴露端口
EXPOSE 10000

# 直接在启动时从环境变量读取
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["sh", "-c", "echo 'KEY length: '$OPENAI_API_KEY && python -c 'import os; print(\"PY KEY:\", len(os.getenv(\"OPENAI_API_KEY\",\"\")))' && python scripts/init_db.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
