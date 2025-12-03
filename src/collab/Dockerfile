FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
# We need to ensure fastapi and uvicorn are installed. 
# If they are not in requirements.txt, we install them explicitly.
RUN pip install --no-cache-dir fastapi uvicorn websockets

# Copy source code
COPY src/collab ./src/collab
# We might need shared modules later, so copying src/infrastructure if needed
# COPY src/infrastructure ./src/infrastructure

# Expose port
EXPOSE 8002

# Run the application
CMD ["uvicorn", "src.collab.main:app", "--host", "0.0.0.0", "--port", "8002"]
