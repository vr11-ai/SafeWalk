FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

ENV PORT=5000
EXPOSE 5000

CMD ["gunicorn", "api_server:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4"]
