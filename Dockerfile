# Start with an official Python image
FROM python:3.12.3-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set working directory in the container
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY ./src /usr/src/app/src
COPY ./requirements.txt /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt

COPY ./.venv/client_secrets.json /usr/src/app/.venv/
COPY ./.venv/database_metadata.json /usr/src/app/.venv/
COPY ./.venv/CHATGPT_API /usr/src/app/.venv/
COPY ./.venv/PYANNOTE_KEY /usr/src/app/.venv/

# Expose the desired port
EXPOSE 5000

WORKDIR /usr/src/app/

# Start the Flask server by default
CMD ["python", "-m", "src.rest.ProtocolServer"]
