FROM python:3.11-slim

WORKDIR /app

# ffmpeg (gera streams sintéticos) + fontes DejaVu (texto sobre o vídeo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Código completo (sem os streams, que são gerados no primeiro start)
COPY . .

ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Gera os streams sintéticos DURANTE O BUILD (o container sobe instantâneo).
RUN python gerar_streams.py || true

EXPOSE 5050 8484

# O comando (app.py ou core_server.py) vem do docker-compose.
CMD ["python", "app.py"]
