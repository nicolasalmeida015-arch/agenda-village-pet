FROM python:3.12-slim
# Fuso da loja: as regras de antecedência mínima e de falta usam a hora local (o servidor de nuvem roda em UTC)
ENV TZ=America/Sao_Paulo PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
# O Render informa a porta em $PORT; localmente usa 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
