# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the Python script into the container
COPY generate_keys.py .

# Install PyNaCl
RUN pip install PyNaCl

# Command to run the Python script
CMD ["python", "generate_keys.py"]