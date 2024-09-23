# Use the official Python 3.9 slim image as the base image
FROM python:3.9-slim

# Create a non-privileged user
RUN addgroup --system appgroup && adduser --system --group appuser

# Install cron, curl, and supervisor
RUN apt-get update && apt-get install -y \
    cron \
    curl \
    supervisor \
    build-essential \
    gcc \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default model, can be overridden during deployment
ENV MODEL=arima

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements first to leverage Docker cache for faster builds
COPY requirements.txt /app/

# Upgrade pip and install Cython and numpy manually by parsing the requirements.txt
# they are known nuisances with the pip install -r requirements.txt
RUN pip install --upgrade pip && \
    CYTHON_VERSION=$(grep -i '^Cython==' requirements.txt | cut -d'=' -f3) \
    && NUMPY_VERSION=$(grep -i '^numpy==' requirements.txt | cut -d'=' -f3) \
    && pip install --no-cache-dir Cython==$CYTHON_VERSION numpy==$NUMPY_VERSION

# Install requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the working directory
COPY . /app/

# Copy the crontab file into the container and set it
COPY crontab /etc/cron.d/allora_worker_cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/allora_worker_cron

# Apply the cron job
RUN crontab /etc/cron.d/allora_worker_cron

# Copy the supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set permissions to the non-privileged user
RUN chown -R appuser:appgroup /app

# Expose the port that the app will run on
EXPOSE 8000

# Start supervisord to run both cron and uvicorn
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
