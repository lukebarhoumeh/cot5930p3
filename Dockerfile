# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy all project files to the container
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose the port that Flask will run on
EXPOSE 8080

# Command to run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
