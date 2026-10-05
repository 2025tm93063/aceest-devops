# ---------- Stage 1: Build ----------
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

WORKDIR /app

# Non-root user for security
RUN addgroup --system aceest && adduser --system --ingroup aceest aceest

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN chown -R aceest:aceest /app
USER aceest

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DB_PATH=/app/data/aceest_fitness.db

EXPOSE 5000

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
