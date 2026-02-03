# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY gateway/requirements.txt .

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Copy the application code into the container
COPY gateway/src/ .

# Copy shared utilities
COPY shared/ ./shared/

# Specify the command to run when the container starts
CMD ["python", "main.py"]