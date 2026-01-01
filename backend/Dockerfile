FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
# (We do this first to cache dependencies so builds are faster)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# Run the app. 
# IMPORTANT: --host 0.0.0.0 is required for Docker to expose the port
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]