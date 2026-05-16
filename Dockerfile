# 1. Start with a lightweight Python 3.11 Linux environment
FROM python:3.11-slim

# 2. Set the working directory inside the cloud container
WORKDIR /app

# 3. Install the C++ system libraries required by OpenCV and DeepFace
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy your backend requirements and install them securely
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your actual code folders into the container
COPY backend /app/backend
COPY frontend /app/frontend

# 6. Expose port 7860 (Hugging Face strictly requires this specific port)
EXPOSE 7860
WORKDIR /app/backend

# 7. Start your FastAPI server using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]