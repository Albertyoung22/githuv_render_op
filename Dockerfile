FROM python:3.11-slim

WORKDIR /app

# Install dependencies (Flask, Waitress, Edge-TTS)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

ENV PORT=10000
EXPOSE 10000

# Run Flask using Waitress production WSGI server
CMD ["python", "app.py"]
