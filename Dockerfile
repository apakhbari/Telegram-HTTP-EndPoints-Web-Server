# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required Python packages
RUN pip install --no-cache-dir Flask requests[socks]

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable to prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Run app.py when the container launches
CMD ["python", "app.py"]