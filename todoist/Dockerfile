FROM python:3.9-slim
WORKDIR /app
COPY a.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Set environment variables
EXPOSE 8000

# Specify the command to run your application
CMD ["python3", "a.py"]

