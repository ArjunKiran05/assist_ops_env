FROM python:3.11-slim

WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn pydantic requests

# Expose port
EXPOSE 7860

# Run server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]