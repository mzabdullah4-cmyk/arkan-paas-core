FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /runner
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY runner.py registry.py ./
RUN useradd --system --create-home appuser && chown -R appuser /runner
USER appuser
CMD ["python", "runner.py"]
