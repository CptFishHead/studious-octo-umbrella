FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \    && useradd -m appuser \    && chown -R appuser /app
USER appuser
COPY . .
CMD ["python", "bot.py"]
