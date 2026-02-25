# Stage 1: Builder
FROM python:3.11-slim-bookworm as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim-bookworm

WORKDIR /app

RUN useradd -m -u 1000 auralis
USER auralis

COPY --from=builder /root/.local /home/auralis/.local
ENV PATH=/home/auralis/.local/bin:$PATH

COPY . .

ENV PYTHONUNBUFFERED=1
CMD ["python", "agent.py", "start"]