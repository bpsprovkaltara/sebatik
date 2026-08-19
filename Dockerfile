FROM node:22-alpine AS frontend
WORKDIR /build
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend backend
COPY src src
COPY scripts scripts
COPY --from=frontend /build/dist frontend/dist
# Direktori data dibuat kosong. Isinya tidak ikut ke dalam image: basis data
# tinggal di PostgreSQL (volume terpisah), sedangkan arsip unggahan dan bukti
# dukung dipasang sebagai volume supaya tidak hilang saat image diganti.
RUN mkdir -p /app/data/processed/arsip-unggahan /app/data/processed/bukti-dukung /app/backup
EXPOSE 8000
CMD ["python","-m","uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8000"]
