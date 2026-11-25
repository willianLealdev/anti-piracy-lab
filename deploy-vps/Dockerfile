FROM python:3.11-slim

WORKDIR /app

# Dependências
COPY deploy-vps/requirements-vps.txt ./
RUN pip install --no-cache-dir -r requirements-vps.txt

# Código completo (core_server.py + app.py + templates + streams + data)
COPY . .

ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 5050 8484

# O comando é definido no docker-compose (core ou painel)
CMD ["python", "app.py"]
