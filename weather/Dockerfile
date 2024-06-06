FROM python:3.9-slim
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Set environment variables
EXPOSE 5000

# Specify the command to run your application
CMD ["python3", "weather.py"]

