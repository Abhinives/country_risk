# Use official Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Set environment variables to disable telemetry and prompts
ENV STREAMLIT_GATHER_USAGE_STATS=False
ENV STREAMLIT_SERVER_HEADLESS=true

# Expose the Streamlit port
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "--server.port=8501", "streamlit_app.py"]