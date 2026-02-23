# HealthAI Coach - ETL Pipeline
FROM eclipse-temurin:17-jdk-jammy

# Set working directory
WORKDIR /app

# Install Python 3.10 (default in jammy)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Download PostgreSQL JDBC driver for Spark
RUN mkdir -p /app/jars && \
    curl -L https://jdbc.postgresql.org/download/postgresql-42.7.1.jar \
    -o /app/jars/postgresql-42.7.1.jar

# Copy project files
COPY . .

# Create data directories
RUN mkdir -p data/raw data/processed logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV JAVA_HOME=/opt/java/openjdk
ENV PYSPARK_SUBMIT_ARGS="--jars /app/jars/postgresql-42.7.1.jar pyspark-shell"

# Default command
CMD ["python3", "main.py", "--pipeline", "exercises"]
