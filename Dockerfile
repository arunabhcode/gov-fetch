# Use the official Python 3.12 slim image as a base
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install uv, the package installer
RUN pip install uv

# Copy the pyproject.toml file first to leverage Docker layer caching
COPY pyproject.toml ./

# Install project dependencies using uv
# --system installs packages globally in the container's Python environment
# --no-cache prevents caching, reducing image size
RUN uv pip install --system --no-cache .

# Copy the rest of the application code into the working directory
COPY . .

# Define the command to run the application
# CMD ["python", "fetch/main.py"] 