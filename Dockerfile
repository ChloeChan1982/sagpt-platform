FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 直接把 API Key 硬编码到环境变量（临时方案）
ENV OPENAI_API_KEY=sk-jagttstdbyrmtchmrshfumjmxnpjcixarvkeutsycvzzyamo
ENV AI_PROVIDER=siliconflow
ENV OPENAI_BASE_URL=https://cloud.siliconflow.cn/me/account/ak
ENV OPENAI_MODEL=deepseek-ai/DeepSeek-V4-Flash
ENV USE_FREE_MODEL_TIER=true

EXPOSE 10000

CMD ["sh", "-c", "python scripts/init_db.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
