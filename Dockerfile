FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

EXPOSE ${PORT}

# Railway private network requires IPv6 (::) binding.
# Bind to [::]:PORT which accepts BOTH IPv6 and IPv4 connections
# via IPv4-mapped addresses on Linux (dual-stack).
CMD gunicorn app:app --bind "[::]:${PORT}" --workers 2 --timeout 120
