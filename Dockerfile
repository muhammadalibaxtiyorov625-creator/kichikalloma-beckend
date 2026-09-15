# ==========================================
# 1-BOSQICH: Frontend (React/Vite) Build
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/website

COPY website/package.json ./
RUN npm install

COPY website/ ./
RUN npx vite build

# ==========================================
# 2-BOSQICH: Production Python Backend
# ==========================================
FROM python:3.11-slim AS production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY --from=frontend-builder /app/website/dist/public ./website/dist/public

ENV PORT=3000
ENV PYTHONUNBUFFERED=1

EXPOSE 3000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
