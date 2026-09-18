FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /runner

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY runner.py ./runner.py

RUN useradd --system --create-home appuser && chown -R appuser /runner
USER appuser

EXPOSE 8000

CMD ["python", "runner.py"]
