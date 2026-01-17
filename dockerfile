# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start the Agent OS
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]